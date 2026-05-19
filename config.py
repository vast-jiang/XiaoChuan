import os

# --- Hardware Pins ---
SERVO_PIN = 18
MOTOR_PIN = 13
I2C_ADDR_ADS = 0x48

# --- Vision Settings ---
# Force 640x480 for 5MP camera to save 512MB RAM
CAM_W, CAM_H = 640, 480
INPUT_SIZE = 320
AI_SKIP = 6       # Process AI every 6 frames
JPG_QUAL = 50     # Quality/Bandwidth balance

MODEL_PATH = os.path.join(os.path.dirname(__file__), "vision/models/bottle.onnx")
TARGETS = {39: "BOTTLE", 26: "BAG"}

# --- Server ---
PORT = 5000
