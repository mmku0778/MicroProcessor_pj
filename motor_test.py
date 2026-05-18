import RPi.GPIO as GPIO
import time

# 경고 끄기 및 BCM 핀 번호 설정
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# 사륜구동 확인

# =======================================
# 1. 핀 번호 설정 (BCM 기준)
# =======================================
# 드라이버 #1 (왼쪽)
LF_IN1, LF_IN2, LF_PWM = 5, 6, 12     # 왼쪽 앞 (LF)
LR_IN1, LR_IN2, LR_PWM = 16, 20, 13   # 왼쪽 뒤 (LR)

# 드라이버 #2 (오른쪽)
RF_IN1, RF_IN2, RF_PWM = 23, 24, 18   # 오른쪽 앞 (RF)
RR_IN1, RR_IN2, RR_PWM = 21, 26, 19   # 오른쪽 뒤 (RR)

# 모든 핀을 리스트로 묶어서 한 번에 설정하기 쉽게 만듦
motor_pins = [
    LF_IN1, LF_IN2, LF_PWM,
    LR_IN1, LR_IN2, LR_PWM,
    RF_IN1, RF_IN2, RF_PWM,
    RR_IN1, RR_IN2, RR_PWM
]

# 모든 핀을 출력(OUT) 모드로 설정
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
# 3. 전진 함수 정의
# =======================================
def move_forward(speed):
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

# =======================================
# 4. 정지 함수 정의
# =======================================
def stop_motors():
    pwm_lf.ChangeDutyCycle(0)
    pwm_lr.ChangeDutyCycle(0)
    pwm_rf.ChangeDutyCycle(0)
    pwm_rr.ChangeDutyCycle(0)
    
    for pin in [LF_IN1, LF_IN2, LR_IN1, LR_IN2, RF_IN1, RF_IN2, RR_IN1, RR_IN2]:
        GPIO.output(pin, GPIO.LOW)

# =======================================
# 5. 실제 구동 테스트 실행
# =======================================
try:
    print("🚗 4WD 동시 주행 테스트를 시작합니다!")
    print("바닥 마찰력을 이겨내고 전진합니다 (속도 50%)...")
    
    move_forward(50)  # 속도 50%로 전진
    time.sleep(3)     # 3초 동안 주행
    
    print("🛑 정지!")
    stop_motors()

except KeyboardInterrupt:
    print("강제 종료됨.")

finally:
    # 핀 초기화 (안전)
    pwm_lf.stop()
    pwm_lr.stop()
    pwm_rf.stop()
    pwm_rr.stop()
    GPIO.cleanup()
    print("테스트 종료.")
