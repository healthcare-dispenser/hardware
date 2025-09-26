from collections import defaultdict
from types import SimpleNamespace

class MockMessage:
    def __init__(self, topic, payload, qos=0):
        self.topic = topic
        self.payload = payload.encode() if isinstance(payload, str) else payload
        self.qos = qos

class MockBroker:
    def __init__(self): self.subs = defaultdict(list)
    def subscribe(self, topic, client): self.subs[topic].append(client)
    def publish(self, topic, payload, qos=0):
        for c in self.subs.get(topic, []):
            if getattr(c, "on_message", None):
                c.on_message(c, None, MockMessage(topic, payload, qos))
        return SimpleNamespace(rc=0)

class MockClient:
    def __init__(self, broker, client_id="mock"):
        self.broker=broker; self.client_id=client_id
        self.on_connect=None; self.on_message=None
    def connect(self, *a, **k):
        if self.on_connect: self.on_connect(self, None, None, 0, None)
    def subscribe(self, topic, qos=0): self.broker.subscribe(topic, self)
    def publish(self, topic, payload, qos=0, retain=False): return self.broker.publish(topic, payload, qos)
    def loop_forever(self): pass
