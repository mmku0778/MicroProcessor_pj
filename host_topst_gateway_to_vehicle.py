import socket
import json
import time
import threading
import serial

# --- 설정 값 ---
AIG_LISTEN_IP = "0.0.0.0"
AIG_LISTEN_PORT = 5005
VEHICLE_IP = "192.168.0.24"
VEHICLE_PORT = 6006
ARDUINO_PORT = "/dev/ttyACM0"
BAUD_RATE = 115200

# --- 글로벌 변수 ---
arduino_state = {
    "joy_x": 512, "joy_y": 512, 
    "e_stop": False, "deadman": False
}
current_mode = "AUTO"  # 초기 시작 모드
last_mode_request_state = False

def arduino_read_thread():
    """아두이노 데이터를 0.1초마다 실시간으로 수신하고 처리하는 스레드"""
    global arduino_state, current_mode, last_mode_request_state
    try:
        ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
        print(f"[HOST] Arduino serial started: {ARDUINO_PORT}")
        while True:
            line = ser.readline().decode('utf-8').strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    data = json.loads(line)
                    if data.get("src") == "arduino":
                        arduino_state["joy_x"] = data.get("joy_x", 512)
                        arduino_state["joy_y"] = data.get("joy_y", 512)
                        arduino_state["e_stop"] = data.get("e_stop", False)
                        arduino_state["deadman"] = data.get("deadman", False)
                        
                        # [핵심 수정] 아두이노 스레드에서 버튼 눌림 즉시 감지 및 토글 처리
                        current_req = data.get("mode_request", False)
                        
                        # 버튼이 안 눌려있다가(False) 눌린 순간(True)을 포착
                        if current_req and not last_mode_request_state:
                            current_mode = "MANUAL" if current_mode == "AUTO" else "AUTO"
                            print(f"\n[MODE CHANGED] Now in {current_mode} MODE")
                        
                        last_mode_request_state = current_req
                        
                except json.JSONDecodeError:
                    pass
    except Exception as e:
        print(f"[HOST] Arduino serial error: {e}")

def determine_supervisor_cmd(perception_data, start_time):
    """계획서 6번 항목: Supervisor 우선순위 판단 및 명령 생성"""
    global current_mode
    
    # 기본 명령 뼈대 생성
    cmd = {
        "type": "SUPERVISOR_CMD",
        "allow_motion": True,
        "speed_limit": 0.35, # 기본 주행 속도
        "fault": "NONE",
        "ttl_ms": 300,
        "timestamp": time.time(),
        "mode": current_mode
    }

    # --- [우선순위 1] E-STOP (하드웨어 비상 정지) ---
    if arduino_state["e_stop"]:
        cmd["allow_motion"] = False
        cmd["speed_limit"] = 0.0
        cmd["fault"] = "HARDWARE_ESTOP"
    
    # --- [우선순위 2] Deadman 해제 감지 ---
    # 수동 모드(MANUAL)인데 데드맨 스위치를 잡고 있지 않다면 즉시 정지
    elif current_mode == "MANUAL" and not arduino_state["deadman"]:
        cmd["allow_motion"] = False
        cmd["speed_limit"] = 0.0
        cmd["fault"] = "DEADMAN_RELEASED"
    
    # --- [수동 모드 조이스틱 제어 로직] ---
    # 수동 모드이면서 위의 정지 조건에 걸리지 않았을 때만 조이스틱 반영
    if current_mode == "MANUAL" and cmd["allow_motion"]:
        joy_y = arduino_state["joy_y"]
        if joy_y > 600:
            cmd["speed_limit"] = 0.5  # 전진 조작
        elif joy_y < 400:
            cmd["speed_limit"] = -0.5 # 후진 조작
        else:
            cmd["speed_limit"] = 0.0  # 중립

    # 정량 평가용 로직 처리 시간 계산 (목표: 0.5초 이내 증명)
    process_time_ms = (time.time() - start_time) * 1000
    print(f"[EVALUATION] Logic Processing Time: {process_time_ms:.2f} ms")

    return cmd

def main():
    print("[HOST] Integrated Gateway Start")
    
    # 아두이노 수신 스레드 실행
    threading.Thread(target=arduino_read_thread, daemon=True).start()

    # AI-G 데이터 수신 소켓 열기 (5005 포트)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((AIG_LISTEN_IP, AIG_LISTEN_PORT))
    server.listen(1)
    print(f"[HOST] AI-G listen port: {AIG_LISTEN_PORT}")

    vehicle_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        try:
            client, addr = server.accept()
            print(f"\n[HOST] AI-G Connected from {addr}")
            
            while True:
                data = client.recv(4096)
                if not data:
                    break
                
                # 명령어 생성 시작 시간 기록
                start_time = time.time() 
                
                try:
                    perception_data = json.loads(data.decode('utf-8'))
                    
                    # 현재 입력 상태 화면 출력
                    print(f"\n[RX] ARDUINO: Mode={current_mode}, E-STOP={arduino_state['e_stop']}, Deadman={arduino_state['deadman']}")
                    
                    # 우선순위 판별 함수 호출
                    final_cmd = determine_supervisor_cmd(perception_data, start_time)
                    
                    # 최종 결정된 명령 터미널 출력
                    print("[TX] SUPERVISOR_CMD")
                    print(json.dumps(final_cmd, indent=2))
                    
                    # 차량 제어부(라즈베리파이)로 데이터 전송
                    vehicle_sock.sendto(json.dumps(final_cmd).encode('utf-8'), (VEHICLE_IP, VEHICLE_PORT))

                except json.JSONDecodeError:
                    pass
                
        except KeyboardInterrupt:
            print("\n[HOST] Stopped")
            break
        except Exception as e:
            print(f"[HOST] Error: {e}")

if __name__ == "__main__":
    main()
