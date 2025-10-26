def execute_mix(cmd: dict) -> bool:
    """
    서버 명령 페이로드를 해석하여 펌프 제어를 실행합니다.
    cmd의 값은 'mg' 단위라고 가정합니다. (서버 단위 맞춤)
    """
    init_gpio()  # 펌프 구동 직전에 GPIO 초기화
    
    try:
        channels = ["vitamin", "melatonin", "magnesium", "electrolyte"]
        total_duration = 0.0

        for ch in channels:
            v_raw = cmd.get(ch, 0)
            try:
                # float()으로 변환
                volume_value = float(v_raw) if v_raw is not None else 0.0
            except (ValueError, TypeError):
                volume_value = 0.0

            volume_value = max(0.0, volume_value)  # 음수 방지

            # ✅ 서버는 mg 단위로 값을 주기 때문에 mL로 변환 (밀도 ≒ 1 기준)
            volume_ml = volume_value / 1000.0

            if volume_ml > 0.0 and ch in PUMP_TABLE:
                spec = PUMP_TABLE[ch]
                duration = volume_ml * spec.sec_per_ml  # 필요한 구동 시간 계산
                total_duration += duration

                # 채널별 순차 구동
                _run_pump_gpio(ch, duration)
                time.sleep(0.15)

        if total_duration == 0.0:
            log.info("모든 채널이 0.0 → 실행할 펌프 없음 (성공 처리)")

        log.info("믹싱 완료 (GPIO)")
        return True

    except Exception as e:
        log.exception(f"execute_mix 실패: {e}")
        return False
    finally:
        cleanup_gpio()  # 펌프 구동 후 GPIO 정리
