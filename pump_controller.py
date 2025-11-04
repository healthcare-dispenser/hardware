import logging
import time
from dataclasses import dataclass
import RPi.GPIO as GPIO

log = logging.getLogger("pump")
if not log.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# ── 릴레이 핀 (Active-Low 가정) ──────────────────────────
PUMP_PINS = {
    "zinc":        17,  # Relay IN1
    "melatonin":   27,  # Relay IN2
    "magnesium":   22,  # Relay IN3
    "electrolyte": 23,  # Relay IN4
}
SLOT_PUMP_MAP = {
    1: "zinc",
    2: "melatonin",
    3: "magnesium",
    4: "electrolyte",
}

# ── GPIO ────────────────────────────────────────────────
def init_gpio():
    GPIO.setmode(GPIO.BCM)
    for pin in PUMP_PINS.values():
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)   # OFF (Active-Low)
    log.info("GPIO setup complete: Pumps are OFF")

def cleanup_gpio():
    GPIO.cleanup()
    log.info("GPIO cleanup complete")

# ── 보정값 ───────────────────────────────────────────────
@dataclass
class PumpSpec:
    name: str
    sec_per_ml: float = 0.024  # 실측 후 조정 권장

PUMP_TABLE: dict[str, PumpSpec] = {
    "zinc":        PumpSpec("zinc",        sec_per_ml=0.024),
    "melatonin":   PumpSpec("melatonin",   sec_per_ml=0.030),
    "magnesium":   PumpSpec("magnesium",   sec_per_ml=0.025),
    "electrolyte": PumpSpec("electrolyte", sec_per_ml=0.022),
}

# ── 저수준 제어 ─────────────────────────────────────────
def _run_pump_gpio(channel: str, duration: float) -> None:
    if duration <= 0:
        return
    pin = PUMP_PINS[channel]
    GPIO.output(pin, GPIO.LOW)   # ON
    log.info(f"[GPIO] {channel:11s} | PIN={pin} | {duration:.2f}s start")
    time.sleep(duration)
    GPIO.output(pin, GPIO.HIGH)  # OFF
    log.info(f"[GPIO] {channel:11s} | PIN={pin} | done")

# ── DISPENSE ────────────────────────────────────────────
def execute_mix(cmd: dict) -> bool:
    channels = ["zinc", "melatonin", "magnesium", "electrolyte"]
    init_gpio()
    try:
        total = 0.0
        for ch in channels:
            vol = float(cmd.get(ch, 0.0) or 0.0)
            vol = max(0.0, vol)
            if vol > 0.0 and ch in PUMP_TABLE:
                spec = PUMP_TABLE[ch]
                dur = vol * spec.sec_per_ml
                total += dur
                _run_pump_gpio(ch, dur)
                time.sleep(0.15)

        if total == 0.0:
            log.info("모든 채널 0.0 → 실행할 펌프 없음 (성공 처리)")
        log.info("믹싱 완료")
        return True
    except Exception as e:
        log.exception(f"execute_mix 실패: {e}")
        return False
    finally:
        cleanup_gpio()

# ── WASH ────────────────────────────────────────────────
def execute_wash(slot: int, wash_duration: float = 3.0) -> bool:
    if slot not in SLOT_PUMP_MAP:
        log.error(f"유효하지 않은 세척 슬롯: {slot}")
        return False
    ch = SLOT_PUMP_MAP[slot]
    init_gpio()
    try:
        log.info(f"💦 WASH {ch} (slot {slot}) {wash_duration:.1f}s")
        _run_pump_gpio(ch, wash_duration)
        log.info("세척 완료")
        return True
    except Exception as e:
        log.exception(f"세척 중 오류: {e}")
        return False
    finally:
        cleanup_gpio()

