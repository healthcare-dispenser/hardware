# common.py
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# ── 환경변수 로드 ─────────────────────────────────────────────
load_dotenv()
BROKER_HOST = os.getenv("BROKER_HOST", "localhost")
BROKER_PORT = int(os.getenv("BROKER_PORT", "1883"))
DEVICE_UUID = os.getenv("DEVICE_UUID", "test-uuid-1234")

# ── 토픽 유틸 ────────────────────────────────────────────────
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

# ── 시간 포맷(백엔드 규격: complteAt) ────────────────────────
def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

# ── 페이로드 빌더(오타 스펙 포함) ────────────────────────────
def build_register_payload(uuid: str | None = None) -> dict:
    return { "uuid": (uuid or DEVICE_UUID) }

def build_command_response(command_uuid: str, status: str, uuid: str | None = None, complteAt: str | None = None) -> dict:
    # status: "SUCCESS" | "FAIL"
    return {
        "uuid": (uuid or DEVICE_UUID),
        "commandUuid": command_uuid,
        "status": status,
        "completedAt": complteAt or now_iso(),
    }

# ── 명령 파싱 유틸(백에서 'magnesum' 오타 대응) ─────────────
def parse_command_payload(d: dict) -> dict:
    return {
        "commandUuid": d.get("commandUuid"),
        "vitamin": d.get("vitamin", 0),
        "melatonin": d.get("melatonin", 0),
        "magnesium": d.get("magnesium", d.get("magnesum", 0)),
        "electrolyte": d.get("electrolyte", 0),
    }
