"""Camera frame overlay — status banner, metrics, EAR bar meter."""
import cv2
import numpy as np

_C = {
    "active":   (  0, 190,   0),
    "drowsy":   (  0, 130, 255),
    "sleeping": ( 20,  20, 220),
    "no_face":  (100, 100, 100),
}
_L = {
    "active":   "  ACTIVE",
    "drowsy":   "  DROWSY — Wake up!",
    "sleeping": "  SLEEPING — ALARM!",
    "no_face":  "  No face detected",
}

class Visualizer:
    def __init__(self, config: dict):
        self.fn    = cv2.FONT_HERSHEY_SIMPLEX
        self.fs    = float(config.get("font_scale", 0.65))
        self.thick = int(config.get("thickness", 2))
        self.show_pc   = bool(config.get("show_perclos",   True))
        self.show_pose = bool(config.get("show_head_pose", True))

    def overlay(self, frame, r: dict, fps: float = 0.0) -> np.ndarray:
        if frame is None:
            return frame
        out = frame.copy()
        h, w = out.shape[:2]

        status = r.get("status",           "active")
        ear    = r.get("ear",               0.0)
        dur    = r.get("closure_duration",  0.0)
        thr    = r.get("threshold",         0.20)
        cal    = r.get("is_calibrated",     False)
        cal_p  = r.get("cal_progress",      0)
        cal_n  = r.get("cal_needed",        120)
        pc     = r.get("perclos",           0.0)
        pitch  = r.get("pitch_deg",         0.0)
        nod    = r.get("is_nodding",        False)
        color  = _C.get(status, (150,150,150))
        label  = _L.get(status, status.upper())

        # ── status banner ────────────────────────────────────────────────────
        banner = np.full((50, w, 3), color, np.uint8)
        out[0:50, :] = cv2.addWeighted(out[0:50,:], 0.40, banner, 0.60, 0)
        cv2.putText(out, label,       (10, 34),    self.fn, self.fs, (255,255,255), self.thick)
        cv2.putText(out, f"EAR {ear:.4f}", (w-165, 22), self.fn, 0.50, (255,255,255), 1)
        cv2.putText(out, f"thr {thr:.4f}", (w-165, 40), self.fn, 0.40, (200,200,200), 1)

        # ── calibration bar ──────────────────────────────────────────────────
        if not cal:
            bw = w - 20
            cv2.rectangle(out, (10,54), (10+bw,66), (35,35,35), -1)
            fw = int(cal_p / max(cal_n,1) * bw)
            cv2.rectangle(out, (10,54), (10+fw,66), (0,190,190), -1)
            pct = int(cal_p / max(cal_n, 1) * 100)
            cv2.putText(out, f"Calibrating… keep eyes open  {pct}%",
                        (14,64), self.fn, 0.34, (255,255,255), 1)

        # ── sleeping border ──────────────────────────────────────────────────
        if status == "sleeping":
            t = 7
            cv2.rectangle(out, (t,t), (w-t,h-t), (0,0,220), t)

        # ── closure duration ─────────────────────────────────────────────────
        if status in ("drowsy","sleeping") and dur > 0:
            cv2.putText(out, f"Eyes closed {dur:.1f}s",
                        (10, h-14), self.fn, 0.52, (255,255,255), 2)

        # ── PERCLOS ──────────────────────────────────────────────────────────
        if self.show_pc and cal:
            pc_c = (0,0,200) if pc>=0.40 else (0,130,255) if pc>=0.20 else (0,165,0)
            cv2.putText(out, f"PERCLOS {pc*100:.0f}%",
                        (10, h-38), self.fn, 0.42, pc_c, 1)

        # ── head nod ─────────────────────────────────────────────────────────
        if self.show_pose and nod:
            cv2.putText(out, f"HEAD NOD {pitch:.0f}°",
                        (w-170, h-14), self.fn, 0.44, (0,100,255), 1)

        # ── FPS ──────────────────────────────────────────────────────────────
        if fps > 0:
            cv2.putText(out, f"{fps:.0f} fps",
                        (w-68, h-38), self.fn, 0.38, (140,140,140), 1)

        # ── EAR bar meter ────────────────────────────────────────────────────
        bw, bh = 160, 14
        bx, by = w-bw-10, h-bh-60
        cv2.rectangle(out, (bx,by), (bx+bw,by+bh), (32,32,32), -1)
        fill = min(int(ear / max(thr*2, 0.38) * bw), bw)
        cv2.rectangle(out, (bx,by), (bx+fill,by+bh), color, -1)
        tx = bx + int(thr / max(thr*2, 0.38) * bw)
        cv2.line(out, (tx,by-3), (tx,by+bh+3), (0,0,200), 2)
        cv2.putText(out, "EAR", (bx-28, by+bh-1), self.fn, 0.30, _C["active"], 1)

        return out
