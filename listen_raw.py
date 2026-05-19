import serial
import time

print("===================================")
print("[SYS] Serial Monitor Service Started")
print("===================================")

try:
    ser = serial.Serial('/dev/serial0', 115200, timeout=1)
    print("[INFO] /dev/serial0 opened successfully.")
    
    empty_count = 0
    while True:
        if ser.in_waiting > 0:
            raw_data = ser.read(ser.in_waiting)
            print(f"[RECV] -> {raw_data.hex()}")
            empty_count = 0
        else:
            empty_count += 1
            if empty_count > 10:
                print("Waiting for signal...", end="\r")
        time.sleep(0.1)

except Exception as e:
    print(f"\n[ERROR] Failed to open serial port: {e}")