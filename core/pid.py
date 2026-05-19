"""
PID 控制器算法实现
"""
class PIDController:
    def __init__(self, kp, ki, kd, max_out=1.0):
        self.kp = kp  # 比例系数
        self.ki = ki  # 积分系数
        self.kd = kd  # 微分系数
        self.max_out = max_out  # 输出限幅
        
        self.prev_error = 0.0
        self.integral = 0.0
        self.max_integral = 200.0 # 积分抗饱和限幅

    def compute(self, error, dt):
        """
        计算控制量输出
        """
        if dt <= 0.0:
            return 0.0
            
        p_out = self.kp * error
        
        self.integral += error * dt
        self.integral = max(-self.max_integral, min(self.max_integral, self.integral))
        i_out = self.ki * self.integral
        
        derivative = (error - self.prev_error) / dt
        d_out = self.kd * derivative
        
        self.prev_error = error
        output = p_out + i_out + d_out
        
        return max(-self.max_out, min(self.max_out, output))
        
    def reset(self):
        """重置控制器状态变量"""
        self.prev_error = 0.0
        self.integral = 0.0
