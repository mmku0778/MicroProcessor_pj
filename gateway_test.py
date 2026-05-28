import serial
import json
import time

# 아두이노가 연결된 포트 번호와 속도를 설정합니다. (포트 이름은 환경에 맞게 변경)
# Ubuntu 환경 예시: '/dev/ttyUSB0' 또는 '/dev/ttyACM0'
SERIAL_PORT = '/dev/ttyACM0' 
BAUD_RATE = 115200

try:
    py_serial = serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE, timeout=1)
    print(f"아두이노 연결 성공: {SERIAL_PORT}")
    
    while True:
        if py_serial.readable():
            # 아두이노로부터 한 줄 단위로 읽어옴
            response = py_serial.readline().decode('utf-8').strip()
            
            try:
                # 수신된 JSON 문자열 파싱
                data = json.loads(response)
                e_stop_status = data.get("e_stop", False)
                
                if e_stop_status:
                    print("[ALERT] Hardware E-STOP 감지! 즉시 정지 신호 필요")
                    # 향후 이 부분에 팀원의 TOPST D3 송신 로직 연동
                else:
                    print("[INFO] 정상 상태 (E-STOP 해제)")
                    
            except json.JSONDecodeError:
                # 최초 연결 시 깨진 데이터가 들어올 경우 예외 처리
                pass
                
        time.sleep(0.1) # 10Hz 주기 대기

except Exception as e:
    print(f"시리얼 통신 오류: {e}")
