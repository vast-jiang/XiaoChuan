import sys
import os
import time
import threading

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web.app import start_server, ctrl, vision, sens
from hardware.ibus_reader import XiaoChuan_Receiver
from core.pid import PIDController

def rc_control_loop():
    """系统主控循环"""
    receiver = XiaoChuan_Receiver()
    print("[SYS] XiaoChuan Core Engine Started")

    rc_or_ai_was_active = False
    last_swc_state = 1000
    last_swd_state = 1000
    last_ai_state = False
    last_telemetry_time = 0

    # PID 控制器初始化与参数调优
    steer_pid = PIDController(kp=0.008, ki=0.0002, kd=0.003, max_out=1.0)
    last_loop_time = time.time()

    while True:
        current_time = time.time()
        dt = current_time - last_loop_time
        last_loop_time = current_time

        receiver.update()

        if receiver.is_connected:
            throttle = (receiver.throttle - 1500) / 500.0
            steer = (receiver.steer - 1500) / 500.0

            if abs(throttle) < 0.1: throttle = 0.0
            if abs(steer) < 0.1: steer = 0.0

            try:
                if hasattr(receiver, 'channels') and len(receiver.channels) >= 6:
                    raw_swc = receiver.channels[4]
                    raw_swd = receiver.channels[5]
                else:
                    raw_swc = getattr(receiver, 'bait_switch', last_swc_state)
                    raw_swd = getattr(receiver, 'swd', last_swd_state)
            except Exception:
                raw_swc = last_swc_state
                raw_swd = last_swd_state

            current_swc = raw_swc if 900 <= raw_swc <= 2100 else last_swc_state
            current_swd = raw_swd if 900 <= raw_swd <= 2100 else last_swd_state

            if current_swd > 1800 and last_swd_state <= 1800:
                ctrl.drop_bait()
                print("[CMD] Bait dropped via SwD")
            last_swd_state = current_swd

            ai_mode_enabled = (current_swc > 1800)
            if ai_mode_enabled != last_ai_state:
                print(f"[SYS] AI Mode: {'ON' if ai_mode_enabled else 'OFF'}")
                if ai_mode_enabled:
                    steer_pid.reset()
                last_ai_state = ai_mode_enabled
            last_swc_state = current_swc

            if current_time - last_telemetry_time > 5.0:
                try:
                    n = sens.get_reading()
                    d = sens.get_distance()
                    t = sens.get_temp()
                    print(f"[STAT] Dist:{d:>5.1f}cm | Turb:{n:>4.1f}% | Temp:{int(t)}C")
                except Exception:
                    pass
                last_telemetry_time = current_time

            human_is_active = (throttle != 0.0 or steer != 0.0)

            if human_is_active:
                ctrl.rc_override(throttle, steer)
                rc_or_ai_was_active = True
                
            elif ai_mode_enabled:
                target = vision.get_target_data()
                if target["x"] is not None:
                    error = target["x"] - (target["width"] / 2.0)
                    ai_steer = steer_pid.compute(error, dt)
                    
                    # 动态油门：大角度转向时降速以提升差速效率
                    ai_throttle = 0.45 - (abs(ai_steer) * 0.15)
                    ai_throttle = max(0.35, ai_throttle) 
                    
                    # 死区补偿：防止低 PWM 信号导致的电机停转
                    if 0 < ai_steer < 0.15: ai_steer = 0.15
                    if -0.15 < ai_steer < 0: ai_steer = -0.15

                    if target["area"] > 40000:
                        ctrl.halt() 
                    else:
                        ctrl.rc_override(ai_throttle, ai_steer) 
                else:
                    steer_pid.reset()
                    # 寻路模式：单侧驱动进行原地转向搜寻
                    ctrl.rc_override(0.0, 0.4) 
                rc_or_ai_was_active = True
            else:
                if rc_or_ai_was_active:
                    ctrl.halt() 
                    rc_or_ai_was_active = False
        else:
            if rc_or_ai_was_active:
                print("[WARN] RC Signal Lost. System halted.")
                ctrl.halt()
                rc_or_ai_was_active = False

        time.sleep(0.02)

if __name__ == "__main__":
    try:
        web_thread = threading.Thread(target=start_server, daemon=True)
        web_thread.start()
        rc_control_loop()
    except KeyboardInterrupt:
        print("\n[SYS] Terminating processes...")
        ctrl.halt()
        sys.exit(0)