# pump_controller.py
"""
액상펌프 제어 (라즈베리파이 GPIO 릴레이 구동 버전)
- 시뮬 아닌 실제 GPIO 제어
- 펌프 1회(unit)당 동작 시간(sec_per_unit) 기반으로 릴레이 ON/OFF
- 릴레이 Active-Low(LOW=ON) 기준. 필요시 ACTIVE_LOW=False로 변경
"""

from dataclasses import dataclass
import logging
import time
from typing import Dict

import RPi.GPIO as GPIO  # 라즈베리파이에서 실행

log = logging.getLogger("pump")
if not log.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# ===== 릴레이/핀 설정 =====
ACTIVE_LOW = True        # 대부분의 릴레이 보드는 LOW=ON
GPIO.setmode(GPIO.BCM)   # BCM 번호 체계 사용
GPIO.setwarnings(False)

# 채널명 ↔ GPIO 핀 매핑 (실제 배선에 맞게 필요시 숫자만 바꾸면 됨)
PUMP_PINS: Dict[str, int] = {
    "vitamin":     17,   # GPIO17
    "melatonin":   27,   # GPIO27
    "magnesium":   22,   # GPIO22
    "electrolyte": 23,   # GPIO23
}

for pin in PUMP_PINS.values():
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH if ACTIVE_LOW else GPIO.LOW)

def _relay_on(pin: int):
    GPIO.output(pin, GPIO.LOW if ACTIVE_LOW else GPIO.HIGH)

def _relay_off(pin: int):
    GPIO.output(pin, GPIO.HIGH if ACTIVE_LOW else GPIO.LOW)

# ===== 펌프 사양(가정치) =====
@dataclass
class PumpSpec:
    name: str
    rate_mL_per_unit: float  # 1 unit 당 mL (설명용, 제어는 시간 기반)
    sec_per_unit: float      # 1 unit 동작 시간(초)

# 하드웨어 보정 시 아래 값만 조정
PUMP_TABLE: Dict[str, PumpSpec] = {
    "vitamin":     PumpSpec("vitamin",     rate_mL_per_unit=1.0, sec_per_unit=0.40),
    "melatonin":   PumpSpec("melatonin",   rate_mL_per_unit=0.5, sec_per_unit=0.35),
    "magnesium":   PumpSpec("magnesium",   rate_mL_per_unit=1.0, sec_per_unit=0.45),
    "electrolyte": PumpSpec("electrolyte", rate_mL_per_unit=1.2, sec_per_unit=0.50),
}

def _run_pump_real(channel: str, units: int) -> None:
    """지정 채널 펌프를 units 만큼 동작 (시간 = units * sec_per_unit)"""
    if channel not in PUMP_TABLE:
        log.error(f"알 수 없는 채널: {channel}")
        return
    if channel not in PUMP_PINS:
        log.error(f"핀 매핑이 없는 채널: {channel}")
        return
    if units <= 0:
        return

    spec = PUMP_TABLE[channel]
    pin = PUMP_PINS[channel]
    duration = max(0.0, units * spec.sec_per_unit)

    log.info(f"[REAL] {channel:10s} | units={units:3d} | ~{duration:.2f}s 동작")
    _relay_on(pin)
    try:
        time.sleep(duration)
    finally:
        _relay_off(pin)

def execute_mix(cmd: dict) -> bool:
    """
    서버에서 받은 명령 딕셔너리로 액상 배합 실행
    기대 키: commandUuid, vitamin, melatonin, magnesium, electrolyte
    성공 시 True, 실패 시 False
    """
    try:
        channels = ["vitamin", "melatonin", "magnesium", "electrolyte"]

        # 유효성 점검 + 총 유닛 계산 (로그용)
        total_units = 0
        for ch in channels:
            val = int(cmd.get(ch, 0) or 0)
            if val < 0:
                log.error(f"{ch} 값이 음수임: {val}")
                return False
            total_units += val
        log.info(f"배합 시작 | total_units={total_units} | cmdUuid={cmd.get('commandUuid')}")

        # 채널별 순차 구동
        for ch in channels:
            units = int(cmd.get(ch, 0) or 0)
            if units > 0:
                _run_pump_real(ch, units)

        log.info("배합 완료")
        return True

    except Exception as e:
        log.exception(f"배합 실패: {e}")
        return False

