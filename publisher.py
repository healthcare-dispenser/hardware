# publisher.py
import json
import logging
import paho.mqtt.client as mqtt

from common import (
    DEVICE_UUID, topics,
    build_register_payload, build_command_response, build_wash_response,
)

log = logging.getLogger("publisher")
if not log.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

def get_client() -> mqtt.Client:
    """
    MQTT 클라이언트 생성 (connect는 listener에서 수행)
    필요 시 .env로 아이디/비번, TLS 옵션을 붙일 수 있음.
    """
    client = mqtt.Client(client_id=DEVICE_UUID, clean_session=True)
    return client

def publish_register(client: mqtt.Client):
    t = topics()
    payload = build_register_payload()
    client.publish(t["pub_register"], json.dumps(payload), qos=1)
    log.info(f"➡️  PUBLISH {t['pub_register']} {payload}")

def publish_command_response(client: mqtt.Client, command_uuid: str, status: str):
    t = topics()
    payload = build_command_response(command_uuid, status)
    client.publish(t["pub_command_resp"], json.dumps(payload), qos=1)
    log.info(f"➡️  PUBLISH {t['pub_command_resp']} {payload}")

def publish_wash_response(client: mqtt.Client, slot: int, status: str):
    t = topics()
    payload = build_wash_response(slot, status)
    client.publish(t["pub_wash_resp"], json.dumps(payload), qos=1)
    log.info(f"➡️  PUBLISH {t['pub_wash_resp']} {payload}")
