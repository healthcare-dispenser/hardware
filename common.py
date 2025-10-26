# common.py
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# 환경 변수 로드 (.env)
load_dotenv()

BROKER_HOST = os.getenv("BROKER_HOST", "13.209.96.224")
BROKER_PORT = int(os.getenv("BROKER_PORT", "1883"))

# 라즈베리파이(디스펜서) 고유 ID
DEVICE_UUID = os.getenv("DEVICE_UUID", "dispenser-001")


def topic_base(uuid: str | None = None) -> str:
    return f"dispenser/{(uuid or DEVICE_UUID)}"


def topics(uuid: str | None = None) -> dict:
    base = topic_base(uuid)
    return {
        "pub_register":       f"{base}/register",
        "pub_command_resp":   f"{base}/command/response",
        "sub_register_resp":  f"{base}/register/response",
        "sub_command":        f"{base}/command",
    }


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def build_register_payload(uuid: str | None = None) -> dict:
    return {
        "uuid": (uuid or DEVICE_UUID)
    }


def build_command_response(
    command_uuid: str,
    status: str,
    uuid: str | None = None,
    complteAt: str | None = None,
) -> dict:
    return {
        "uuid": (uuid or DEVICE_UUID),
        "commandUuid": command_uuid,
        "status": status,
        # "completedAt": complteAt or now_iso(),
    }


def parse_command_payload(d: dict) -> dict:
    """
    서버가 내려주는 명령 JSON을 라즈에서 쓰기 좋은 형태로 정리.
    서버 측 키 기준:
      - zinc (아연)
      - magnesium (마그네슘)
      - electrolyte (전해질)
      - melatonin (멜라토닌)
    단위는 mg 라고 가정.
    """
    return {
        "commandUuid": d.get("commandUuid"),
        "zinc": d.get("zinc", 0),
        "magnesium": d.get("magnesium", d.get("magnesum", 0)),
        "electrolyte": d.get("electrolyte", 0),
        "melatonin": d.get("melatonin", 0),
    }
