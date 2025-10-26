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
# ⚠️ 반드시 실제 배선에 맞게 확인할 것.
# 예: IN1=아연, IN2=마그네슘 ... 이런 식으로 실제랑 다르면 여기 수정해야 함.
PUMP_PINS = {
    "zinc":        17,  # GPIO17 → Relay IN1 → 아연
    "magnesium":   27,  # GPIO27 → Relay IN2 → 마그네슘
    "electrolyte": 22,  # GPIO22 → Relay IN3 → 전해질
    "melatonin":   23,  # GPIO23 → Relay IN4 → 멜라토닌
}

def init_gpio():
    """
    펌프 돌리기 직전 GPIO 설정하고 전부 OFF(HIGH)로 초기화.
    릴레이가 Active Low라고 가정 (LOW=ON, HIGH=OFF).
    """
    GPIO.setmode(GPIO.BCM)
    for pin in PUMP_PINS.values():
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)  # OFF 상태
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
    # 몇 초를 돌려야 1 mL 나오는지.
    # 실제로 재서 교정할 값.
    sec_per_ml: float

# 초기 추정값 (임시). 나중에 실측해서 바꿔.
PUMP_TABLE: dict[str, PumpSpec] = {
    "zinc":        PumpSpec("zinc",        sec_per_ml=0.03),
    "magnesium":   PumpSpec("magnesium",   sec_per_ml=0.03),
    "electrolyte": PumpSpec("electrolyte", sec_per_ml=0.03),
    "melatonin":   PumpSpec("melatonin",   sec_per_ml=0.03),
}

def _run_pump_gpio(channel: str, duration: float) -> None:
    """
    특정 채널 펌프를 duration초 동안 켰다가 끈다.
    """
    if duration <= 0:
        return

    pin = PUMP_PINS[channel]

    # 펌프 ON (LOW)
    GPIO.output(pin, GPIO.LOW)
    log.info(f"[GPIO] {channel:11s} | PIN={pin} | {duration:.2f}s 동작 시작")

    time.sleep(duration)

    # 펌프 OFF (HIGH)
    GPIO.output(pin, GPIO.HIGH)
    log.info(f"[GPIO] {channel:11s} | PIN={pin} | 동작 완료")

def execute_mix(cmd: dict) -> bool:
    """
    서버 명령(cmd)을 바탕으로 각 채널을 순서대로 펌핑.
    서버가 보내는 값은 mg 단위라고 가정 (예: magnesium=90.0).
    여기서 mg -> mL 로 변환해서 duration 계산.
    """
    init_gpio()

    try:
        # 이 순서대로 실행 (UI 기대 순서에 맞춰서 정하면 됨)
        channels = ["zinc", "magnesium", "electrolyte", "melatonin"]
        total_duration = 0.0

        for ch in channels:
            raw_val = cmd.get(ch, 0)

            try:
                mg_value = float(raw_val) if raw_val is not None else 0.0
            except (ValueError, TypeError):
                mg_value = 0.0

            if mg_value < 0:
                mg_value = 0.0

            # mg → mL 변환
            # 밀도≈1g/mL 가정: 1000 mg ≈ 1 mL
            volume_ml = mg_value / 1000.0

            if volume_ml > 0.0 and ch in PUMP_TABLE:
                spec = PUMP_TABLE[ch]

                duration = volume_ml * spec.sec_per_ml
                total_duration += duration

                # 디버깅용 상세 로그
                log.info(
                    f"[MIX] ch={ch} mg={mg_value} -> ml={volume_ml:.4f} "
                    f"sec_per_ml={spec.sec_per_ml} -> duration={duration:.2f}s"
                )

                _run_pump_gpio(ch, duration)
                time.sleep(0.15)  # 채널 간 쉬는 시간 (역류/기포 안정화)

        if total_duration == 0.0:
            log.info("모든 채널이 요청량 0mg → 펌프 미동작 (성공 처리)")

        log.info("믹싱 완료 (GPIO)")
        return True

    except Exception as e:
        log.exception(f"execute_mix 실패: {e}")
        return False

    finally:
        cleanup_gpio()
