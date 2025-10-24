# relay_test_one.py
import time
import RPi.GPIO as GPIO

PIN = 17
ACTIVE_LOW = False  # 릴레이가 LOW일 때 켜지면 True, HIGH일 때 켜지면 False

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.OUT, initial=(GPIO.HIGH if ACTIVE_LOW else GPIO.LOW))

def on():
    GPIO.output(PIN, GPIO.LOW if ACTIVE_LOW else GPIO.HIGH)

def off():
    GPIO.output(PIN, GPIO.HIGH if ACTIVE_LOW else GPIO.LOW)

try:
    while True:
        print("ON")
        on()
        time.sleep(1.0)

        print("OFF")
        off()
        time.sleep(1.0)
except KeyboardInterrupt:
    pass
finally:
    off()
    GPIO.cleanup()
