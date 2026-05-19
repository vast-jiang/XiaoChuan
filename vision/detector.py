import cv2
import threading
import time
import subprocess
import numpy as np
import os

class XiaoChuan_Vision:
    """视觉处理与目标追踪类"""
    def __init__(self, camera_index=0):
        self.current_frame = None
        self.running = True
        self.last_detections = None
        self.ai_lock = threading.Lock()
        self.frame_for_ai = None 
        
        self.target_classes = ['bottle', 'bicycle', 'chair', 'tvmonitor'] 
        self.target_info = {"x": None, "y": None, "area": 0, "width": 480}

        self.classNames = { 0: 'background',
            1: 'aeroplane', 2: 'bicycle', 3: 'bird', 4: 'boat',
            5: 'bottle', 6: 'bus', 7: 'car', 8: 'cat', 9: 'chair',
            10: 'cow', 11: 'diningtable', 12: 'dog', 13: 'horse',
            14: 'motorbike', 15: 'person', 16: 'pottedplant',
            17: 'sheep', 18: 'sofa', 19: 'train', 20: 'tvmonitor' }
        
        model_dir = os.path.join(os.path.dirname(__file__), "models")
        prototxt = os.path.join(model_dir, "MobileNetSSD_deploy.prototxt")
        weights = os.path.join(model_dir, "MobileNetSSD_deploy.caffemodel")
        
        self.use_ai = False
        if os.path.exists(prototxt) and os.path.exists(weights):
            self.net = cv2.dnn.readNetFromCaffe(prototxt, weights)
            self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            self.use_ai = True
            threading.Thread(target=self._ai_worker, daemon=True).start()

        threading.Thread(target=self._update_frame, daemon=True).start()

    def _ai_worker(self):
        """异步推理线程"""
        while self.running:
            if self.use_ai and self.frame_for_ai is not None:
                try:
                    frame = self.frame_for_ai.copy()
                    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
                    self.net.setInput(blob)
                    detections = self.net.forward()
                    with self.ai_lock:
                        self.last_detections = detections
                except Exception:
                    pass
            time.sleep(0.05)

    def _update_frame(self):
        """流媒体捕获与渲染线程"""
        cmd = [
            "rpicam-vid", "-t", "0", "--codec", "mjpeg",
            "--width", "480", "--height", "360",
            "--framerate", "30", "--inline", "--nopreview", "-o", "-"
        ]
        
        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10**8)
            bytes_data = b''
            
            while self.running:
                chunk = self.process.stdout.read(4096)
                if not chunk: break
                bytes_data += chunk
                
                a = bytes_data.find(b'\xff\xd8')
                b = bytes_data.find(b'\xff\xd9')
                
                if a != -1 and b != -1:
                    jpg = bytes_data[a:b+2]
                    bytes_data = bytes_data[b+2:]
                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        self.frame_for_ai = frame
                        
                        if self.use_ai:
                            with self.ai_lock:
                                local_detections = self.last_detections
                                
                            if local_detections is not None:
                                h, w = frame.shape[:2]
                                max_area = 0
                                best_target = None
                                best_label = ""
                                
                                for i in range(local_detections.shape[2]):
                                    confidence = local_detections[0, 0, i, 2]
                                    if confidence > 0.5:
                                        class_id = int(local_detections[0, 0, i, 1])
                                        if class_id in self.classNames:
                                            box = local_detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                                            (startX, startY, endX, endY) = box.astype("int")
                                            name = self.classNames[class_id]
                                            
                                            # 绘制基础检测框
                                            cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 1)
                                            cv2.putText(frame, f"{name} {confidence*100:.0f}%", (startX, startY - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                                            
                                            # 目标特征筛选
                                            if name in self.target_classes:
                                                area = (endX - startX) * (endY - startY)
                                                if area > max_area:
                                                    max_area = area
                                                    best_target = (startX, startY, endX, endY)
                                                    best_label = name

                                if best_target is not None:
                                    (startX, startY, endX, endY) = best_target
                                    center_x = int((startX + endX) / 2)
                                    center_y = int((startY + endY) / 2)
                                    
                                    # 绘制锁定追踪框
                                    cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 0, 255), 2)
                                    cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
                                    
                                    self.target_info = {"x": center_x, "y": center_y, "area": max_area, "width": w}
                                else:
                                    self.target_info = {"x": None, "y": None, "area": 0, "width": w}
                                    
                        self.current_frame = frame
        except Exception as e:
            # 这里的打印会在终端中暴露真实的物理错误
            print(f"\n[致命错误] 视觉推流崩溃原因: {e}\n")

    def get_target_data(self):
        return self.target_info

    def get_jpg(self):
        if self.current_frame is None: return None
        ret, jpeg = cv2.imencode('.jpg', self.current_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
        return jpeg.tobytes() if ret else None

    def stop(self):
        self.running = False
        if hasattr(self, 'process'):
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
