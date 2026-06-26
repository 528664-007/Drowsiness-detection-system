"""
Aegis-Wake DrowsinessDetector v4.0

Critical fix: EAR now uses RAW NORMALIZED coordinates (lm.x, lm.y)
instead of pixel coordinates (lm.x*w, lm.y*h).

Why this matters:
  • Frame is 640×480 — non-square aspect ratio
  • Multiplying x by 640 and y by 480 creates DIFFERENT scales per axis
  • Vertical (closing) distances get scaled by 480, horizontal by 640
  • This makes EAR appear ~25% LOWER than real value
  • Head movement changes the effective aspect ratio seen by each eye
  • Result: any head movement triggers false low-EAR → false drowsy alarm

With normalized coords:
  • Both axes are in [0,1] — consistent unit
  • EAR is stable across head positions, distances, and camera resolutions
  • Calibration is more reliable and thresholds are more predictable
"""

import cv2, time
import numpy as np
import mediapipe as mp
from collections import deque


# ── 6-point EAR indices (MediaPipe Face Mesh) ────────────────────────────────
# order: [outer, top1, top2, inner, bot2, bot1]
_L = [33,  159, 158, 133, 153, 145]
_R = [362, 386, 385, 263, 380, 374]

# 3D model for head pose (generic skull, mm)
_FACE_3D = np.array([
    [  0.0,    0.0,    0.0],   # nose tip     lm 1
    [  0.0, -330.0,  -65.0],   # chin         lm 152
    [-225.0,  170.0, -135.0],  # left corner  lm 33
    [ 225.0,  170.0, -135.0],  # right corner lm 263
    [-150.0, -150.0, -125.0],  # left mouth   lm 61
    [ 150.0, -150.0, -125.0],  # right mouth  lm 291
], dtype=np.float64)
_FACE_LM = [1, 152, 33, 263, 61, 291]


def _ear_norm(lm, idx):
    """
    Compute EAR using NORMALIZED coordinates only (no w/h multiply).
    This makes EAR distance- and resolution-invariant.
    """
    pts = np.array([[lm[i].x, lm[i].y] for i in idx], dtype=np.float32)
    v1  = np.linalg.norm(pts[1] - pts[5])
    v2  = np.linalg.norm(pts[2] - pts[4])
    hz  = np.linalg.norm(pts[0] - pts[3])
    return (v1 + v2) / (2.0 * hz + 1e-7)


