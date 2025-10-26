# listener.py
import json
import logging
import paho.mqtt.client as mqtt

from pump_controller import execute_mix
from common import (
    DEVICE_UUID,
    BROKER_HOST,
    BROKER_PORT,
    topics,
    parse_command_payload,
)
from publisher import (
    get_client,
    publish_register,
    publish_command_response,
)

log = logging.getLogger("listener")
if not log.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s"
    )

def on_connect(client: mqtt.Client, userdata, flags, rc):
    """
    MQTT 브로커에 붙었을 때 한 번 호출됨.
    구독 설정 + register 메시지 전송.
    (현재 paho Client는 v3 모드라 rc 인자 형태 OK)
    """
    log.info(
        f"MQTT connected rc={rc}  BROKER={BROKER_HOST}:{BROKER_PORT}  UUID={DEVICE_UUID}"
    )

    t = topics()

    # 서버가 보내는 응답/명령 받기
    client.subscribe(t["sub_register_resp"], qos=1)
    client.subscribe(t["sub_command"], qos=1)

    # 부팅 알림 (기기 등록)
    publish_register(client)

def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    """
    모든 수신 MQTT 메시지 처리.
    sub_register_resp / sub_command 두 가지를 본다.
    """
    topic = msg.topic

    # JSON 디코딩
    try:
        data = json.loads(msg.payload.decode())
    except Exception as e:
        log.error(f"JSON decode error on {topic}: {e}")
        return

    log.info(f"📩 RECV  {topic} {data}")

    t = topics()

    # 1) 서버가 register 응답 준 경우
    if topic == t["sub_register_resp"]:
        # 예: {"uuid":"...","status":"SUCCESS"}
        log.info(f"Register response: {data}")
        return

    # 2) 서버가 '이 조합으로 펌핑해라'라고 명령 준 경우
    if topic == t["sub_command"]:
        try:
            cmd = parse_command_payload(data)
            command_uuid = cmd.get("commandUuid")
            if not command_uuid:
                log.error("commandUuid missing in command payload")
                return

            # 실제 펌프 동작
            ok = execute_mix(cmd)

        except Exception as e:
            log.exception(f"command handling error: {e}")
            ok = False
            command_uuid = data.get("commandUuid")  # 최소한 응답은 하자

        status = "SUCCESS" if ok else "FAIL"
        publish_command_response(client, command_uuid, status)
        return

    # 그 외 토픽은 무시
    log.info(f"Unhandled topic: {topic}")

def main():
    client = get_client()
    client.on_connect = on_connect
    client.on_message = on_message

    # 브로커 접속
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)

    # MQTT 루프 (blocking)
    client.loop_forever()

if __name__ == "__main__":
    main()
