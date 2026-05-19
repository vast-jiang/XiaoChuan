"""
XiaoChuan 极简数据记录器
"""
import time

class XiaoChuan_Logger:
    def __init__(self):
        self.filename = "data_log.csv"
        with open(self.filename, 'w') as f:
            f.write("Time,Mode,Link,Dist,Turb,L_PWM,R_PWM\n")

    def record(self, mode, link, dist, turb, l_pwm, r_pwm):
        try:
            with open(self.filename, 'a') as f:
                f.write(f"{time.strftime('%H:%M:%S')},{mode},{int(link)},{dist},{turb},{l_pwm},{r_pwm}\n")
        except:
            pass