class DrowsinessDetector:

    def __init__(self, config: dict):
        # ── thresholds & windows ─────────────────────────────────────────────
        self._cal_n       = int(config.get("calibration_frames",       120))
        self._cal_mult    = float(config.get("calibration_multiplier",  0.78))
        self.threshold    = float(config.get("default_threshold",       0.20))
        smooth_w          = int(config.get("ear_smoothing_window",        9))
        self._blink_max   = int(config.get("blink_max_frames",            8))
        self._consec_req  = int(config.get("consecutive_frames_drowsy",  60))
        self._reset_req   = int(config.get("reset_frames",               20))
        self._sleep_sec   = float(config.get("sleeping_seconds",         5.0))
        perclos_win       = float(config.get("perclos_window_seconds",  60.0))
        self._pc_drowsy   = float(config.get("perclos_drowsy_threshold", 0.20))
        self._pc_sleep    = float(config.get("perclos_sleep_threshold",  0.40))
        self._nod_pitch   = float(config.get("nod_pitch_threshold",     20.0))
        self._nod_frames  = int(config.get("nod_consec_frames",          25))
        self._show_mesh   = bool(config.get("show_mesh",                True))
        self._perclos_win = perclos_win

        # ── MediaPipe ────────────────────────────────────────────────────────
        self._fm = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False, max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)
        _du = mp.solutions.drawing_utils
        self._dot  = _du.DrawingSpec(color=(0,180,0), thickness=1, circle_radius=1)
        self._line = _du.DrawingSpec(color=(0, 80,0), thickness=1)

        # ── EAR state ────────────────────────────────────────────────────────
        self._ear_buf     = deque(maxlen=smooth_w)
        self._consec_low  = 0
        self._consec_high = 0
        self._t_closed    = None    # timestamp when eyes first closed
        self._closure_dur = 0.0
        self.current_status = "active"
        self.ear_value    = 0.30

        # ── Calibration ──────────────────────────────────────────────────────
        self._cal_buf  = []
        self._cal_done = False

        # ── PERCLOS ──────────────────────────────────────────────────────────
        self._pc_log  = deque()   # (timestamp, is_closed)
        self.perclos  = 0.0

        # ── Head pose ────────────────────────────────────────────────────────
        self._nod_c    = 0
        self.pitch_deg = 0.0
        self.is_nodding= False

        # ── Session ──────────────────────────────────────────────────────────
        self.total_frames    = 0
        self.drowsy_events   = 0
        self.sleeping_events = 0

    # ══════════════════════════════════════════════════════════════════════════
    def process_frame(self, frame: np.ndarray) -> tuple:
        h, w  = frame.shape[:2]
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res   = self._fm.process(rgb)
        self.total_frames += 1
        now   = time.time()

        out = dict(ear=0.0, status="no_face", closure_duration=0.0,
                   faces_detected=0, threshold=self.threshold,
                   is_calibrated=self._cal_done,
                   cal_progress=len(self._cal_buf), cal_needed=self._cal_n,
                   left_ear=0.0, right_ear=0.0,
                   perclos=0.0, pitch_deg=0.0, is_nodding=False)

        if not res.multi_face_landmarks:
            self._consec_low  = 0
            self._consec_high = 0
            self._t_closed    = None
            self._closure_dur = 0.0
            self.current_status = "no_face"
            self._push_perclos(now, False)
            self._trim_perclos(now)
            return frame, out

        lm = res.multi_face_landmarks[0].landmark
        out["faces_detected"] = 1

        # draw face mesh
        if self._show_mesh:
            mp.solutions.drawing_utils.draw_landmarks(
                frame, res.multi_face_landmarks[0],
                mp.solutions.face_mesh.FACEMESH_TESSELATION,
                self._dot, self._line)

        # ── EAR (normalized coords — no w/h multiply) ────────────────────────
        left_ear  = _ear_norm(lm, _L)
        right_ear = _ear_norm(lm, _R)
        raw       = (left_ear + right_ear) / 2.0
        self._ear_buf.append(raw)
        smooth = float(np.mean(self._ear_buf))
        self.ear_value = smooth

        self._draw_eye_labels(frame, lm, w, h, left_ear, right_ear)

        # ── Calibration ──────────────────────────────────────────────────────
        self._calibrate(smooth)

        # ── Head pose ────────────────────────────────────────────────────────
        self._head_pose(lm, w, h)

        # ── PERCLOS ──────────────────────────────────────────────────────────
        closed = smooth < self.threshold
        self._push_perclos(now, closed)
        self._trim_perclos(now)
        n  = len(self._pc_log)
        nc = sum(1 for _, c in self._pc_log if c)
        self.perclos = nc / max(n, 1)

        # ── State machine ─────────────────────────────────────────────────────
        status = self._state(smooth, now)
        self.current_status = status

        out.update(ear=smooth, status=status,
                   closure_duration=self._closure_dur,
                   left_ear=left_ear, right_ear=right_ear,
                   is_calibrated=self._cal_done,
                   cal_progress=len(self._cal_buf),
                   threshold=self.threshold,
                   perclos=self.perclos,
                   pitch_deg=self.pitch_deg,
                   is_nodding=self.is_nodding)
        return frame, out

    # ══════════════════════════════════════════════════════════════════════════
    def _calibrate(self, smooth: float):
        if self._cal_done:
            return
        # Only collect clearly-open eye readings
        if smooth > 0.22:
            self._cal_buf.append(smooth)
        if len(self._cal_buf) >= self._cal_n:
            baseline      = float(np.mean(self._cal_buf))
            raw_thr       = baseline * self._cal_mult
            # Hard floor: never go below 0.17 to avoid constant false alarms
            self.threshold = max(0.17, raw_thr)
            self._cal_done = True
            print(f"[Detector] Calibration done: "
                  f"baseline={baseline:.4f}  threshold={self.threshold:.4f}")

    def _state(self, smooth: float, now: float) -> str:
        below = smooth < self.threshold

        if below:
            self._consec_high = 0
            self._consec_low += 1

            # ignore blinks
            if self._consec_low <= self._blink_max:
                return "active"

            if self._t_closed is None:
                self._t_closed = now
            self._closure_dur = now - self._t_closed

            if (self._closure_dur >= self._sleep_sec
                    or self.perclos >= self._pc_sleep):
                if self.current_status != "sleeping":
                    self.sleeping_events += 1
                return "sleeping"

            if (self._consec_low >= self._consec_req
                    or self.perclos >= self._pc_drowsy):
                if self.current_status not in ("drowsy", "sleeping"):
                    self.drowsy_events += 1
                return "drowsy"

            return "active"

        else:
            self._consec_low = 0
            self._t_closed   = None
            self._closure_dur = 0.0

            # hysteresis — stay alerted until eyes open long enough
            if self.current_status in ("drowsy", "sleeping"):
                self._consec_high += 1
                if self._consec_high < self._reset_req:
                    return self.current_status
            self._consec_high = 0

            if self.is_nodding:
                return "drowsy"
            return "active"

    def _push_perclos(self, ts, closed):
        self._pc_log.append((ts, closed))

    def _trim_perclos(self, now):
        cutoff = now - self._perclos_win
        while self._pc_log and self._pc_log[0][0] < cutoff:
            self._pc_log.popleft()

    def _head_pose(self, lm, w, h):
        try:
            img_pts = np.array(
                [[lm[i].x * w, lm[i].y * h] for i in _FACE_LM],
                dtype=np.float64)
            f   = w
            cam = np.array([[f,0,w/2],[0,f,h/2],[0,0,1]], np.float64)
            ok, rvec, _ = cv2.solvePnP(
                _FACE_3D, img_pts, cam, np.zeros((4,1)),
                flags=cv2.SOLVEPNP_ITERATIVE)
            if not ok:
                return
            rmat, _ = cv2.Rodrigues(rvec)
            angles, *_ = cv2.RQDecomp3x3(rmat)
            self.pitch_deg = angles[0]
            if self.pitch_deg > self._nod_pitch:
                self._nod_c = min(self._nod_c + 1, self._nod_frames + 10)
            else:
                self._nod_c = max(0, self._nod_c - 2)
            self.is_nodding = self._nod_c >= self._nod_frames
        except Exception:
            pass

    def _draw_eye_labels(self, frame, lm, w, h, le, re):
        lx = max(0, int(lm[_L[0]].x * w) - 38)
        ly = max(12, int(lm[_L[0]].y * h) - 10)
        rx = max(0, int(lm[_R[0]].x * w) - 38)
        ry = max(12, int(lm[_R[0]].y * h) - 10)
        c  = (0, 255, 120)
        cv2.putText(frame, f"L:{le:.3f}", (lx, ly),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, c, 1)
        cv2.putText(frame, f"R:{re:.3f}", (rx, ry),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, c, 1)

    def get_session_stats(self) -> dict:
        return dict(total_frames=self.total_frames,
                    drowsy_events=self.drowsy_events,
                    sleeping_events=self.sleeping_events,
                    final_threshold=self.threshold,
                    final_perclos=self.perclos)
