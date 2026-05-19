import time
try:
    import serial
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False

class XiaoChuan_Receiver:
    """i-BUS 协议解析器"""
    def __init__(self):
        self.PWM_MID = 1500
        self.channels = [self.PWM_MID] * 14
        self.is_connected = False
        self.last_update = time.time()
        self.ser = None
        
        if HAS_SERIAL:
            try:
                self.ser = serial.Serial('/dev/serial0', 115200, timeout=0.01)
            except Exception:
                pass

    def update(self):
        """解析串口数据帧"""
        if not self.ser: return
            
        try:
            while self.ser.in_waiting >= 32:
                # 校验数据帧头 0x20 0x40
                if self.ser.read(1) == b'\x20' and self.ser.read(1) == b'\x40':
                    data = self.ser.read(30)
                    if len(data) == 30:
                        for i in range(10):
                            self.channels[i] = data[i*2] | (data[i*2 + 1] << 8)
                        self.last_update = time.time()
                        self.is_connected = True
                        self.ser.reset_input_buffer()
                        break
        except Exception:
            pass
            
        # 0.5s 超时断连保护
        if time.time() - self.last_update > 0.5:
            self.is_connected = False
            self.channels = [self.PWM_MID] * 14

    @property
    def throttle(self): 
        return self.channels[1] 
        
    @property
    def steer(self): 
        return self.channels[3] 
        
    @property
    def bait_switch(self): 
        return self.channels[5]
