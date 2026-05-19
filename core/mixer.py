"""
XiaoChuan 差速混控算法
"""
import config

def xiaochuan_mixer(throttle, steer):
    t_offset = throttle - config.PWM_MID
    s_offset = steer - config.PWM_MID
    left_pwm = max(-500, min(500, t_offset + s_offset))
    right_pwm = max(-500, min(500, t_offset - s_offset))
    return int(left_pwm + config.PWM_MID), int(right_pwm + config.PWM_MID)