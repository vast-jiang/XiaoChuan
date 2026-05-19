from adafruit_servokit import ServoKit
import time
import threading

class MotorController:
    """动力控制总线，负责双发电机混控与舵机调度"""
    def __init__(self):
        try:
            self.kit = ServoKit(channels=16)
            self.CH_BAIT = 0
            self.CH_LEFT = 1  
            self.CH_RIGHT = 2 

            self.REVERSE_LEFT = False
            self.REVERSE_RIGHT = True  

            self.LEFT_TRIM = 0.85
            self.RIGHT_TRIM = 1.0

            self.kit.servo[self.CH_LEFT].set_pulse_width_range(1000, 2000)
            self.kit.servo[self.CH_RIGHT].set_pulse_width_range(1000, 2000)

            self.kit.servo[self.CH_LEFT].angle = 90
            self.kit.servo[self.CH_RIGHT].angle = 90
            self.kit._pca.channels[self.CH_BAIT].duty_cycle = 0

            self.current_throttle = 0.0
            self.current_steer = 0.0

            time.sleep(3) # 电调初始化等待
            self.ready = True

        except Exception:
            self.ready = False

    def _update_mixer(self):
        """差速混控解算"""
        if not self.ready: return

        try:
            left_pwr = self.current_throttle + self.current_steer
            right_pwr = self.current_throttle - self.current_steer

            left_pwr *= self.LEFT_TRIM
            right_pwr *= self.RIGHT_TRIM

            if self.REVERSE_LEFT: left_pwr = -left_pwr
            if self.REVERSE_RIGHT: right_pwr = -right_pwr

            left_pwr = max(-1.0, min(1.0, left_pwr))
            right_pwr = max(-1.0, min(1.0, right_pwr))

            self.kit.servo[self.CH_LEFT].angle = 90 + (left_pwr * 90)
            self.kit.servo[self.CH_RIGHT].angle = 90 + (right_pwr * 90)
            
        except OSError:
            pass

    def set_drive(self, speed):
        self.current_throttle = speed / 100.0
        self._update_mixer()

    def set_steer(self, steer):
        self.current_steer = steer
        self._update_mixer()

    def rc_override(self, throttle, steer):
        self.current_throttle = throttle
        self.current_steer = steer
        self._update_mixer()

    def drop_bait(self):
        """触发投饵舵机单次循环"""
        if not self.ready: return
        def action():
            try:
                self.kit.continuous_servo[self.CH_BAIT].throttle = 1.0
                time.sleep(2)
                self.kit._pca.channels[self.CH_BAIT].duty_cycle = 0
            except OSError:
                pass
        threading.Thread(target=action).start()

    def halt(self):
        if self.ready:
            self.current_throttle = 0.0
            self.current_steer = 0.0
            try:
                self._update_mixer()
                self.kit._pca.channels[self.CH_BAIT].duty_cycle = 0
            except OSError:
                pass
