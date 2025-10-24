# 충돌이 발생한 파일을 백업합니다. (혹시 모를 원격 변경 사항 확인용)
cp pump_controller.py pump_controller_CONFLICT_BACKUP.py

# 새로운(충돌이 해결된) 내용을 pump_controller.py에 덮어씁니다.
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
# 라즈베리파이 GPIO 핀 번호와 영양제 채널 매핑
PUMP_PINS = {
    # 릴레이는 Active Low(LOW 신호 시 ON)로 가정하고 배선됨
    "vitamin": 17,    # GPIO17 → Relay IN1 (라인1)
    "melatonin": 27,  # GPIO27 → Relay IN2 (라인2)
    "magnesium": 22,  # GPIO22 → Relay IN3 (라인3)
    "electrolyte": 23, # GPIO23 → Relay IN4 (라인4)
}

# 2. GPIO 초기화 및 정리 함수
def init_gpio():
    """펌프 구동을 위해 GPIO를 설정하고 핀을 HIGH(OFF) 상태로 초기화합니다."""
    # 펌프 구동 직전에 호출
    GPIO.setmode(GPIO.BCM)
    for pin in PUMP_PINS.values():
        GPIO.setup(pin, GPIO.OUT)
        # 릴레이 OFF 상태 유지 (Active Low 가정)
        GPIO.output(pin, GPIO.HIGH)
    log.info("GPIO setup complete: Pumps are OFF")

def cleanup_gpio():
    """펌프 구동 후 GPIO를 정리하여 핀 상태를 해제합니다."""
    # 펌프 구동 후 항상 호출
    GPIO.cleanup()
    log.info("GPIO cleanup complete")


@dataclass
class PumpSpec:
    name: str
    # ★★★ 핵심 보정값: 1mL 배출에 필요한 시간(초). 실험 후 이 값을 수정해야 합니다. ★★★
    sec_per_ml: float = 0.40 

# 채널별(영양소별) 펌프 스펙 — 실제 보정값을 측정하여 이 값을 반드시 수정해야 합니다.
PUMP_TABLE: dict[str, PumpSpec] = {
    "vitamin":    PumpSpec("vitamin",   sec_per_ml=0.40),
    "melatonin":  PumpSpec("melatonin", sec_per_ml=0.70), # 멜라토닌이 점성이 높을 경우 시간이 더 걸릴 수 있음
    "magnesium":  PumpSpec("magnesium", sec_per_ml=0.45),
    "electrolyte":PumpSpec("electrolyte",sec_per_ml=0.42),
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
    서버 명령 페이로드를 해석하여 펌프 제어를 실행합니다.
    cmd의 값은 배출할 용량(mL)이라고 가정합니다.
    """
    init_gpio() # 펌프 구동 직전에 GPIO 초기화
    
    try:
        # 백엔드 팀의 명령 구조 (common.py의 parse_command_payload와 일치)
        channels = ["vitamin", "melatonin", "magnesium", "electrolyte"]
        total_duration = 0.0

        for ch in channels:
            v_raw = cmd.get(ch, 0)
            try:
                # float()으로 변환하여 정밀도(소수점)를 유지합니다.
                volume_ml = float(v_raw) if v_raw is not None else 0.0
            except (ValueError, TypeError):
                volume_ml = 0.0

            volume_ml = max(0.0, volume_ml) # 음수 방지

            if volume_ml > 0.0 and ch in PUMP_TABLE: # 0.0 초과인 경우만 실행
                spec = PUMP_TABLE[ch]
                duration = volume_ml * spec.sec_per_ml # 필요한 구동 시간(초) 계산
                total_duration += duration
                
                # 채널별 순차 구동
                _run_pump_gpio(ch, duration) # 실제 GPIO 구동
                time.sleep(0.15) # 펌프 구동 사이의 간격 (모터 안정화/액체 이동 대기)

        if total_duration == 0.0:
            log.info("모든 채널이 0.0 → 실행할 펌프 없음 (성공 처리)")

        log.info("믹싱 완료 (GPIO)")
        return True

    except Exception as e:
        log.exception(f"execute_mix 실패: {e}")
        return False
    finally:
        cleanup_gpio() # 펌프 구동 후 GPIO 정리
EOF
