# common.py 파일을 깨끗한 코드로 완전히 덮어씁니다.
cat << 'EOF' > common.py
# common.py
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# .env 로드
load_dotenv()

# 브로커/서버 기본 설정
# 🚩 수정됨: BROKER_HOST를 새 IP로 변경
BROKER_HOST = os.getenv("BROKER_HOST", "35.208.61.223")
BROKER_PORT = int(os.getenv("BROKER_PORT", "1883"))

# 디스펜서 고유 UUID (앱/서버가 이 값으로 이 기기를 인식함)
DEVICE_UUID = os.getenv("DEVICE_UUID", "dispenser-001")

def topic_base(uuid: str | None = None) -> str:
    """토픽 prefix: dispenser/<uuid>"""
    return f"dispenser/{(uuid or DEVICE_UUID)}"

def topics(uuid: str | None = None) -> dict:
    """
    서버/라즈파이 간 MQTT 통신에 쓰는 모든 토픽들.
    pub_* = 라즈파이가 발행하는 쪽
    sub_* = 라즈파이가 구독하는 쪽
    """
    base = topic_base(uuid)
    return {
        "pub_register":       f"{base}/register",
        "pub_command_resp":   f"{base}/command/response",
        "sub_register_resp":  f"{base}/register/response",
        "sub_command":        f"{base}/command",
    }

def now_iso() -> str:
    """현재 시각을 ISO8601 문자열로 (초 단위까지)"""
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def build_register_payload(uuid: str | None = None) -> dict:
    """라즈베리파이가 '나 이 uuid 기기야' 하고 서버에 보내는 등록 페이로드"""
    return {
        "uuid": (uuid or DEVICE_UUID)
    }

def build_command_response(
    command_uuid: str,
    status: str,
    uuid: str | None = None,
    complteAt: str | None = None,
) -> dict:
    """
    서버 명령 실행 결과를 서버한테 알려줄 때 쓰는 페이로드
    status: "SUCCESS" 또는 "FAIL"
    """
    return {
        "uuid": (uuid or DEVICE_UUID),
        "commandUuid": command_uuid,
        "status": status,
    }

def parse_command_payload(d: dict) -> dict:
    """
    서버에서 내려온 raw 명령(JSON)을 우리가 쓰기 편한 dict 형태로 정리.
    세척(WASH) 명령과 배출(DISPENSE) 명령을 모두 처리할 수 있게 수정했습니다.
    """
    return {
        "commandUuid": d.get("commandUuid"),
        # 🚩 배출 명령에 사용되는 필드 (zinc로 변경됨)
        "zinc": d.get("zinc", 0), 
        "melatonin": d.get("melatonin", 0),
        "magnesium": d.get("magnesium", d.get("magnesum", 0)),
        "electrolyte": d.get("electrolyte", 0),
        # 🚩 세척 명령에 사용되는 필드
        "slot": d.get("slot"),
        "commandType": d.get("commandType", "DISPENSE") # 기본값은 DISPENSE로 가정
    }
EOF
