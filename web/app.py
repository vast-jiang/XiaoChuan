from flask import Flask, Response, render_template, request, jsonify
from hardware.motor_controller import MotorController
from hardware.sensors import WaterSensors
import time
import config
import logging

# 拦截屏蔽 werkzeug 产生的常规网页连接包日志，防止控制台爆满，保证响应性能
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
ctrl = MotorController()
sens = WaterSensors(config.I2C_ADDR_ADS)

# 动态加载摄像头及视觉 AI 执行框架
try:
    from vision.detector import XiaoChuan_Vision
    vision = XiaoChuan_Vision()
    has_cam = True
except Exception as e:
    print(f"[警告] 视觉流读取框架初始化异常，图传挂载降级: {e}")
    vision = None
    has_cam = False

@app.route('/')
def index(): 
    """加载并下发 Web 端控制控制台主页面"""
    return render_template('index.html')

@app.route('/stream')
def stream():
    """实时机器视觉图传 MJPEG 网络异步推流端点"""
    def gen():
        while True:
            if has_cam:
                b = vision.get_jpg() 
                if b: 
                    yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + b + b'\r\n')
            time.sleep(0.05)
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/t')
def telemetry():
    """传感器数据遥测数据下发端点 (供网页端 AJAX 高频秒级拉取)"""
    n = sens.get_reading() # 获取浊度数据
    return jsonify({
        "d": f"{sens.get_distance()} cm", # 距离
        "n": f"{n:.1f}%",                 # 浊度百分比
        "t": f"{int(sens.get_temp())}C"   # CPU温度
    })

@app.route('/c')
def command():
    """
    接收并翻译网页控制端虚拟键盘/按键指令的底层中转站
    支持参数：fw=前进、st=全机停转、lt=左转、rt=右转、ct=摇杆转向回正、db=异步投饵
    """
    q = request.args.get('q')
    if q == 'fw': 
        ctrl.set_drive(60)
    elif q == 'st': 
        ctrl.set_drive(0)
    elif q == 'lt': 
        ctrl.set_steer(-0.8)
    elif q == 'rt': 
        ctrl.set_steer(0.8)
    elif q == 'ct': 
        ctrl.set_steer(0.0)
    elif q == 'db': 
        ctrl.drop_bait()
    return "OK"

def start_server():
    """建立 Web API 网关核心服务服务器实例"""
    print(f"[系统] Web核心服务运行中 (端口: {config.PORT})")
    app.run(host='0.0.0.0', port=config.PORT, threaded=True, use_reloader=False)
