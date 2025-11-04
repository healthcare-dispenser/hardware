cat > common.py <<'PY'
import os
import json
from dotenv import load_dotenv

# ── 환경변수 로드 ─────────────────────────────────────────────
load_dotenv()

BROKER_HOST = os.getenv("BROKER_HOST", "127.0.0.1")
BROKER_PORT = int(os.getenv("BROKER_PORT", "1883"))
DEVICE_UUID = os.getenv("DEVICE_UUID", "healthcaredispenser")

# ── 토픽 유틸 ────────────────────────────────────────────────
def topic_base(uuid: str | None = None) -> str:
    return f"dispenser/{(uuid or DEVICE_UUID)}"

def topics(uuid: str | None = None) -> dict:
    base = topic_base(uuid)
    return {
        # publish
        "pub_register":       f"{base}/register",
        "pub_command_resp":   f"{base}/command/response",
        "pub_wash_resp":      f"{base}/wash/response",

        # subscribe
        "sub_register_resp":  f"{base}/register/response",
        "sub_command":        f"{base}/command",
        "sub_wash":           f"{base}/wash",
    }

# ── 페이로드 빌더 ────────────────────────────────────────────
def build_register_payload() -> dict:
    # 서버 스펙: dispenserUuid 키 사용
    return {"dispenserUuid": DEVICE_UUID}

def build_command_response(command_uuid: str, status: str) -> dict:
    return {"commandUuid": command_uuid, "status": status}

def build_wash_response(slot: int, status: str) -> dict:
    return {"slot": int(slot), "status": status}

# ── 명령 파서 ────────────────────────────────────────────────
def _to_float(v) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0

def parse_command_payload(data: dict) -> dict:
    """
    서버에서 내려오는 DISPENSE 명령 페이로드 표준화
    ex)
    {
      "commandUuid": "...",
      "commandType": "DISPENSE",
      "zinc": 5, "melatonin": 3, "magnesium": 4, "electrolyte": 8
    }
    """
    if not isinstance(data, dict):
        return {}

    return {
        "commandUuid": data.get("commandUuid"),
        "commandType": (data.get("commandType") or "DISPENSE").upper(),
        "zinc":         _to_float(data.get("zinc")),
        "melatonin":    _to_float(data.get("melatonin")),
        "magnesium":    _to_float(data.get("magnesium")),
        "electrolyte":  _to_float(data.get("electrolyte")),
        "slot":         data.get("slot"),
    }
PY
