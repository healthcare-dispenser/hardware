from pump_controller import PumpController

if __name__ == "__main__":
    pins = {"A":17, "B":27, "C":22, "D":23}
    pc = PumpController(pins, active_low=True, max_continuous_ms=2000, cooldown_ms=500)
    try:
        res = pc.dispense("A", pumps=3, unit_ms=350)
        print(res)
    finally:
        pc.cleanup()
