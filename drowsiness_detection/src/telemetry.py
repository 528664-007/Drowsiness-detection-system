"""
Pure-OpenCV telemetry panel — no matplotlib, no Tkinter, zero threading.

Layout (stacked):
  ┌─────────────────────────────────┐
  │   EAR time-series  (160 px)     │
  ├─────────────────────────────────┤
  │   PERCLOS bar | Pitch bar (40px)│
  └─────────────────────────────────┘
"""
import cv2
import numpy as np
from collections import deque

_BG    = ( 16,  24,  34)
_GRID  = ( 44,  54,  64)
_CYAN  = (210, 190,   0)
_ORG   = (  0, 140, 255)
_RED   = (  0,   0, 235)
_GRN   = (  0, 180,  60)
_WHITE = (255, 255, 255)
_GRAY  = (130, 130, 130)
_THOLD = ( 60,  60, 210)


class TelemetryPlotter:

    EAR_MAX = 0.55

    def __init__(self, max_pts=240, panel_w=640, ear_h=160, bar_h=40):
        self.max_pts  = max_pts
        self.panel_w  = panel_w
        self.ear_h    = ear_h
        self.bar_h    = bar_h
        self.panel_h  = ear_h + bar_h

        self._ear    = deque(maxlen=max_pts)
        self._status = deque(maxlen=max_pts)
        self._pc     = deque(maxlen=max_pts)
        self._pitch  = deque(maxlen=max_pts)

        self.threshold  = 0.20
        self.nod_thresh = 20.0

        # ── pre-allocated render buffers (avoid np.full every frame) ──────────
        self._ebuf = np.full((ear_h, panel_w, 3), _BG, dtype=np.uint8)
        self._bbuf = np.full((bar_h, panel_w, 3), _BG, dtype=np.uint8)
        self._cbuf = np.empty((ear_h+bar_h, panel_w, 3), dtype=np.uint8)

        # ── static grid drawn once ───────────────────────────────────────────
        self._grid = np.full((ear_h, panel_w, 3), _BG, dtype=np.uint8)
        for pct in (0.25, 0.50, 0.75):
            y = self._ey(pct, ear_h)
            cv2.line(self._grid, (38, y), (panel_w-4, y), _GRID, 1)
            cv2.putText(self._grid, f"{pct:.2f}", (2, y+4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.28, _GRAY, 1)
        cv2.putText(self._grid, "EAR  Time-Series",
                    (panel_w//2-60, 13),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, _WHITE, 1)

    def update(self, ear, status, perclos=0.0, pitch=0.0):
        self._ear.append(ear)
        self._status.append(status)
        self._pc.append(perclos)
        self._pitch.append(pitch)

    def render(self) -> np.ndarray:
        """Returns pre-allocated combined buffer — no heap allocation."""
        self._render_ear()
        self._render_bars()
        self._cbuf[:self.ear_h] = self._ebuf
        self._cbuf[self.ear_h:] = self._bbuf
        return self._cbuf

    # ── EAR graph ─────────────────────────────────────────────────────────────
    def _render_ear(self):
        W, H = self.panel_w, self.ear_h
        img  = self._ebuf
        np.copyto(img, self._grid)          # fast in-place reset to grid

        ty = self._ey(self.threshold, H)
        cv2.line(img, (38, ty), (W-4, ty), _THOLD, 1)
        cv2.putText(img, f"thr={self.threshold:.3f}",
                    (W-82, ty-3), cv2.FONT_HERSHEY_SIMPLEX, 0.28, _THOLD, 1)

        ear_l = list(self._ear)
        sta_l = list(self._status)
        n = len(ear_l)
        if n < 2:
            return

        pw = W - 44
        xs = [int(38 + i * pw / self.max_pts) for i in range(n)]
        for i in range(1, n):
            y0 = self._ey(ear_l[i-1], H)
            y1 = self._ey(ear_l[i],   H)
            st = sta_l[i]
            c  = _RED if st=="sleeping" else _ORG if st=="drowsy" else _CYAN
            cv2.line(img, (xs[i-1], y0), (xs[i], y1), c, 2)

        cv2.putText(img, f"EAR: {ear_l[-1]:.4f}",
                    (42, H-5), cv2.FONT_HERSHEY_SIMPLEX, 0.35, _WHITE, 1)

    def _ey(self, v, H):
        y = int(H - min(v, self.EAR_MAX) / self.EAR_MAX * (H-20) - 5)
        return max(5, min(H-5, y))

    # ── bars ──────────────────────────────────────────────────────────────────
    def _render_bars(self):
        W, H  = self.panel_w, self.bar_h
        img   = self._bbuf
        img[:] = _BG                        # fast in-place reset
        half  = W // 2
        pc    = self._pc[-1]    if self._pc    else 0.0
        pitch = self._pitch[-1] if self._pitch else 0.0
        self._hbar(img, 8,      10, half-16, 14, pc,
                   0.50, 0.20, 0.40, f"PERCLOS {pc*100:.0f}%")
        self._hbar(img, half+8, 10, half-16, 14, max(pitch,0),
                   40.0, self.nod_thresh, 30.0, f"Pitch {pitch:.0f}deg")

    @staticmethod
    def _hbar(img, x, y, bw, bh, v, vmax, warn, danger, lbl):
        cv2.rectangle(img, (x,y), (x+bw, y+bh), (38,38,38), -1)
        fill = min(int(v/vmax*bw), bw)
        r = v/vmax
        c = _RED if r >= danger/vmax else _ORG if r >= warn/vmax else _GRN
        if fill > 0:
            cv2.rectangle(img, (x,y), (x+fill, y+bh), c, -1)
        wx = x + int(warn/vmax*bw)
        cv2.line(img, (wx, y-2), (wx, y+bh+2), _ORG, 1)
        cv2.putText(img, lbl, (x, y+bh+12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.30, _WHITE, 1)

    def stop(self):
        pass
