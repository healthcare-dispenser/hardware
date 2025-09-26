# publisher.py
import json
import logging
import paho.mqtt.client as mqtt

from common import (
    BROKER_HOST, BROKER_PORT, DEVICE_UUID,
    topics, build_register_payload, build_command_response
)

log = logging.getLogger("publisher")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

def get_client() -> mqtt.Client:
    client = mqtt.Client(client_id=DEVICE_UUID, clean_session=True)
    return client

def publish_register(client: mqtt.Client):
    t = topics()
    payload = build_register_payload()
    client.publish(t["pub_register"], json.dumps(payload), qos=1)
    log.info(f"➡️  PUBLISH {t['pub_register']} {payload}")

def publish_command_response(client: mqtt.Client, command_uuid: str, status: str):
    """
    status: 'SUCCESS' or 'FAIL'
    필드명은 백엔드 규격대로 complteAt 사용
    """
    t = topics()
    payload = build_command_response(command_uuid, status)
    client.publish(t["pub_command_resp"], json.dumps(payload), qos=1)
    log.info(f"➡️  PUBLISH {t['pub_command_resp']} {payload}")

if __name__ == "__main__":
    # 단독 테스트: 브로커 연결 → register 1회 발행
    log.info(f"BROKER={BROKER_HOST}:{BROKER_PORT}  UUID={DEVICE_UUID}")
    client = get_client()
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()
    publish_register(client)
    # 잠깐 대기 후 종료(테스트용)
    import time; time.sleep(1.5)
    client.loop_stop()
    client.disconnect()
