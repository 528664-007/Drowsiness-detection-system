"""Video capture — single-threaded, called from the main loop."""
import cv2, time


class VideoHandler:

    def __init__(self, config: dict):
        self.device_id = int(config.get("device_id", 0))
        self.width     = int(config.get("width",  640))
        self.height    = int(config.get("height", 480))
        self.fps       = int(config.get("fps",     30))
        self.cap       = None
        self._fc, self._ts = 0, time.time()
        self.current_fps   = 0.0

    def start(self) -> bool:
        # CAP_DSHOW avoids Windows MSMF stall; fall back to any backend
        for backend in (cv2.CAP_DSHOW, cv2.CAP_ANY):
            try:
                cap = cv2.VideoCapture(self.device_id, backend)
                if cap.isOpened():
                    self.cap = cap
                    break
                cap.release()
            except Exception:
                pass

        if not self.cap or not self.cap.isOpened():
            print(f"[Camera] ERROR: Cannot open device {self.device_id}")
            print("[Camera] Try changing device_id in config/config.yaml (0, 1, 2…)")
            return False

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS,          self.fps)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE,   1)   # low latency

        aw = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        ah = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        af = self.cap.get(cv2.CAP_PROP_FPS)
        print(f"[Camera] Opened device {self.device_id}: {aw}x{ah} @ {af:.0f} fps")
        return True

    def read(self):
        if not self.cap or not self.cap.isOpened():
            return None
        ret, frame = self.cap.read()
        if not ret or frame is None:
            return None
        self._fc += 1
        now = time.time()
        if now - self._ts >= 1.0:
            self.current_fps = self._fc / (now - self._ts)
            self._fc, self._ts = 0, now
        return frame

    def stop(self):
        if self.cap:
            self.cap.release()
            self.cap = None
        print("[Camera] Released")
