# common.py
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# ── 환경변수 로드 ─────────────────────────────────────────────
load_dotenv()

# 서버/브로커 기본값을 새 서버 IP로 맞춤
BROKER_HOST = os.getenv("BROKER_HOST", "13.209.96.224")
BROKER_PORT = int(os.getenv("BROKER_PORT", "1883"))

# 디스펜서 UUID (라즈베리파이마다 다르게 넣어줄 값)
# .env에 DEVICE_UUID가 있으면 그걸 우선 사용하고,
# 없으면 기본값 "dispenser-001" 사용
DEVICE_UUID = os.getenv("DEVICE_UUID", "dispenser-001")

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

# ── 시간 포맷(백엔드 규격: completedAt/complteAt 호환) ────────
def now_iso() -> str:
    # 로컬 타임존 포함 ISO 문자열 (초 단위까지)
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

# ── 페이로드 빌더 ────────────────────────────────────────────
def build_register_payload(uuid: str | None = None) -> dict:
    # 서버에 "나 이 uuid 디스펜서야"라고 알릴 때 쓰는 페이로드
    return { "uuid": (uuid or DEVICE_UUID) }

def build_command_response(
    command_uuid: str,
    status: str,
    uuid: str | None = None,
    complteAt: str | None = None
) -> dict:
    # status: "SUCCESS" | "FAIL"
    # completedAt 필드는 서버가 섭취 완료 시각 기록할 때 사용
    return {
        "uuid": (uuid or DEVICE_UUID),
        "commandUuid": command_uuid,
        "status": status,
        "completedAt": complteAt or now_iso(),
    }

# ── 명령 파싱 유틸(백엔드 오타 'magnesum'까지 커버) ──────────
def parse_command_payload(d: dict) -> dict:
    return {
        "commandUuid": d.get("commandUuid"),
        "vitamin": d.get("vitamin", 0),
        "melatonin": d.get("melatonin", 0),
        "magnesium": d.get("magnesium", d.get("magnesum", 0)),
        "electrolyte": d.get("electrolyte", 0),
    }
