import time
import logging
import threading
from typing import Optional, Callable, Dict, Any, List
from enum import Enum

import numpy as np

logger = logging.getLogger("SmartBIM.Drone")


class DroneStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ARMED = "armed"
    FLYING = "flying"
    ERROR = "error"


class DroneHandler:
    """معالج الطائرة المسيرة — اتصال MAVLink + بث فيديو OpenCV
    يدعم الاتصال المباشر بالطائرة أو تحميل بيانات من ملفات"""

    def __init__(self):
        self.status = DroneStatus.DISCONNECTED
        self.connection = None
        self.video_capture = None
        self.is_streaming = False
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._stream_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._frame_callbacks: List[Callable] = []
        self._status_callbacks: List[Callable] = []
        self._telemetry: Dict[str, Any] = {
            "battery": 0,
            "altitude": 0.0,
            "speed": 0.0,
            "gps_lat": 0.0,
            "gps_lon": 0.0,
            "heading": 0,
            "satellites": 0,
            "signal_strength": 0,
        }
        self._frame_count = 0
        self._fps = 0.0

    def get_status(self) -> Dict[str, Any]:
        """الحصول على حالة الطائرة الحالية"""
        return {
            "status": self.status.value,
            "is_streaming": self.is_streaming,
            "telemetry": dict(self._telemetry),
            "frame_count": self._frame_count,
            "fps": self._fps,
        }

    def connect(self, connection_string: str = "udp:127.0.0.1:14550",
                baud: int = 57600) -> bool:
        """الاتصال بالطائرة عبر MAVLink"""
        self.status = DroneStatus.CONNECTING
        self._notify_status()
        try:
            from pymavlink import mavutil
            self.connection = mavutil.mavlink_connection(
                connection_string, baud=baud
            )
            self.connection.wait_heartbeat(timeout=10)
            self.status = DroneStatus.CONNECTED
            self._stop_event.clear()
            self._heartbeat_thread = threading.Thread(
                target=self._heartbeat_loop, daemon=True
            )
            self._heartbeat_thread.start()
            self._notify_status()
            logger.info(f"Drone connected: {connection_string}")
            return True
        except Exception as e:
            self.status = DroneStatus.ERROR
            self._notify_status()
            logger.error(f"Drone connection failed: {e}")
            return False

    def disconnect(self):
        """قطع الاتصال بالطائرة"""
        self._stop_event.set()
        self.stop_video_stream()
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            self.connection = None
        self.status = DroneStatus.DISCONNECTED
        self._notify_status()
        logger.info("Drone disconnected")

    def start_video_stream(self, source: Any = 0) -> bool:
        """بدء بث الفيديو — من كاميرا الطائرة أو ملف"""
        try:
            import cv2
            if isinstance(source, str) and source.startswith("rtsp"):
                self.video_capture = cv2.VideoCapture(source)
            elif isinstance(source, str):
                self.video_capture = cv2.VideoCapture(source)
            else:
                self.video_capture = cv2.VideoCapture(int(source))

            if not self.video_capture.isOpened():
                logger.error("Failed to open video source")
                return False

            self.is_streaming = True
            self._stop_event.clear()
            self._stream_thread = threading.Thread(
                target=self._stream_loop, daemon=True
            )
            self._stream_thread.start()
            logger.info(f"Video stream started: {source}")
            return True
        except Exception as e:
            logger.error(f"Video stream failed: {e}")
            return False

    def stop_video_stream(self):
        """إيقاف بث الفيديو"""
        self.is_streaming = False
        if self.video_capture:
            try:
                self.video_capture.release()
            except Exception:
                pass
            self.video_capture = None
        logger.info("Video stream stopped")

    def capture_frame(self) -> Optional[np.ndarray]:
        """التقاط إطار واحد"""
        if self.video_capture and self.video_capture.isOpened():
            ret, frame = self.video_capture.read()
            if ret:
                return frame
        return None

    def load_images_from_folder(self, folder_path: str) -> List[np.ndarray]:
        """تحميل صور من مجلد للمعالجة"""
        import cv2
        import os
        images = []
        supported = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
        if not os.path.isdir(folder_path):
            logger.error(f"Folder not found: {folder_path}")
            return images
        files = sorted(os.listdir(folder_path))
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in supported:
                path = os.path.join(folder_path, fname)
                img = cv2.imread(path)
                if img is not None:
                    images.append(img)
        logger.info(f"Loaded {len(images)} images from {folder_path}")
        return images

    def extract_features(self, image: np.ndarray,
                         method: str = "ORB") -> Dict[str, Any]:
        """استخراج الميزات من الصورة — DSBA Stage 1"""
        import cv2
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        if method.upper() == "SIFT":
            detector = cv2.SIFT_create(nfeatures=2000)
        else:
            detector = cv2.ORB_create(nOctaveLayers=4, nfeatures=2000)

        keypoints, descriptors = detector.detectAndCompute(gray, None)
        points = np.array([kp.pt for kp in keypoints]) if keypoints else np.array([])
        sizes = np.array([kp.size for kp in keypoints]) if keypoints else np.array([])

        return {
            "keypoints_count": len(keypoints) if keypoints else 0,
            "points": points,
            "sizes": sizes,
            "descriptors": descriptors,
            "image_shape": image.shape,
        }

    def match_features(self, desc1: np.ndarray, desc2: np.ndarray,
                       method: str = "ORB") -> List[Any]:
        """مطابقة الميزات بين صورتين"""
        import cv2
        if desc1 is None or desc2 is None:
            return []

        if method.upper() == "SIFT":
            bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
            raw_matches = bf.knnMatch(desc1, desc2, k=2)
            good = []
            for m_pair in raw_matches:
                if len(m_pair) == 2:
                    m, n = m_pair
                    if m.distance < 0.75 * n.distance:
                        good.append(m)
            return good
        else:
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(desc1, desc2)
            matches = sorted(matches, key=lambda x: x.distance)
            return matches[:200]

    def generate_point_cloud_from_images(self, images: List[np.ndarray],
                                         progress_callback: Optional[Callable] = None
                                         ) -> Optional[np.ndarray]:
        """توليد سحابة نقاط من مجموعة صور — DSBA Stage 1
        يستخدم Structure from Motion مبسط"""
        import cv2

        if len(images) < 2:
            logger.error("Need at least 2 images for SfM")
            return None

        all_3d_points = []
        total_pairs = len(images) - 1

        for i in range(total_pairs):
            if progress_callback:
                progress_callback(int((i / total_pairs) * 100))

            feat1 = self.extract_features(images[i])
            feat2 = self.extract_features(images[i + 1])

            matches = self.match_features(feat1["descriptors"], feat2["descriptors"])
            if len(matches) < 8:
                continue

            pts1 = np.float64([feat1["points"][m.queryIdx] for m in matches])
            pts2 = np.float64([feat2["points"][m.trainIdx] for m in matches])

            h, w = images[i].shape[:2]
            focal = max(h, w) * 1.2
            cx, cy = w / 2.0, h / 2.0
            K = np.array([[focal, 0, cx], [0, focal, cy], [0, 0, 1]])

            E, mask = cv2.findEssentialMat(pts1, pts2, K, method=cv2.RANSAC,
                                           prob=0.999, threshold=1.0)
            if E is None:
                continue

            _, R, t, mask_pose = cv2.recoverPose(E, pts1, pts2, K)

            P1 = K @ np.hstack([np.eye(3), np.zeros((3, 1))])
            P2 = K @ np.hstack([R, t])

            points_4d = cv2.triangulatePoints(P1, P2, pts1.T, pts2.T)
            points_3d = points_4d[:3] / points_4d[3]
            points_3d = points_3d.T

            valid = np.all(np.isfinite(points_3d), axis=1)
            points_3d = points_3d[valid]

            if len(points_3d) > 0:
                dists = np.linalg.norm(points_3d, axis=1)
                median_dist = np.median(dists)
                keep = dists < median_dist * 5
                all_3d_points.append(points_3d[keep])

        if progress_callback:
            progress_callback(100)

        if not all_3d_points:
            logger.warning("No 3D points generated")
            return None

        combined = np.vstack(all_3d_points)
        logger.info(f"Generated point cloud with {len(combined)} points")
        return combined

    def save_point_cloud(self, points: np.ndarray, filepath: str):
        """حفظ سحابة النقاط بصيغة PLY"""
        with open(filepath, "w") as f:
            f.write("ply\n")
            f.write("format ascii 1.0\n")
            f.write(f"element vertex {len(points)}\n")
            f.write("property float x\n")
            f.write("property float y\n")
            f.write("property float z\n")
            f.write("end_header\n")
            for pt in points:
                f.write(f"{pt[0]:.6f} {pt[1]:.6f} {pt[2]:.6f}\n")
        logger.info(f"Point cloud saved: {filepath}")

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """معالجة إطار فيديو"""
        import cv2
        processed = cv2.GaussianBlur(frame, (3, 3), 0)
        return processed

    def on_frame(self, callback: Callable):
        self._frame_callbacks.append(callback)

    def on_status_change(self, callback: Callable):
        self._status_callbacks.append(callback)

    def _notify_status(self):
        for cb in self._status_callbacks:
            try:
                cb(self.status)
            except Exception:
                pass

    def _heartbeat_loop(self):
        while not self._stop_event.is_set():
            try:
                if self.connection:
                    msg = self.connection.recv_match(
                        type=["HEARTBEAT", "SYS_STATUS", "GPS_RAW_INT",
                              "GLOBAL_POSITION_INT", "VFR_HUD"],
                        blocking=True, timeout=2
                    )
                    if msg:
                        self._process_telemetry(msg)
            except Exception:
                pass
            time.sleep(0.5)

    def _process_telemetry(self, msg):
        msg_type = msg.get_type()
        if msg_type == "SYS_STATUS":
            self._telemetry["battery"] = getattr(msg, "battery_remaining", 0)
        elif msg_type == "GLOBAL_POSITION_INT":
            self._telemetry["altitude"] = getattr(msg, "relative_alt", 0) / 1000.0
            self._telemetry["gps_lat"] = getattr(msg, "lat", 0) / 1e7
            self._telemetry["gps_lon"] = getattr(msg, "lon", 0) / 1e7
            self._telemetry["heading"] = getattr(msg, "hdg", 0) / 100
        elif msg_type == "VFR_HUD":
            self._telemetry["speed"] = getattr(msg, "groundspeed", 0)
            self._telemetry["altitude"] = getattr(msg, "alt", 0)
        elif msg_type == "GPS_RAW_INT":
            self._telemetry["satellites"] = getattr(msg, "satellites_visible", 0)

    def _stream_loop(self):
        last_time = time.time()
        frame_times = []

        while self.is_streaming and not self._stop_event.is_set():
            frame = self.capture_frame()
            if frame is not None:
                processed = self.process_frame(frame)
                self._frame_count += 1

                now = time.time()
                frame_times.append(now)
                frame_times = [t for t in frame_times if now - t < 1.0]
                self._fps = len(frame_times)

                for cb in self._frame_callbacks:
                    try:
                        cb(processed)
                    except Exception:
                        pass
            else:
                time.sleep(0.01)
