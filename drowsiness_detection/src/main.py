#!/usr/bin/env python3
"""
Aegis-Wake v4.0 — single-threaded main loop (Windows/Linux/Mac safe).

Every step runs on the main thread:
  grab → detect → alarm → log → overlay → panel → show → repeat

The alarm audio runs in its own daemon thread (pygame Channel only).
No Tkinter, no matplotlib, no other GUI threads.
"""
import sys, cv2, time, signal
import numpy as np
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).parent))

from video_handler       import VideoHandler
from drowsiness_detector import DrowsinessDetector
from logger              import CSVLogger
from visualizer          import Visualizer
from alarm               import AudioAlarm
from telemetry           import TelemetryPlotter


def _load(path="config/config.yaml"):
    try:
        cfg = yaml.safe_load(open(path)) or {}
        print(f"[Config] Loaded {path}")
        return cfg
    except FileNotFoundError:
        print(f"[Config] {path} not found — using defaults")
        return {}


def _defaults():
    return dict(
        camera       = dict(device_id=0, width=640, height=480, fps=30),
        detection    = dict(
            calibration_frames=120, calibration_multiplier=0.78,
            default_threshold=0.20, ear_smoothing_window=9,
            blink_max_frames=8, consecutive_frames_drowsy=60,
            reset_frames=20, sleeping_seconds=5.0,
            perclos_window_seconds=60,
            perclos_drowsy_threshold=0.20, perclos_sleep_threshold=0.40,
            nod_pitch_threshold=20.0, nod_consec_frames=25,
            show_mesh=True),
        alarm        = dict(sound_file="assets/alarm.wav", volume=0.9,
                            repeat_interval=2.0),
        logging      = dict(csv_file="logs/drowsiness_log.csv",
                            log_interval_seconds=1.0),
        visualization= dict(font_scale=0.65, thickness=2,
                            show_perclos=True, show_head_pose=True),
    )


def _merge(base, over):
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _merge(base[k], v)
        else:
            base[k] = v
    return base


def main():
    cfg = _merge(_defaults(), _load())

    video    = VideoHandler(cfg["camera"])
    detector = DrowsinessDetector(cfg["detection"])
    logger   = CSVLogger(cfg["logging"])
    alarm    = AudioAlarm(cfg["alarm"])
    viz      = Visualizer(cfg["visualization"])
    telem    = TelemetryPlotter(panel_w=cfg["camera"].get("width", 640))
    telem.nod_thresh = cfg["detection"].get("nod_pitch_threshold", 20.0)

    if not video.start():
        print("[Main] Fatal: camera could not be opened — exiting")
        return 1

    cw = cfg["camera"].get("width",  640)
    ch = cfg["camera"].get("height", 480)

    WIN = "Aegis-Wake v5.0 — Drowsiness Detection  (Q / ESC to quit)"
    cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WIN, cw, ch + telem.panel_h)

    # pre-allocate combined display buffer (avoid vconcat allocation each frame)
    combined = np.empty((ch + telem.panel_h, cw, 3), dtype=np.uint8)

    _stop = [False]
    def _sig(s, f): _stop[0] = True
    signal.signal(signal.SIGINT,  _sig)
    signal.signal(signal.SIGTERM, _sig)

    print("=" * 58)
    print("  Aegis-Wake v5.0  —  Running")
    print("  Keep eyes open for ~4s to calibrate…")
    print("  Press Q or ESC to quit")
    print("=" * 58)

    t_fps, c_fps, live_fps = time.perf_counter(), 0, 0.0

    while not _stop[0]:
        # 1. grab
        frame = video.read()
        if frame is None:
            time.sleep(0.02)
            continue

        # 2. detect
        frame, result = detector.process_frame(frame)
        status  = result.get("status",           "active")
        ear     = result.get("ear",               0.0)
        dur     = result.get("closure_duration",  0.0)
        perclos = result.get("perclos",            0.0)
        pitch   = result.get("pitch_deg",          0.0)
        telem.threshold = result.get("threshold", telem.threshold)

        # 3. alarm — called on main thread, zero threading, zero lag
        alarm.update(status in ("drowsy", "sleeping"))

        # 4. log
        logger.log(ear, status, dur, perclos, pitch, live_fps)

        # 5. telemetry data
        telem.update(ear, status, perclos, pitch)

        # 6. render into pre-allocated buffer (no heap allocation)
        display = viz.overlay(frame, result, fps=live_fps)
        panel   = telem.render()
        combined[:ch]  = display
        combined[ch:]  = panel
        cv2.imshow(WIN, combined)

        # 7. FPS
        c_fps += 1
        now = time.perf_counter()
        if now - t_fps >= 1.0:
            live_fps = c_fps / (now - t_fps)
            c_fps, t_fps = 0, now

        # 8. keys
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), ord("Q"), 27):
            break

    # shutdown
    print("\nShutting down…")
    alarm.shutdown()
    video.stop()
    logger.flush()
    cv2.destroyAllWindows()

    s = detector.get_session_stats()
    print(f"  Frames processed : {s['total_frames']}")
    print(f"  Drowsy events    : {s['drowsy_events']}")
    print(f"  Sleeping events  : {s['sleeping_events']}")
    print(f"  Final threshold  : {s['final_threshold']:.4f}")
    print(f"  Final PERCLOS    : {s['final_perclos']*100:.1f}%")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
