# 🚢 XiaoChuan (小船) - AI-Assisted Unmanned Surface Vehicle

![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9+-green.svg)
![Hardware](https://img.shields.io/badge/Hardware-Raspberry%20Pi%20Zero%202W-red.svg)

**XiaoChuan (小船)** 是一款基于微型边缘计算节点驱动的多功能遥控无人水面舰艇（USV）。它集成了机器视觉、多源传感器融合与差速混控算法，能够在水面上执行环境监测、水面清理以及高精度投饵等任务。

## ✨ 核心功能 (Core Features)

* 🧠 **AI 辅助驾驶与目标追踪**：搭载 MobileNetSSD 轻量级视觉模型，支持水面特定目标（如塑料瓶垃圾等）的识别与锁定，并结合 **PID 闭环控制算法**实现自动追踪与差速转向。
* 🗑️ **水面垃圾清理**：配合 AI 视觉系统与推力矢量控制，能够精准接近并收集水面漂浮物。
* 🐟 **全自动投饵系统**：支持通过遥控器（SwD 通道）或 Web 控制台一键触发异步投饵舵机，进行精准定点打窝。
* 💧 **实时水质与环境遥测**：
    * **水质浊度检测**：通过 ADS1115 高精度 ADC 实时采集水体浑浊度。
    * **超声波避障测距**：内置复合滤波算法（去极值平均 + 一阶低通），提供稳定抗干扰的距离数据。
* 🎮 **双端权限仲裁控制**：支持 FlySky i-BUS 物理遥控器与基于 Flask 的 Web 虚拟摇杆无缝切换，物理遥控器具有最高仲裁优先级。

## 🛠️ 硬件架构 (Hardware Architecture)

* **核心主控**：Raspberry Pi Zero 2W (512MB RAM)
* **视觉感知**：OV5647 5MP 摄像头 (CSI 接口，MJPEG 硬件级异步推流)
* **动力总线**：双涵道无刷电机 + 差速混控 (I2C PCA9685 控制)
* **战术通信**：FlySky 接收机 (基于 `/dev/serial0` 的 i-BUS 协议底层解析)
* **传感矩阵**：水质浊度传感器、HC-SR04 超声波模块

## 💻 软件栈与核心算法 (Software Stack & Algorithms)

* **Web 引擎**：基于 Flask 构建异步非阻塞 API 网关，提供纯 HTML/JS 的轻量级移动端自适应控制台。
* **机器视觉**：OpenCV DNN 模块，后台独立线程推理，确保主控循环零延迟。
* **控制工程**：
    * 带有积分抗饱和与死区补偿的 PID 转向追踪算法。
    * 针对双发电机机械差异的软件级 Trim 动态配平算法。
    * 基于 `systemd` 的后台高可用守护进程。

## 🚀 快速启动 (Quick Start)

### 1. 环境准备
确保树莓派 Zero 2W 已安装最新的 Raspberry Pi OS，并已在 `raspi-config` 中开启 I2C、Serial 和 Camera 接口。

```bash
# 克隆仓库
git clone [https://github.com/vast-jiang/XiaoChuan.git](https://github.com/vast-jiang/XiaoChuan.git)
cd XiaoChuan

# 挂载隔离的虚拟环境并安装依赖
python -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
