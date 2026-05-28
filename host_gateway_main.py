import socket
import json
import time
import threading

# --- 설정 값 ---
AIG_LISTEN_IP = "0.0.0.0"
AIG_LISTEN_PORT = 5005
CONTROLLER_LISTEN_IP = "0.0.0.0"
CONTROLLER_LISTEN_PORT = 5006
VEHICLE_IP = "192.168.0.24"
VEHICLE_PORT = 6006

# --- 글로벌 변수 ---
arduino_state = {
    "joy_x": 512, "joy_y": 512, 
    "e_stop": False, "deadman": False
}
current_mode = "AUTO"
last_mode_request_state = False

def controller_tcp_thread():
    """5006번 포트에서 아두이노(컨트롤러) 데이터를 실시간 수신하는 스레드"""
    global arduino_state, current_mode, last_mode_request_state
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((CONTROLLER_LISTEN_IP, CONTROLLER_LISTEN_PORT))
    server.listen(1)
    print(f"[HOST] Controller listen port: {CONTROLLER_LISTEN_PORT} (대기 중)")
    
    while True:
        client, addr = server.accept()
        print(f"\n[HOST] Arduino Sender Connected from {addr}")
        buffer = ""
        while True:
            try:
                data = client.recv(1024)
                if not data:
                    break
                
                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    
                    if line.startswith("{") and line.endswith("}"):
                        try:
                            parsed = json.loads(line)
                            if parsed.get("src") == "arduino":
                                arduino_state["joy_x"] = parsed.get("joy_x", 512)
                                arduino_state["joy_y"] = parsed.get("joy_y", 512)
                                arduino_state["e_stop"] = parsed.get("e_stop", False)
                                arduino_state["deadman"] = parsed.get("deadman", False)
                                
                                # 수동/자동 모드 토글 로직
                                current_req = parsed.get("mode_request", False)
                                if current_req and not last_mode_request_state:
                                    current_mode = "MANUAL" if current_mode == "AUTO" else "AUTO"
                                    print(f"\n[MODE CHANGED] Now in {current_mode} MODE")
                                
                                last_mode_request_state = current_req
                        except json.JSONDecodeError:
                            pass
            except Exception:
                break
        print("[HOST] Arduino Sender Disconnected. Waiting for reconnection...")

def determine_supervisor_cmd(perception_data, start_time):
    """Supervisor 우선순위 판단 로직 (변경 없음)"""
    global current_mode
    cmd = {
        "type": "SUPERVISOR_CMD", "allow_motion": True,
        "speed_limit": 0.35, "fault": "NONE",
        "ttl_ms": 300, "timestamp": time.time(), "mode": current_mode
    }

    if arduino_state["e_stop"]:
        cmd["allow_motion"] = False
        cmd["speed_limit"] = 0.0
        cmd["fault"] = "HARDWARE_ESTOP"
    elif current_mode == "MANUAL" and not arduino_state["deadman"]:
        cmd["allow_motion"] = False
        cmd["speed_limit"] = 0.0
        cmd["fault"] = "DEADMAN_RELEASED"
    if current_mode == "MANUAL" and cmd["allow_motion"]:
        joy_y = arduino_state["joy_y"]
        if joy_y > 600: cmd["speed_limit"] = 0.5
        elif joy_y < 400: cmd["speed_limit"] = -0.5
        else: cmd["speed_limit"] = 0.0

    process_time_ms = (time.time() - start_time) * 1000
    print(f"[EVALUATION] Logic Processing Time: {process_time_ms:.2f} ms")
    return cmd

def main():
    print("[HOST] Integrated Gateway Start (Phase 4: Dual Port Architecture)")
    
    # 5006번 수신 스레드 실행
    threading.Thread(target=controller_tcp_thread, daemon=True).start()

    # 5005번 수신 소켓 (AI-G용)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((AIG_LISTEN_IP, AIG_LISTEN_PORT))
    server.listen(1)
    print(f"[HOST] AI-G listen port: {AIG_LISTEN_PORT} (대기 중)")

    vehicle_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        try:
            client, addr = server.accept()
            print(f"\n[HOST] AI-G Connected from {addr}")
            while True:
                data = client.recv(4096)
                if not data: break
                
                start_time = time.time()
                try:
                    perception_data = json.loads(data.decode('utf-8'))
                    print(f"\n[RX] ARDUINO: Mode={current_mode}, E-STOP={arduino_state['e_stop']}, Deadman={arduino_state['deadman']}")
                    
                    final_cmd = determine_supervisor_cmd(perception_data, start_time)
                    
                    print("[TX] SUPERVISOR_CMD")
                    print(json.dumps(final_cmd, indent=2))
                    vehicle_sock.sendto(json.dumps(final_cmd).encode('utf-8'), (VEHICLE_IP, VEHICLE_PORT))
                except json.JSONDecodeError:
                    pass
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[HOST] Error: {e}")

if __name__ == "__main__":
    main()
