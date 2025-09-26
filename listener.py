# listener.py
import json
import logging
import paho.mqtt.client as mqtt
from pump_controller import execute_mix


from common import (
    BROKER_HOST, BROKER_PORT, DEVICE_UUID,
    topics, parse_command_payload,
)
from publisher import get_client, publish_register, publish_command_response

log = logging.getLogger("listener")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

def on_connect(client: mqtt.Client, userdata, flags, rc):
    log.info(f"MQTT connected rc={rc}  BROKER={BROKER_HOST}:{BROKER_PORT}  UUID={DEVICE_UUID}")
    t = topics()
    # 서버가 주는 응답/명령을 구독
    client.subscribe(t["sub_register_resp"], qos=1)
    client.subscribe(t["sub_command"], qos=1)
    # 최초 등록 publish
    publish_register(client)

def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    topic = msg.topic
    try:
        data = json.loads(msg.payload.decode())
    except Exception as e:
        log.error(f"JSON decode error on {topic}: {e}")
        return

    log.info(f"📩 RECV  {topic} {data}")

    t = topics()
    if topic == t["sub_register_resp"]:
        # { "uuid": "...", "status": "SUCCESS|FAIL" }
        log.info(f"Register response: {data}")

    elif topic == t["sub_command"]:
        # { "commandUuid", "vitamin", "melatonin", "magnesum|magnesium", "electrolyte" }
        cmd = parse_command_payload(data)
        command_uuid = cmd.get("commandUuid")
        if not command_uuid:
            log.error("commandUuid missing")
            return

        # 펌프 제어 실행 (현재는 시뮬레이션; GPIO는 추후 교체)
        try:
            ok = execute_mix(cmd)
        except Exception as e:
            log.exception(f"execute_mix error: {e}")
            ok = False

        status = "SUCCESS" if ok else "FAIL"
        publish_command_response(client, command_uuid, status)


def main():
    client = get_client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_forever()

if __name__ == "__main__":
    main()
