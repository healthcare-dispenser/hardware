# tester.py
import json, time
import paho.mqtt.client as mqtt
from common import BROKER_HOST, BROKER_PORT, DEVICE_UUID, topics

def main():
    t = topics()
    cmd = {
        "commandUuid": "local-test-001",
        "vitamin": 2,
        "melatonin": 1,
        "magnesum": 3,   # 백엔드 스펙의 오탈자 그대로
        "electrolyte": 0
    }

    client = mqtt.Client(client_id=f"tester-{DEVICE_UUID}", clean_session=True)
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=30)
    client.loop_start()
    time.sleep(0.2)

    client.publish(t["sub_command"], json.dumps(cmd), qos=1)  # dispenser/{uuid}/command
    print(f"➡️  TEST PUBLISH {t['sub_command']} {cmd}")

    time.sleep(0.5)
    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    print(f"BROKER={BROKER_HOST}:{BROKER_PORT}  UUID={DEVICE_UUID}")
    main()
