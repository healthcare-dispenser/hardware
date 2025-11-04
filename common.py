import os
from dotenv import load_dotenv

load_dotenv()

BROKER_HOST = os.getenv("BROKER_HOST", "127.0.0.1")
BROKER_PORT = int(os.getenv("BROKER_PORT", "1883"))
DEVICE_UUID = os.getenv("DEVICE_UUID", "healthcaredispenser")

def topic_base(uuid: str | None = None) -> str:
    return f"dispenser/{(uuid or DEVICE_UUID)}"

def topics(uuid: str | None = None) -> dict:
    base = topic_base(uuid)
    return {
        "pub_register":       f"{base}/register",
        "pub_command_resp":   f"{base}/command/response",
        "pub_wash_resp":      f"{base}/wash/response",
        "sub_register_resp":  f"{base}/register/response",
        "sub_command":        f"{base}/command",
        "sub_wash":           f"{base}/wash",
    }

# 서버가 'uuid' 키를 기대 → 여기서 통일
def build_register_payload() -> dict:
    return {"uuid": DEVICE_UUID}

def build_command_response(command_uuid: str, status: str) -> dict:
    return {"commandUuid": command_uuid, "status": status}

def build_wash_response(slot: int, status: str) -> dict:
    return {"slot": int(slot), "status": status}

def _to_float(v) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0

def parse_command_payload(data: dict) -> dict:
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
