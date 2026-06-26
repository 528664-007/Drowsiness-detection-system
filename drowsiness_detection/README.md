# Aegis-Wake v4.0 — Real-Time Driver Drowsiness Detection

## Quick Start
```bash
pip install -r requirements.txt
python assets/gen_beep.py   # generate alarm.wav (run once)
python run.py
```
Press **Q** or **ESC** to quit.

## Bugs fixed in v4.0
| Bug | Root Cause | Fix |
|---|---|---|
| False drowsy on movement | EAR used pixel coords with non-square aspect ratio (640×480) | EAR now uses raw normalized coords (lm.x, lm.y) — distance & resolution invariant |
| False drowsy instantly | consecutive_frames=20 = 0.67s, no blink filter | 60 frames (2s) + blink filter (8 frames) + hysteresis (20 frames) |
| Alarm not triggering | Threading lock deadlock in _play() loop | Dedicated pygame Channel + threading.Event worker, play(loops=-1 or repeat) |

## New features in v4.0
- **PERCLOS** — % eye closure over 60-second window (independent drowsy trigger)
- **Head-nod detection** — solvePnP pitch > 20° triggers drowsy
- **Calibration progress bar** — visible on screen during warmup
- **gen_beep.py** — generates two-tone alarm.wav automatically
- **Session stats** — printed on exit

## Tuning
Edit `config/config.yaml`:
- `consecutive_frames_drowsy` — higher = less sensitive (default 60 = 2s)
- `sleeping_seconds` — how long eyes must be closed to trigger SLEEPING (default 5s)
- `calibration_multiplier` — higher = looser threshold (try 0.80 if still too sensitive)
