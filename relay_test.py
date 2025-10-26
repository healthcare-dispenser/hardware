# relay_test.py
import time
import RPi.GPIO as GPIO

PINS = [17, 27, 22, 23]   # IN1..IN4에 연결한 GPIO
ACTIVE_LOW = True         # 릴레이가 LOW에서 켜지면 True

GPIO.setmode(GPIO.BCM)
for p in PINS:
    GPIO.setup(p, GPIO.OUT, initial=(GPIO.HIGH if ACTIVE_LOW else GPIO.LOW))

def on(pin):
    GPIO.output(pin, GPIO.LOW if ACTIVE_LOW else GPIO.HIGH)

def off(pin):
    GPIO.output(pin, GPIO.HIGH if ACTIVE_LOW else GPIO.LOW)

try:
    while True:
        for pin in PINS:
            print(f"PIN {pin} ON")
            on(pin)
            time.sleep(1.0)
            print(f"PIN {pin} OFF")
            off(pin)
            time.sleep(0.5)
except KeyboardInterrupt:
    pass
finally:
    # 모두 끄고 종료
    for p in PINS:
        off(p)
    GPIO.cleanup()
