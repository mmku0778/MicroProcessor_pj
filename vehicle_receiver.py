import socket
import json
import time
import RPi.GPIO as GPIO

# ======================================
# 라즈베리파이에서 실행
# =======================================
# 1. 통신 및 글로벌 상태 설정
# =======================================
LISTEN_IP = "0.0.0.0"
LISTEN_PORT = 6006

last_cmd_time = time.time()
current_ttl_seconds = 0.3
is_moving = False

# =======================================
# 2. 하드웨어 핀 번호 설정 (BCM 기준)
# =======================================
# 드라이버 #1 (왼쪽)
LF_IN1, LF_IN2, LF_PWM = 5, 6, 12     # 왼쪽 앞 (LF)
LR_IN1, LR_IN2, LR_PWM = 16, 20, 13   # 왼쪽 뒤 (LR)

# 드라이버 #2 (오른쪽)
RF_IN1, RF_IN2, RF_PWM = 23, 24, 18   # 오른쪽 앞 (RF)
RR_IN1, RR_IN2, RR_PWM = 21, 26, 19   # 오른쪽 뒤 (RR)

motor_pins = [
    LF_IN1, LF_IN2, LF_PWM,
    LR_IN1, LR_IN2, LR_PWM,
    RF_IN1, RF_IN2, RF_PWM,
    RR_IN1, RR_IN2, RR_PWM
]

pwm_lf = pwm_lr = pwm_rf = pwm_rr = None

def setup_motors():
    """모터 핀 초기화 및 PWM 설정"""
    global pwm_lf, pwm_lr, pwm_rf, pwm_rr
    
    print("[HARDWARE] GPIO 핀 초기화 중...")
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    
    for pin in motor_pins:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
        
    # PWM 설정 (100Hz)
    pwm_lf = GPIO.PWM(LF_PWM, 100)
    pwm_lr = GPIO.PWM(LR_PWM, 100)
    pwm_rf = GPIO.PWM(RF_PWM, 100)
    pwm_rr = GPIO.PWM(RR_PWM, 100)
    
    pwm_lf.start(0)
    pwm_lr.start(0)
    pwm_rf.start(0)
    pwm_rr.start(0)
    print("[HARDWARE] 모터 초기화 완료.")

# =======================================
# 3. 주행 제어 함수 정의
# =======================================
def drive_motors(speed_limit):
    """Host 명령(speed_limit: -1.0 ~ 1.0)에 따라 주행"""
    # -1.0 ~ 1.0 값을 0 ~ 100의 Duty Cycle로 변환
    duty_cycle = abs(speed_limit) * 100
    duty_cycle = max(0, min(100, duty_cycle))
    
    if speed_limit > 0:
        print(f" -> [MOTOR] 4WD 전진 중... (속도: {speed_limit:.2f})")
        # 전진 (IN1: HIGH, IN2: LOW)
        for in1, in2 in [(LF_IN1, LF_IN2), (LR_IN1, LR_IN2), (RF_IN1, RF_IN2), (RR_IN1, RR_IN2)]:
            GPIO.output(in1, GPIO.HIGH)
            GPIO.output(in2, GPIO.LOW)
            
    elif speed_limit < 0:
        print(f" -> [MOTOR] 4WD 후진 중... (속도: {speed_limit:.2f})")
        # 후진 (IN1: LOW, IN2: HIGH)
        for in1, in2 in [(LF_IN1, LF_IN2), (LR_IN1, LR_IN2), (RF_IN1, RF_IN2), (RR_IN1, RR_IN2)]:
            GPIO.output(in1, GPIO.LOW)
            GPIO.output(in2, GPIO.HIGH)
    else:
        stop_motors("SPEED_ZERO")
        return

    # 속도(PWM) 적용
    pwm_lf.ChangeDutyCycle(duty_cycle)
    pwm_lr.ChangeDutyCycle(duty_cycle)
    pwm_rf.ChangeDutyCycle(duty_cycle)
    pwm_rr.ChangeDutyCycle(duty_cycle)

def stop_motors(reason):
    """모든 모터 정지 및 PWM 차단"""
    print(f" -> [MOTOR] 🛑 강제 정지! (사유: {reason})")
    
    if pwm_lf: pwm_lf.ChangeDutyCycle(0)
    if pwm_lr: pwm_lr.ChangeDutyCycle(0)
    if pwm_rf: pwm_rf.ChangeDutyCycle(0)
    if pwm_rr: pwm_rr.ChangeDutyCycle(0)
    
    for pin in [LF_IN1, LF_IN2, LR_IN1, LR_IN2, RF_IN1, RF_IN2, RR_IN1, RR_IN2]:
        GPIO.output(pin, GPIO.LOW)

# =======================================
# 4. 메인 UDP 수신 및 타임아웃 로직
# =======================================
def main():
    global last_cmd_time, current_ttl_seconds, is_moving
    
    setup_motors()
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LISTEN_IP, LISTEN_PORT))
    sock.settimeout(0.05) # 50ms마다 깨어나서 타임아웃 감시
    
    print(f"\n[VEHICLE] 차량 제어부 가동 시작. 관제 명령 대기 중... (포트: {LISTEN_PORT})")
    
    try:
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                cmd = json.loads(data.decode('utf-8'))
                
                # 수신 성공 시 타임아웃 갱신
                last_cmd_time = time.time()
                current_ttl_seconds = cmd.get("ttl_ms", 300) / 1000.0
                
                allow_motion = cmd.get("allow_motion", False)
                fault = cmd.get("fault", "UNKNOWN")
                speed = cmd.get("speed_limit", 0.0)
                
                if allow_motion:
                    is_moving = True
                    drive_motors(speed)
                else:
                    if is_moving:
                        is_moving = False
                        stop_motors(fault)
                        
            except socket.timeout:
                # 지정된 시간(0.3초) 동안 명령이 없으면 강제 정지
                time_since_last_cmd = time.time() - last_cmd_time
                if is_moving and time_since_last_cmd > current_ttl_seconds:
                    is_moving = False
                    print(f"\n[ERROR] LEASE_TIMEOUT: {current_ttl_seconds}초 이상 명령 수신 끊김!")
                    stop_motors("COMM_LOSS")
                    
            except json.JSONDecodeError:
                pass 

    except KeyboardInterrupt:
        print("\n[VEHICLE] 프로그램 종료. 모터 전력 차단.")
    finally:
        stop_motors("PROGRAM_EXIT")
        GPIO.cleanup()

if __name__ == "__main__":
    main()
