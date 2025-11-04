# pump_controller.py 파일을 깨끗한 코드로 완전히 덮어씁니다.
cat << 'EOF' > pump_controller.py
# pump_controller.py

import logging
import time
from dataclasses import dataclass
import RPi.GPIO as GPIO # RPi.GPIO 모듈 추가

log = logging.getLogger("pump")
if not log.handlers:
    # 로깅 설정: RPi에서 실행할 때 콘솔에 로그가 출력되도록 설정
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# 1. GPIO 핀 설정 (pinmap.md 기반)
# 🚩 수정됨: vitamin -> zinc. 핀 번호와 영양제 채널 매핑.
PUMP_PINS = {
    # 릴레이는 Active Low(LOW 신호 시 ON)로 가정하고 배선됨
    "zinc": 17,    # GPIO17 → Relay IN1 (슬롯 1)
    "melatonin": 27,  # GPIO27 → Relay IN2 (슬롯 2)
    "magnesium": 22,  # GPIO22 → Relay IN3 (슬롯 3)
    "electrolyte": 23, # GPIO23 → Relay IN4 (슬롯 4)
}
# 슬롯 번호(1~4)와 채널 이름 매핑 (세척 로직용)
SLOT_PUMP_MAP = {
    1: "zinc",
    2: "melatonin",
    3: "magnesium",
    4: "electrolyte"
}


# 2. GPIO 초기화 및 정리 함수
def init_gpio():
    """펌프 구동을 위해 GPIO를 설정하고 핀을 HIGH(OFF) 상태로 초기화합니다."""
    GPIO.setmode(GPIO.BCM)
    for pin in PUMP_PINS.values():
        GPIO.setup(pin, GPIO.OUT)
        # 릴레이 OFF 상태 유지 (Active Low 가정)
        GPIO.output(pin, GPIO.HIGH)
    log.info("GPIO setup complete: Pumps are OFF")

def cleanup_gpio():
    """펌프 구동 후 GPIO를 정리하여 핀 상태를 해제합니다."""
    GPIO.cleanup()
    log.info("GPIO cleanup complete")


@dataclass
class PumpSpec:
    name: str
    # ★★★ 핵심 보정값: 1mL 배출에 필요한 시간(초). 간장 실험값 기반 (0.024 초/mL) ★★★
    sec_per_ml: float = 0.024 

# 채널별(영양소별) 펌프 스펙 — 실제 보정값을 측정하여 이 값을 반드시 수정해야 합니다.
PUMP_TABLE: dict[str, PumpSpec] = {
    "zinc":    PumpSpec("zinc",   sec_per_ml=0.024), 
    "melatonin":  PumpSpec("melatonin", sec_per_ml=0.030), 
    "magnesium":  PumpSpec("magnesium", sec_per_ml=0.025), 
    "electrolyte":PumpSpec("electrolyte",sec_per_ml=0.022), 
}


def _run_pump_gpio(channel: str, duration: float) -> None:
    """실제 GPIO 제어를 통해 펌프를 지정된 시간(초) 동안 구동합니다."""
    if duration <= 0: return

    pin = PUMP_PINS[channel]
    
    # 릴레이 ON (Active Low 가정: LOW 신호 시 ON)
    GPIO.output(pin, GPIO.LOW)
    log.info(f"[GPIO] {channel:11s} | PIN={pin} | {duration:.2f}s 동작 시작")
    time.sleep(duration) # 펌프 구동
    # 릴레이 OFF
    GPIO.output(pin, GPIO.HIGH)
    log.info(f"[GPIO] {channel:11s} | PIN={pin} | 동작 완료")


def execute_mix(cmd: dict) -> bool:
    """
    서버 명령 페이로드를 해석하여 펌프 제어를 실행합니다. (배출 로직)
    """
    # 🚩 zinc를 포함하도록 channels 리스트 변경
    channels = ["zinc", "melatonin", "magnesium", "electrolyte"] 
    total_duration = 0.0
    
    init_gpio() 
    
    try:
        for ch in channels:
            v_raw = cmd.get(ch, 0)
            try:
                volume_ml = float(v_raw) if v_raw is not None else 0.0
            except (ValueError, TypeError):
                volume_ml = 0.0

            volume_ml = max(0.0, volume_ml) 

            if volume_ml > 0.0 and ch in PUMP_TABLE: 
                spec = PUMP_TABLE[ch]
                duration = volume_ml * spec.sec_per_ml 
                total_duration += duration
                
                # 채널별 순차 구동
                _run_pump_gpio(ch, duration) 
                time.sleep(0.15) 

        if total_duration == 0.0:
            log.info("모든 채널이 0.0 → 실행할 펌프 없음 (성공 처리)")

        log.info("믹싱 완료 (GPIO)")
        return True

    except Exception as e:
        log.exception(f"execute_mix 실패: {e}")
        return False
    finally:
        cleanup_gpio() 


def execute_wash(slot: int, wash_duration: float = 3.0) -> bool:
    """
    🚩 세척 명령을 처리합니다. (DispenserController의 requestWash에 대응)
    """
    if slot not in SLOT_PUMP_MAP:
        log.error(f"유효하지 않은 세척 슬롯 번호: {slot}")
        return False
    
    channel = SLOT_PUMP_MAP[slot]
    
    log.info(f"💦 {channel} (Slot {slot}) {wash_duration:.1f}s 세척 시작...")
    
    init_gpio()
    try:
        # 세척은 정해진 시간(wash_duration) 동안 작동합니다.
        _run_pump_gpio(channel, wash_duration) 
        log.info(f"💦 {channel} 세척 완료.")
        return True
    except Exception as e:
        log.exception(f"세척 중 오류 발생: {e}")
        return False
    finally:
        cleanup_gpio()
EOF
