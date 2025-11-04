# listener.py 파일을 깨끗한 코드로 완전히 덮어씁니다.
cat << 'EOF' > listener.py
# listener.py
import json
import logging
import paho.mqtt.client as mqtt
from pump_controller import execute_mix, execute_wash # execute_wash 함수 추가

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
        log.info(f"Register response: {data}")

    # 2) 서버가 '이 조합대로 펌프 돌려' 또는 '세척해'라고 명령 내린 경우
    elif topic == t["sub_command"]:
        cmd = parse_command_payload(data)

        command_uuid = cmd.get("commandUuid")
        command_type = cmd.get("commandType", "DISPENSE") # 명령 유형을 확인
        
        if not command_uuid:
            log.error("commandUuid missing")
            return

        ok = False
        
        # 🚩 세척 명령 처리 (DispenserController.java의 requestWash에 대응)
        if command_type == "WASH" and cmd.get("slot") is not None:
            slot = cmd.get("slot")
            try:
                # 🚩 3.0초 동안 세척하도록 설정 (필요시 시간 변경 가능)
                ok = execute_wash(slot, wash_duration=3.0) 
            except Exception as e:
                log.exception(f"세척 실행 중 오류: {e}")
                ok = False
        
        # 🚩 배출 명령 처리
        elif command_type == "DISPENSE":
            try:
                ok = execute_mix(cmd)
            except Exception as e:
                log.exception(f"execute_mix error: {e}")
                ok = False
        
        # 🚩 응답 상태 전송
        status = "SUCCESS" if ok else "FAIL"

        publish_command_response(client, command_uuid, status)


def main():
    client = get_client()
    client.on_connect = on_connect
    client.on_message = on_message

    # 🔁 여기서 새 브로커(IP = 35.208.61.223)로 붙는다
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)

    # 메시지 계속 듣기
    client.loop_forever()


if __name__ == "__main__":
    main()
EOF
