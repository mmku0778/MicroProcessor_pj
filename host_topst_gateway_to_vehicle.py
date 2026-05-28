import socket
import json
import csv
import time
from datetime import datetime
import threading
import serial

HOST = "0.0.0.0"
AI_G_PORT = 5005

VEHICLE_IP = "192.168.0.24"   # Raspberry Pi IP
VEHICLE_PORT = 6006

LOG_FILE = "integrated_ai_g_vehicle_log.csv"

# [추가] 아두이노 시리얼 설정
ARDUINO_PORT = "/dev/ttyACM0"
ARDUINO_BAUD = 115200

# [추가] 전역 변수: 아두이노 최신 상태
arduino_state = {
    "e_stop": False,
    "deadman": False,
    "mode_request": False,
    "joy_x": 512,
    "joy_y": 512
}

# [추가] 백그라운드에서 아두이노 시리얼 데이터를 읽어오는 함수
def read_arduino_serial():
    global arduino_state
    try:
        ser = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=1.0)
        print(f"[HOST] Arduino serial started: {ARDUINO_PORT}")
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    try:
                        data = json.loads(line)
                        if data.get("src") == "arduino":
                            # 전역 변수 업데이트
                            arduino_state["e_stop"] = data.get("e_stop", False)
                            arduino_state["deadman"] = data.get("deadman", False)
                            arduino_state["mode_request"] = data.get("mode_request", False)
                            arduino_state["joy_x"] = data.get("joy_x", 512)
                            arduino_state["joy_y"] = data.get("joy_y", 512)
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        print(f"[HOST] Arduino serial error: {e}")


def make_supervisor_cmd(perception_state):
    global arduino_state
    payload = perception_state.get("payload", {})

    cmd = {
        "type": "SUPERVISOR_CMD",
        "allow_motion": True,
        "speed_limit": 0.35,
        "fault": "NONE",
        "ttl_ms": 300,
        "timestamp": time.time()
    }

    # 1. [추가] 아두이노 하드웨어 E-STOP 최우선 처리 (계획서 1순위)
    if arduino_state["e_stop"]:
        cmd["allow_motion"] = False
        cmd["speed_limit"] = 0.0
        cmd["fault"] = "HARDWARE_ESTOP"
        return cmd  # E-STOP 상태면 뒤의 AI-G 로직은 무시하고 바로 리턴

    # 2. 이후 기존 AI-G 판단 로직 수행
    if payload.get("perception_fault", False):
        cmd["allow_motion"] = False
        cmd["speed_limit"] = 0.0
        cmd["fault"] = "SENSOR_FAULT"

    elif payload.get("person_detected", False):
        cmd["allow_motion"] = False
        cmd["speed_limit"] = 0.0
        cmd["fault"] = "PERSON_DANGER"

    elif payload.get("obstacle_detected", False):
        cmd["allow_motion"] = False
        cmd["speed_limit"] = 0.0
        cmd["fault"] = "OBSTACLE_DANGER"

    elif payload.get("stop_marker_detected", False):
        cmd["allow_motion"] = False
        cmd["speed_limit"] = 0.0
        cmd["fault"] = "ZONE_STOP"

    elif payload.get("forbidden_zone_detected", False):
        cmd["allow_motion"] = False
        cmd["speed_limit"] = 0.0
        cmd["fault"] = "ZONE_VIOLATION"

    elif payload.get("slow_zone_detected", False):
        cmd["allow_motion"] = True
        cmd["speed_limit"] = 0.15
        cmd["fault"] = "NONE"

    return cmd


def send_to_vehicle(cmd):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        sock.connect((VEHICLE_IP, VEHICLE_PORT))
        sock.sendall(json.dumps(cmd).encode("utf-8"))
        sock.close()
        print(f"[HOST] Sent to vehicle: {VEHICLE_IP}:{VEHICLE_PORT}")
        return True

    except Exception as e:
        print(f"[HOST] Vehicle send failed: {e}")
        return False


def init_log():
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "time",
            "seq",
            "src",
            "stop_marker",
            "slow_zone",
            "forbidden_zone",
            "perception_fault",
            "allow_motion",
            "speed_limit",
            "fault",
            "vehicle_send_ok"
        ])


def save_log(perception_state, cmd, vehicle_send_ok):
    payload = perception_state.get("payload", {})

    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "time",
            "seq",
            "src",
            "stop_marker",
            "slow_zone",
            "forbidden_zone",
            "perception_fault",
            "allow_motion",
            "speed_limit",
            "fault",
            "vehicle_send_ok"
        ])


def handle_client(conn, addr):
    print(f"\n[HOST] Connected from {addr}")
    buffer = ""

    while True:
        data = conn.recv(1024)

        if not data:
            print("[HOST] Connection closed")
            break

        buffer += data.decode("utf-8")

        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)

            if not line.strip():
                continue

            try:
                perception_state = json.loads(line)
                cmd = make_supervisor_cmd(perception_state)
                vehicle_send_ok = send_to_vehicle(cmd)
                
                # [수정] 로그 저장 시, 이제 arduino_state도 함께 출력하면 좋습니다 (개발자 편의상)
                save_log(perception_state, cmd, vehicle_send_ok)

                print("\n[RX] PERCEPTION_STATE")
                print(json.dumps(perception_state, indent=2))
                
                print(f"[RX] ARDUINO_STATE: E-STOP={arduino_state['e_stop']}, Deadman={arduino_state['deadman']}")

                print("[TX] SUPERVISOR_CMD")
                print(json.dumps(cmd, indent=2))

            except json.JSONDecodeError:
                print("[ERROR] Invalid JSON:", line)


def main():
    init_log()

    # [추가] 아두이노 시리얼 수신 스레드 시작
    arduino_thread = threading.Thread(target=read_arduino_serial, daemon=True)
    arduino_thread.start()

    print("[HOST] Integrated Gateway Start")
    print(f"[HOST] AI-G listen port: {AI_G_PORT}")
    print(f"[HOST] Vehicle target: {VEHICLE_IP}:{VEHICLE_PORT}")
    print(f"[HOST] Log file: {LOG_FILE}")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, AI_G_PORT))
    server.listen(5)

    try:
        while True:
            conn, addr = server.accept()
            try:
                handle_client(conn, addr)
            finally:
                conn.close()

    except KeyboardInterrupt:
        print("\n[HOST] Stopped")

    finally:
        server.close()


if __name__ == "__main__":
    main()
