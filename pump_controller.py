def execute_mix(cmd: dict) -> bool:
    """
    서버에서 받은 명령(cmd)을 해석해서
    vitamin / melatonin / magnesium / electrolyte 순서대로
    필요한 만큼 펌프를 구동한다.

    서버에서 오는 값 단위: mg
    우리는 mg -> mL 로 변환해서 펌프 시간을 계산한다.
    """
    init_gpio()

    try:
        channels = ["vitamin", "melatonin", "magnesium", "electrolyte"]
        total_duration = 0.0

        for ch in channels:
            # 1) 서버 값 가져오기
            raw_val = cmd.get(ch, 0)

            try:
                mg_value = float(raw_val) if raw_val is not None else 0.0
            except (ValueError, TypeError):
                mg_value = 0.0

            if mg_value < 0:
                mg_value = 0.0

            # 2) mg -> mL 변환
            # 액상 비타민/전해질/마그네슘 같은 애들 대부분 물 비슷하다고 보고
            # 밀도≈1g/mL 라고 가정해서 mg(밀리그램)를 mL로 바꾼다.
            # 1000 mg = 1 mL 로 처리.
            volume_ml = mg_value / 1000.0

            # 3) 실제로 그 채널이 존재하고, 뽑아야 할 양이 0보다 크면 펌프 돌림
            if volume_ml > 0.0 and ch in PUMP_TABLE:
                spec = PUMP_TABLE[ch]

                # 필요한 구동 시간(초)
                duration = volume_ml * spec.sec_per_ml

                # 디버깅/보정용 로그
                log.info(
                    f"[MIX] ch={ch} mg={mg_value} -> ml={volume_ml:.4f} "
                    f"sec_per_ml={spec.sec_per_ml} -> duration={duration:.2f}s"
                )

                total_duration += duration

                # 실제 GPIO 구동
                _run_pump_gpio(ch, duration)

                # 채널 사이 쉬어주기 (압 안정화, 역류 방지)
                time.sleep(0.15)

        if total_duration == 0.0:
            log.info("모든 채널이 요청량 0mg → 펌프 미동작 (성공 처리)")

        log.info("믹싱 완료 (GPIO)")
        return True

    except Exception as e:
        log.exception(f"execute_mix 실패: {e}")
        return False

    finally:
        cleanup_gpio()
        log.info("GPIO cleanup complete")
