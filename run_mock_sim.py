from mock_mqtt import MockBroker, MockClient
from listener import attach_listener
from publisher import publish_cmd
from common import TOPIC_ACK, loads

def main():
    broker = MockBroker()

    dev = MockClient(broker, "device")
    attach_listener(dev)     # 디바이스 클라이언트 등록

    backend = MockClient(broker, "backend")
    backend.connect()
    acks = []
    def on_ack(c,u,msg):
        print("[BACKEND] ACK:", msg.payload.decode())
        acks.append(loads(msg.payload.decode()))
    backend.on_message = on_ack
    backend.subscribe(TOPIC_ACK, qos=1)

    job = publish_cmd(backend, ch="A", pumps=3, unit_ms=350)
    assert any(x.get("jobId")==job and x.get("status")=="success" for x in acks)
    print("[TEST] OK")

if __name__ == "__main__":
    main()

