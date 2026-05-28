import serial
import socket
import time

ARDUINO_PORT = "/dev/ttyACM0"
BAUD_RATE = 115200
TARGET_IP = "127.0.0.1"
TARGET_PORT = 5006

def main():
    print(f"[SENDER] 아두이노 시리얼 통신 시작 ({ARDUINO_PORT})")
    try:
        ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
    except Exception as e:
        print(f"[SENDER] 시리얼 연결 에러: {e}")
        return

    while True:
        print(f"[SENDER] 5006 포트 게이트웨이 접속 시도 중... ({TARGET_IP}:{TARGET_PORT})")
        try:
            # TCP 소켓으로 5006 포트 접속
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((TARGET_IP, TARGET_PORT))
            print("[SENDER] 5006 포트 접속 완료! 데이터 전송 시작")
            
            while True:
                line = ser.readline()
                if line:
                    sock.sendall(line) # 아두이노에서 읽은 데이터를 그대로 전송
        except Exception as e:
            print(f"[SENDER] 게이트웨이와 연결 끊김. 2초 후 재시도... ({e})")
            time.sleep(2)

if __name__ == "__main__":
    main()
