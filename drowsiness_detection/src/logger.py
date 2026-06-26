"""CSV logger — buffered writes, minimal overhead."""
import csv, os, time, threading
from pathlib import Path
from datetime import datetime

class CSVLogger:
    HEADER = ["timestamp","ear","status","closure_dur","perclos","pitch_deg","fps"]

    def __init__(self, config: dict):
        self._path    = config.get("csv_file", "logs/drowsiness_log.csv")
        self._iv      = config.get("log_interval_seconds", 1.0)
        self._lock    = threading.Lock()
        self._buf     = []
        self._last    = 0.0
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        if not os.path.exists(self._path):
            with open(self._path, "w", newline="") as f:
                csv.writer(f).writerow(self.HEADER)

    def log(self, ear, status, dur, perclos=0.0, pitch=0.0, fps=0.0):
        now = time.time()
        if (now - self._last) < self._iv and status not in ("drowsy","sleeping"):
            return
        self._last = now
        row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
               f"{ear:.4f}", status, f"{dur:.2f}",
               f"{perclos:.3f}", f"{pitch:.1f}", f"{fps:.1f}"]
        with self._lock:
            self._buf.append(row)
            if len(self._buf) >= 20:
                self._flush()

    def _flush(self):
        if not self._buf:
            return
        try:
            with open(self._path, "a", newline="") as f:
                csv.writer(f).writerows(self._buf)
            self._buf.clear()
        except Exception as e:
            print(f"[Logger] {e}")

    def flush(self):
        with self._lock:
            self._flush()
