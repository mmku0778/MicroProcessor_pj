import RPi.GPIO as GPIO
import time

# 경고 끄기 및 BCM 핀 번호 사용 설정
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# 왼쪽 앞(LF) 모터 핀 설정 (BCM 번호 기준)
# 왼쪽 뒤(LR) 16, 20, 13 / 오른쪽 앞(RF) 23, 24, 18/ 오른쪽 뒤(RR) 21, 26, 19
AIN1 = 5
AIN2 = 6
PWMA = 12

# 핀을 출력 모드로 설정
GPIO.setup(AIN1, GPIO.OUT)
GPIO.setup(AIN2, GPIO.OUT)
GPIO.setup(PWMA, GPIO.OUT)

# PWM 설정 (주파수 100Hz)
pwm_a = GPIO.PWM(PWMA, 100)
pwm_a.start(0)

print("왼쪽 앞(LF) 모터 테스트 시작...")

try:
    # 직진 방향 설정 (하나는 HIGH, 하나는 LOW)
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)

    # 속도 50%로 모터 회전
    print("모터가 50% 속도로 3초간 회전합니다.")
    pwm_a.ChangeDutyCycle(50)
    time.sleep(3)

    # 모터 정지
    print("모터 정지.")
    pwm_a.ChangeDutyCycle(0)
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)

except KeyboardInterrupt:
    print("테스트 강제 종료.")

finally:
    # 핀 상태 초기화 (안전을 위해 필수)
    pwm_a.stop()
    GPIO.cleanup()
    print("GPIO 정리 완료.")
