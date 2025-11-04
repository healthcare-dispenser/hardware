# listener.py 파일을 깨끗한 코드로 완전히 덮어씁니다.
cat << 'EOF' > listener.py
# listener.py
import json
import logging
import paho.mqtt.client as mqtt
from pump_controller import execute_mix

# 🔄 서버/브로커 설정
from common import (
    DEVICE_UUID,
    topics,
    parse_command_payload,
)
from publisher import get_client, publish_register, publish_command_response

# 👉 새 서버 / 브로커 IP (35.208.61.223으로 변경됨)
BROKER_HOST = "35.208.61.223"
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

    # 🔁 여기서 새 브로커로 붙는다
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)

    # 메시지 계속 듣기
    client.loop_forever()


if __name__ == "__main__":
    main()
EOF
