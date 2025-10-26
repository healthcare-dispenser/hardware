# publisher.py
import json
import logging
import paho.mqtt.client as mqtt
from common import (
    DEVICE_UUID,
    topics,
    build_register_payload,
    build_command_response,
)

log = logging.getLogger("publisher")
if not log.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s"
    )

def get_client() -> mqtt.Client:
    """
    MQTT 클라이언트 객체만 만들어서 돌려준다.
    (connect는 listener.py 쪽에서 한다)
    """
    client = mqtt.Client(
        client_id=DEVICE_UUID,
        clean_session=True,
    )
    return client

def publish_register(client: mqtt.Client):
    """
    라즈베리파이가 부팅/연결 직후 '나 여기 있어'라고 서버에 알려주는 등록 메시지 발행
    """
    t = topics()
    payload = build_register_payload()
    client.publish(t["pub_register"], json.dumps(payload), qos=1)
    log.info(f"➡️  PUBLISH {t['pub_register']} {payload}")

def publish_command_response(client: mqtt.Client, command_uuid: str, status: str):
    """
    펌프 동작 결과를 서버로 알려줌
    status: 'SUCCESS' 또는 'FAIL'
    """
    t = topics()
    payload = build_command_response(command_uuid, status)
    client.publish(t["pub_command_resp"], json.dumps(payload), qos=1)
    log.info(f"➡️  PUBLISH {t['pub_command_resp']} {payload}")
