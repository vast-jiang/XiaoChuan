import time
import threading
import os

try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False

try:
    import board
    import busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    HAS_ADC = True
except ImportError:
    HAS_ADC = False

from collections import deque

class WaterSensors:
    def __init__(self, i2c_addr=0x48):
        # 超声波引脚配置 (BCM模式)
        self.TRIG_PIN = 23  
        self.ECHO_PIN = 24  
        self.distance_cm = -1.0
        
        # 滤波器缓存区，保存最近 7 次有效采样
        self.distance_history = deque(maxlen=7)
        
        if HAS_GPIO:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(self.TRIG_PIN, GPIO.OUT)
            GPIO.setup(self.ECHO_PIN, GPIO.IN)
            GPIO.output(self.TRIG_PIN, False)
            print(f"[硬件] 超声波测距就绪 (TRIG:{self.TRIG_PIN}, ECHO:{self.ECHO_PIN})")
        
        # ADS1115 ADC模块初始化
        self.adc_ready = False
        if HAS_ADC:
            try:
                i2c = busio.I2C(board.SCL, board.SDA)
                self.ads = ADS.ADS1115(i2c, address=i2c_addr)
                self.chan_turb = AnalogIn(self.ads, 0)
                self.adc_ready = True
                print(f"[硬件] 传感器总线 {hex(i2c_addr)} 在线")
            except Exception as e:
                print(f"[警告] ADS1115 模块异常: {e}")

        self._running = True
        if HAS_GPIO:
            threading.Thread(target=self._distance_loop, daemon=True).start()

    def _distance_loop(self):
        """超声波高频采集与复合滤波线程"""
        fail_count = 0
        
        # 启动前给传感器 0.5 秒的稳定时间
        time.sleep(0.5)
        
        while self._running:
            try:
                # 发射 15us 的高电平触发信号
                GPIO.output(self.TRIG_PIN, True)
                time.sleep(0.000015)
                GPIO.output(self.TRIG_PIN, False)

                timeout = time.perf_counter() + 0.04 # 40ms 超时阈值 (约限制在7米内)
                pulse_start = time.perf_counter()
                
                # 等待回波拉高
                while GPIO.input(self.ECHO_PIN) == 0 and time.perf_counter() < timeout:
                    pulse_start = time.perf_counter()
                        
                pulse_end = pulse_start
                # 等待回波拉低
                while GPIO.input(self.ECHO_PIN) == 1 and time.perf_counter() < timeout:
                    pulse_end = time.perf_counter()

                # 提取原始距离
                if pulse_end > pulse_start:
                    pulse_duration = pulse_end - pulse_start
                    raw_distance = pulse_duration * 17150
                    
                    if 2 <= raw_distance <= 400:
                        self.distance_history.append(raw_distance)
                        fail_count = 0
                        
                        # 复合滤波算法：去极值平均 + 一阶低通
                        if len(self.distance_history) >= 5:
                            # 1. 排序并掐头去尾 (去除最大值和最小值突刺)
                            sorted_history = sorted(list(self.distance_history))
                            valid_samples = sorted_history[1:-1]
                            
                            # 2. 计算修剪后的平均值
                            avg_dist = sum(valid_samples) / len(valid_samples)
                            
                            # 3. 低通平滑输出 (新数据占 40%，历史数据占 60%)
                            if self.distance_cm == -1.0:
                                self.distance_cm = round(avg_dist, 1)
                            else:
                                smoothed_dist = (self.distance_cm * 0.6) + (avg_dist * 0.4)
                                self.distance_cm = round(smoothed_dist, 1)
                    else:
                        fail_count += 1
                else:
                    fail_count += 1
                    
                # 连续 5 次(约0.3秒)无有效数据，判定为超量程或无障碍
                if fail_count >= 5:
                    self.distance_cm = -1.0
                    self.distance_history.clear()
                    
            except Exception:
                pass
                
            # 强制休眠 60ms，确保环境中残余声波完全消散，防止声波重叠干扰
            time.sleep(0.06)

    def get_distance(self):
        return self.distance_cm

    def get_reading(self):
        """获取浊度百分比"""
        if self.adc_ready:
            try:
                turb_raw = self.chan_turb.voltage
                turb_percent = (4.0 - turb_raw) / 3.0 * 100.0
                turb_percent = max(0.0, min(100.0, turb_percent))
                return round(turb_percent, 1)
            except OSError:
                return 0.0
        return 0.0

    def get_temp(self):
        """读取系统CPU温度"""
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                return float(f.read()) / 1000.0
        except Exception:
            return 0.0
        
    def cleanup(self):
        self._running = False
        if HAS_GPIO:
            GPIO.cleanup()
