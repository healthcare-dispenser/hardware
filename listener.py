# listener.py
import json
import logging
import paho.mqtt.client as mqtt
from pump_controller import execute_mix

# 🔄 서버/브로커 설정
# 원래는 common.py에서 BROKER_HOST, BROKER_PORT, DEVICE_UUID 등을 import 했는데
# 서버 주소가 바뀌어서 여기서도 명확하게 적어준다.
# 만약 common.py도 같이 고칠 거면 아래 직접 지정 부분은 삭제하고
# 기존처럼 `from common import ...`만 써도 된다.

from common import (
    DEVICE_UUID,
    topics,
    parse_command_payload,
)
from publisher import get_client, publish_register, publish_command_response

# 👉 새 서버 / 브로커 IP
BROKER_HOST = "13.209.96.224"
BROKER_PORT = 1883  # MQTT 기본 포트 (팀에서 쓰는 값 유지)

log = logging.getLogger("listener")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")


def on_connect(client: mqtt.Client, userdata, flags, rc):
    log.info(f"MQTT connected rc={rc}  BROKER={BROKER_HOST}:{BROKER_PORT}  UUID={DEVICE_UUID}")

    t = topics()

    # 서버가 주는 응답/명령 토픽 구독
    client.subscribe(t["sub_register_resp"], qos=1)
    client.subscribe(t["sub_command"], qos=1)

    # 라즈베리파이가 처음 켜졌을 때 '나 여기 있어' 하고 서버에 자기 uuid 등록 보내는 부분
    publish_register(client)


def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    topic = msg.topic

    # 메시지(JSON) 파싱
    try:
        data = json.loads(msg.payload.decode())
    except Exception as e:
        log.error(f"JSON decode error on {topic}: {e}")
        return

    log.info(f"📩 RECV  {topic} {data}")

    t = topics()

    # 1) 서버가 등록 응답 준 경우
    if topic == t["sub_register_resp"]:
        # 예: { "uuid": "...", "status": "SUCCESS" }
        log.info(f"Register response: {data}")

    # 2) 서버가 '이 조합대로 펌프 돌려'라고 명령 내린 경우
    elif topic == t["sub_command"]:
        # data 예시:
        # {
        #   "commandUuid": "abc-123",
        #   "vitamin": 1,
        #   "melatonin": 0,
        #   "magnesium": 2,
        #   "electrolyte": 1
        # }
        cmd = parse_command_payload(data)

        command_uuid = cmd.get("commandUuid")
        if not command_uuid:
            log.error("commandUuid missing")
            return

        # 여기서 실제 펌프 구동 로직 실행
        try:
            ok = execute_mix(cmd)
        except Exception as e:
            log.exception(f"execute_mix error: {e}")
            ok = False

        status = "SUCCESS" if ok else "FAIL"

        # 우리가 성공/실패 결과를 다시 서버한테 알려줌
        publish_command_response(client, command_uuid, status)


def main():
    client = get_client()
    client.on_connect = on_connect
    client.on_message = on_message

    # 🔁 여기서 새 브로커(IP = 13.209.96.224)로 붙는다
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)

    # 메시지 계속 듣기
    client.loop_forever()


if __name__ == "__main__":
    main()
