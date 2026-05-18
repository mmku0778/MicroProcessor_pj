import RPi.GPIO as GPIO
import time

# 경고 끄기 및 BCM 핀 번호 설정
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# 전진, 좌회전, 우회전 확인

# =======================================
# 1. 핀 번호 설정 (BCM 기준)
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

# 핀 출력 모드 설정
for pin in motor_pins:
    GPIO.setup(pin, GPIO.OUT)

# =======================================
# 2. PWM (속도 제어) 설정
# =======================================
pwm_lf = GPIO.PWM(LF_PWM, 100)
pwm_lr = GPIO.PWM(LR_PWM, 100)
pwm_rf = GPIO.PWM(RF_PWM, 100)
pwm_rr = GPIO.PWM(RR_PWM, 100)

pwm_lf.start(0)
pwm_lr.start(0)
pwm_rf.start(0)
pwm_rr.start(0)

# =======================================
# 3. 주행 제어 함수 정의
# =======================================

def forward(speed=50):
    """4바퀴 모두 전진"""
    # 왼쪽 앞 (LF)
    GPIO.output(LF_IN1, GPIO.HIGH)
    GPIO.output(LF_IN2, GPIO.LOW)
    pwm_lf.ChangeDutyCycle(speed)

    # 왼쪽 뒤 (LR)
    GPIO.output(LR_IN1, GPIO.HIGH)
    GPIO.output(LR_IN2, GPIO.LOW)
    pwm_lr.ChangeDutyCycle(speed)

    # 오른쪽 앞 (RF)
    GPIO.output(RF_IN1, GPIO.HIGH)
    GPIO.output(RF_IN2, GPIO.LOW)
    pwm_rf.ChangeDutyCycle(speed)

    # 오른쪽 뒤 (RR)
    GPIO.output(RR_IN1, GPIO.HIGH)
    GPIO.output(RR_IN2, GPIO.LOW)
    pwm_rr.ChangeDutyCycle(speed)

def left(speed=50):
    """좌회전: 왼쪽 바퀴는 후진, 오른쪽 바퀴는 전진 (제자리 회전)"""
    # 왼쪽 바퀴 후진 (LOW, HIGH)
    GPIO.output(LF_IN1, GPIO.LOW)
    GPIO.output(LF_IN2, GPIO.HIGH)
    pwm_lf.ChangeDutyCycle(speed)
    
    GPIO.output(LR_IN1, GPIO.LOW)
    GPIO.output(LR_IN2, GPIO.HIGH)
    pwm_lr.ChangeDutyCycle(speed)

    # 오른쪽 바퀴 전진 (HIGH, LOW)
    GPIO.output(RF_IN1, GPIO.HIGH)
    GPIO.output(RF_IN2, GPIO.LOW)
    pwm_rf.ChangeDutyCycle(speed)
    
    GPIO.output(RR_IN1, GPIO.HIGH)
    GPIO.output(RR_IN2, GPIO.LOW)
    pwm_rr.ChangeDutyCycle(speed)

def right(speed=50):
    """우회전: 왼쪽 바퀴는 전진, 오른쪽 바퀴는 후진 (제자리 회전)"""
    # 왼쪽 바퀴 전진 (HIGH, LOW)
    GPIO.output(LF_IN1, GPIO.HIGH)
    GPIO.output(LF_IN2, GPIO.LOW)
    pwm_lf.ChangeDutyCycle(speed)
    
    GPIO.output(LR_IN1, GPIO.HIGH)
    GPIO.output(LR_IN2, GPIO.LOW)
    pwm_lr.ChangeDutyCycle(speed)

    # 오른쪽 바퀴 후진 (LOW, HIGH)
    GPIO.output(RF_IN1, GPIO.LOW)
    GPIO.output(RF_IN2, GPIO.HIGH)
    pwm_rf.ChangeDutyCycle(speed)
    
    GPIO.output(RR_IN1, GPIO.LOW)
    GPIO.output(RR_IN2, GPIO.HIGH)
    pwm_rr.ChangeDutyCycle(speed)

def stop():
    """모든 모터 정지"""
    pwm_lf.ChangeDutyCycle(0)
    pwm_lr.ChangeDutyCycle(0)
    pwm_rf.ChangeDutyCycle(0)
    pwm_rr.ChangeDutyCycle(0)
    
    for pin in [LF_IN1, LF_IN2, LR_IN1, LR_IN2, RF_IN1, RF_IN2, RR_IN1, RR_IN2]:
        GPIO.output(pin, GPIO.LOW)

# =======================================
# 4. 실행 테스트 (메인 로직)
# =======================================
if __name__ == "__main__":
    try:
        print("4WD 통합 주행 테스트를 시작합니다.")
        
        print("1. 전진 (3초)")
        forward(50)
        time.sleep(3)
        stop()
        time.sleep(1)
        
        print("2. 좌회전 (2초)")
        left(50)
        time.sleep(2)
        stop()
        time.sleep(1)

        print("3. 우회전 (2초)")
        right(50)
        time.sleep(2)
        stop()
        
    except KeyboardInterrupt:
        print("사용자에 의해 강제 종료되었습니다.")

    finally:
        # 핀 초기화 (안전)
        stop()
        pwm_lf.stop()
        pwm_lr.stop()
        pwm_rf.stop()
        pwm_rr.stop()
        GPIO.cleanup()
        print("GPIO 핀 정리가 완료되었습니다. 테스트를 종료합니다.")
