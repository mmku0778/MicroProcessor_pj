import time
import board
import busio
import adafruit_vl53l1x

# 1. I2C 통신 설정
i2c = busio.I2C(board.SCL, board.SDA)

# 2. ToF 센서 객체 생성 (VL53L1X 전용)
sensor = adafruit_vl53l1x.VL53L1X(i2c)

# 센서 측정 시작 (VL53L1X 필수 명령어)
sensor.start_ranging()

def get_distance():
    """데이터가 준비될 때까지 기다렸다가 한 번의 거리를 읽어오는 함수"""
    while not sensor.data_ready:
        time.sleep(0.01)
    
    dist = sensor.distance # cm 단위로 반환됨
    sensor.clear_interrupt() # 다음 측정을 위해 필수
    
    # 간혹 센서 오류로 None이 반환될 경우 0.0 처리
    return dist if dist is not None else 0.0

def get_median_distance(samples=5):
    """중간값 필터 적용 함수"""
    distances = []
    for _ in range(samples):
        distances.append(get_distance())
        time.sleep(0.02)
        
    distances.sort()
    return distances[samples // 2]

# 3. 실제 거리 측정 실행
if __name__ == "__main__":
    try:
        print("VL53L1X 센서 거리 측정 테스트를 시작합니다. (종료: Ctrl+C)")
        
        while True:
            # 원본 거리 읽기
            raw_dist_cm = get_distance()
            
            # 필터 적용된 거리 읽기
            filtered_dist_cm = get_median_distance(5)
            
            # 결과 출력
            print(f"원본 거리: {raw_dist_cm:5.1f} cm | 필터 적용 거리: {filtered_dist_cm:5.1f} cm")
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n테스트를 안전하게 종료합니다.")
    finally:
        # 프로그램 종료 시 센서 측정 안전하게 끄기
        sensor.stop_ranging()
