import json
import logging
import paho.mqtt.client as mqtt

from pump_controller import execute_mix, execute_wash
from common import (
    BROKER_HOST, BROKER_PORT, DEVICE_UUID,
    topics, parse_command_payload,
)
from publisher import (
    get_client, publish_register, publish_command_response, publish_wash_response
)

log = logging.getLogger("listener")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

def on_connect(client: mqtt.Client, userdata, flags, rc):
    log.info(f"MQTT connected rc={rc}  BROKER={BROKER_HOST}:{BROKER_PORT}  UUID={DEVICE_UUID}")
    t = topics()
    client.subscribe(t["sub_register_resp"], qos=1)
    client.subscribe(t["sub_command"], qos=1)
    client.subscribe(t["sub_wash"], qos=1)
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
        log.info(f"Register response: {data}")
        return

    if topic == t["sub_command"]:
        cmd = parse_command_payload(data)
        command_uuid = cmd.get("commandUuid")
        if not command_uuid:
            log.error("commandUuid missing")
            return

        ok = False
        try:
            if cmd.get("commandType") == "WASH" and cmd.get("slot") is not None:
                ok = execute_wash(int(cmd.get("slot")), wash_duration=3.0)
            else:
                ok = execute_mix(cmd)
        except Exception as e:
            log.exception(f"execute error: {e}")
            ok = False

        publish_command_response(client, command_uuid, "SUCCESS" if ok else "FAIL")
        return

    if topic == t["sub_wash"]:
        try:
            slot = int(data.get("slot"))
        except Exception:
            log.error(f"세척 payload slot 파싱 실패: {data}")
            return

        ok = False
        try:
            ok = execute_wash(slot, wash_duration=3.0)
        except Exception as e:
            log.exception(f"세척 실행 중 오류: {e}")
            ok = False

        publish_wash_response(client, slot, "SUCCESS" if ok else "FAIL")
        return

def main():
    client = get_client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_forever()

if __name__ == "__main__":
    main()
