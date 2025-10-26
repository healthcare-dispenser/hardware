# pump_controller.py
import logging
import time
from dataclasses import dataclass
import RPi.GPIO as GPIO  # 라즈베리파이 GPIO 제어

log = logging.getLogger("pump")
if not log.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s"
    )

# 릴레이 IN1~IN4에 대응하는 GPIO 번호 (BCM 기준)
# 릴레이는 Active Low라서 LOW면 켜지고 HIGH면 꺼진다고 가정
PUMP_PINS = {
    "vitamin": 17,       # GPIO17 → Relay IN1
    "melatonin": 27,     # GPIO27 → Relay IN2
    "magnesium": 22,     # GPIO22 → Relay IN3
    "electrolyte": 23,   # GPIO23 → Relay IN4
}

def init_gpio():
    """
    펌프 돌리기 직전에 GPIO 모드/핀 초기화하고
    기본값을 '꺼짐'(HIGH)으로 맞춘다.
    """
    GPIO.setmode(GPIO.BCM)
    for pin in PUMP_PINS.values():
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)  # Active Low 릴레이에서 HIGH = OFF
    log.info("GPIO setup complete: Pumps are OFF")

def cleanup_gpio():
    """
    동작 끝나면 GPIO 정리.
    """
    GPIO.cleanup()
    log.info("GPIO cleanup complete")

@dataclass
class PumpSpec:
    name: str
    # 1 mL 뽑는 데 걸리는 시간(초).
    # 실제 액상 점도/펌프에 따라 바꿔줘야 함.
    sec_per_ml: float = 0.40

# 펌프별 교정값(대략치). 나중에 실측해서 조정.
PUMP_TABLE: dict[str, PumpSpec] = {
    "vitamin":     PumpSpec("vitamin",     sec_per_ml=0.40),
    "melatonin":   PumpSpec("melatonin",   sec_per_ml=0.70),
    "magnesium":   PumpSpec("magnesium",   sec_per_ml=0.45),
    "electrolyte": PumpSpec("electrolyte", sec_per_ml=0.42),
}

def _run_pump_gpio(channel: str, duration: float) -> None:
    """
    특정 채널 펌프를 duration초 동안 구동했다가 중지.
    """
    if duration <= 0:
        return

    pin = PUMP_PINS[channel]

    # 릴레이 ON (LOW)
    GPIO.output(pin, GPIO.LOW)
    log.info(f"[GPIO] {channel:11s} | PIN={pin} | {duration:.2f}s 동작 시작")

    time.sleep(duration)  # 실제 펌핑

    # 릴레이 OFF (HIGH)
    GPIO.output(pin, GPIO.HIGH)
    log.info(f"[GPIO] {channel:11s} | PIN={pin} | 동작 완료")

def execute_mix(cmd: dict) -> bool:
    """
    서버에서 받은 명령(cmd)을 해석해서
    vitamin / melatonin / magnesium / electrolyte 순서대로
    필요한 만큼 펌프를 돌린다.

    cmd 예시:
    {
        "commandUuid": "abc-123",
        "vitamin": 1,
        "melatonin": 0,
        "magnesium": 2,
        "electrolyte": 1
    }
    """
    init_gpio()
    try:
        channels = ["vitamin", "melatonin", "magnesium", "electrolyte"]
        total_duration = 0.0

        for ch in channels:
            raw_val = cmd.get(ch, 0)

            # 안전하게 float 변환
            try:
                volume_ml = float(raw_val) if raw_val is not None else 0.0
            except (ValueError, TypeError):
                volume_ml = 0.0

            # 음수 방지
            if volume_ml < 0:
                volume_ml = 0.0

            # 실제로 돌릴 필요가 있으면
            if volume_ml > 0.0 and ch in PUMP_TABLE:
                spec = PUMP_TABLE[ch]
                duration = volume_ml * spec.sec_per_ml
                total_duration += duration

                _run_pump_gpio(ch, duration)
                time.sleep(0.15)  # 채널 사이 잠깐 기다려서 압 안정화

        if total_duration == 0.0:
            log.info("모든 채널 0mL → 펌프 동작 없음 (성공 처리)")

        log.info("믹싱 완료 (GPIO)")
        return True

    except Exception as e:
        log.exception(f"execute_mix 실패: {e}")
        return False

    finally:
        cleanup_gpio()
