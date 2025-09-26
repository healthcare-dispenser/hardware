# pump_controller.py
"""
액상형 전용 펌프 제어 레이어 (시뮬레이션 버전)
- 실제 GPIO 제어 없이 로그만 출력하고 True/False 반환
- 다음 단계에서 RPi GPIO 붙일 예정
"""

from dataclasses import dataclass
import logging
import time

log = logging.getLogger("pump")
if not log.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# 1 단위 = 펌프 1회 가동이라고 가정 (초저비용 방식)
# 나중에 보정 필요하면 PUMP_TABLE의 rate만 수정하면 됨.
@dataclass
class PumpSpec:
    name: str
    rate_ml_per_unit: float = 1.0   # 펌프 1회(1 unit)당 mL (가정값)
    sec_per_unit: float = 0.4       # 펌프 1회 동작 시간(초) (가정값)

# 채널별(영양소별) 펌프 스펙 — 값은 가정, 하드웨어 보정 때 수정
PUMP_TABLE: dict[str, PumpSpec] = {
    "vitamin":    PumpSpec("vitamin",    rate_ml_per_unit=1.0, sec_per_unit=0.40),
    "melatonin":  PumpSpec("melatonin",  rate_ml_per_unit=0.5, sec_per_unit=0.35),
    "magnesium":  PumpSpec("magnesium",  rate_ml_per_unit=1.0, sec_per_unit=0.45),
    "electrolyte":PumpSpec("electrolyte",rate_ml_per_unit=1.2, sec_per_unit=0.50),
}

def _run_pump_sim(channel: str, units: int) -> None:
    """실제 GPIO 없이 시간만 기다리는 시뮬레이션."""
    spec = PUMP_TABLE[channel]
    duration = units * spec.sec_per_unit
    log.info(f"[SIM] {channel:11s} | units={units:3d} | ~{duration:.2f}s 동작")
    time.sleep(min(duration, 0.2))  # 로컬 테스트는 너무 오래 기다리지 않게 상한

def execute_mix(cmd: dict) -> bool:
    """
    cmd = {
      "commandUuid": "...",
      "vitamin": int, "melatonin": int, "magnesium": int, "electrolyte": int
    }
    반환: True(성공) / False(실패)
    """
    try:
        # 유효성 검사
        channels = ["vitamin", "melatonin", "magnesium", "electrolyte"]
        # 음수 방지 및 타입 정리
        amounts: dict[str, int] = {}
        total_units = 0
        for ch in channels:
            v_raw = cmd.get(ch, 0)
            v = int(v_raw) if v_raw is not None else 0
            if v < 0:
                v = 0
            amounts[ch] = v
            total_units += v

        if total_units == 0:
            log.info("모든 채널이 0 → 실행할 펌프 없음 (성공 처리)")
            return True

        # 채널별 순차 구동(동시에 안 돌리는 보수적 방식)
        for ch in channels:
            units = amounts[ch]
            if units <= 0:
                continue
            if ch not in PUMP_TABLE:
                log.error(f"정의되지 않은 채널: {ch}")
                return False
            _run_pump_sim(ch, units)

        log.info("믹싱 완료 (SIM)")
        return True

    except Exception as e:
        log.exception(f"execute_mix 실패: {e}")
        return False
