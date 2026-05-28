# TOPST Safe Car

## 1. 프로젝트 개요

본 프로젝트는 TOPST 보드를 활용한 안전주행 차량 시스템을 구현하는 것을 목표로 한다.

Raspberry Pi 4B를 이용하여 4개의 DC 모터를 제어하고, ToF 거리 센서를 이용하여 차량 전방의 장애물을 감지한다. 장애물이 기준 거리 이내에 감지되면 차량을 자동으로 정지시켜 안전주행 기능을 구현한다.

최종적으로는 TOPST 보드를 관제 장치로 활용하여 차량의 주행 상태를 관리하고, 위험 상황 발생 시 차량을 정지시키는 구조를 목표로 한다.

---

## 2. 프로젝트 목표

본 프로젝트의 목표는 다음과 같다.

- 4WD 차량의 하드웨어를 구성한다.
- Raspberry Pi GPIO를 이용하여 4개의 DC 모터를 제어한다.
- ToF 거리 센서를 이용하여 전방 장애물을 감지한다.
- 장애물이 기준 거리 이내에 감지되면 차량을 자동으로 정지시킨다.
- TOPST 보드를 이용하여 차량 상태를 관제하는 구조를 설계한다.
- 데모 시연을 통해 안전주행 기능을 정량적으로 검증한다.

---

## 3. 시스템 구성

본 시스템은 TOPST 관제부, Raspberry Pi 제어부, 4WD 차량 구동부, 센서부로 구성된다.

```text
TOPST Board
    ↓
Raspberry Pi 4B
    ↓
Motor Driver #1, #2
    ↓
4WD DC Motors

ToF Sensor
    ↓
Raspberry Pi 4B
    ↓
Obstacle Detection Logic
    ↓
Motor Stop
