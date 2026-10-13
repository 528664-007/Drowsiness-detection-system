<div align="center">

# 🚗 Real-Time Driver Drowsiness Detection System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8.1-green.svg)](https://opencv.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.7-red.svg)](https://mediapipe.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Made with Love](https://img.shields.io/badge/Made%20with-%E2%9D%A4%EF%B8%8F-red.svg)](https://github.com/528664-007)

**A real-time computer vision system for detecting driver drowsiness and helping prevent accidents**

[Features](#-features) • [Demo](#-demo) • [Installation](#-installation) • [Usage](#-usage-guide) • [Architecture](#-system-architecture) • [Contributing](#-contributing)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Demo](#-demo)
- [System Architecture](#-system-architecture)
- [Technology Stack](#-technology-stack)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage Guide](#-usage-guide)
- [How It Works](#-how-it-works)
- [Performance Metrics](#-performance-metrics)
- [Project Structure](#-project-structure)
- [API Documentation](#-api-documentation)
- [Troubleshooting](#-troubleshooting)
- [Outputs](#-outputs)
- [Contributing](#-contributing)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)
- [Contact & Support](#-contact--support)

---

## 🎯 Overview

Driver drowsiness is a leading cause of road accidents worldwide. This system provides a **real-time, non-intrusive solution** that monitors the driver's eye movements using a standard webcam and detects signs of drowsiness before they lead to dangerous situations.

The system employs **computer vision** techniques to:
- Track facial landmarks in real time
- Calculate the Eye Aspect Ratio (EAR)
- Detect micro-sleep events
- Trigger immediate audio alerts
- Log data for post-journey analysis

### 🚨 The Problem
Drowsy driving is a major, well-documented cause of road crashes. Fatigue slows reaction time and can cause micro-sleeps that last long enough to leave the lane. Check current figures from your national road-safety authority (for example NHTSA in the US) before quoting statistics.

### 💡 Our Solution
- **Real-time monitoring** at 30 FPS on typical laptop hardware
- **Non-intrusive**: uses a standard webcam
- **Immediate alerts** before a micro-sleep becomes dangerous
- **Data logging** useful for fleet management and safety analysis

---

## ✨ Features

### Core Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Real-time Face Detection** | Detects the driver's face using MediaPipe Face Mesh | ✅ |
| **Eye Aspect Ratio (EAR)** | Precise eye-openness measurement | ✅ |
| **Drowsiness Detection** | Identifies drowsy states with configurable sensitivity | ✅ |
| **Sleep Detection** | Detects extended eye closure | ✅ |
| **Audio Alarm** | Instant audible alerts when drowsy or sleeping | ✅ |
| **Live Telemetry** | Real-time EAR graph with threshold line | ✅ |
| **CSV Logging** | Data logging for analysis | ✅ |
| **Automatic Calibration** | Adapts to individual eye characteristics | ✅ |
| **Multi-threaded Architecture** | Smooth 30 FPS performance | ✅ |
| **Visual Overlays** | Color-coded status and EAR meter | ✅ |

### Planned / Optional Features

- **GPU acceleration** (requires an OpenCV build with CUDA support)
- **Adaptive threshold** for changing lighting conditions
- **Sleep-stage classification** (mild / moderate / severe)
- **Fleet management REST API** (Flask)
- **Mobile / USB camera support**

---

## 🎬 Demo

### Sample Output

<div align="center">

| Active State | Drowsy State | Sleeping State |
|--------------|--------------|----------------|
| 🟢 Green overlay | 🟠 Orange overlay | 🔴 Red overlay |
| EAR: 0.283 | EAR: 0.152 | EAR: 0.098 |
| Status: Active | Status: Drowsy | Status: Sleeping |

</div>

See the [Outputs](#-outputs) section for real screenshots.

### Telemetry Dashboard

The system provides a real-time telemetry window showing:
- Live EAR values over time
- A threshold line for visual reference
- Color-coded status indicators
- A statistical summary

---

## 🧱 System Architecture

```text
┌─────────────────────────────────────────────────────────────────────┐
│                         APPLICATION LAYER                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │
│  │    Video     │    │  Drowsiness  │    │    Logger    │           │
│  │   Handler    │───▶│   Detector   │───▶│    (CSV)     │           │
│  │  (Capture)   │    │  (Analysis)  │    │  (Storage)   │           │
│  └──────────────┘    └──────────────┘    └──────────────┘           │
│         │                   │                   │                   │
│         ▼                   ▼                   ▼                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │
│  │  Visualizer  │    │    Alarm     │    │  Telemetry   │           │
│  │  (Overlay)   │    │   (Audio)    │    │   (Graph)    │           │
│  └──────────────┘    └──────────────┘    └──────────────┘           │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                       MULTI-THREADING LAYER                         │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │
│  │   Capture    │    │  Processing  │    │   Display    │           │
│  │   Thread     │───▶│    Queue     │───▶│   Thread     │           │
│  │   (30 FPS)   │    │  (Analysis)  │    │    (UI)      │           │
│  └──────────────┘    └──────────────┘    └──────────────┘           │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                          HARDWARE LAYER                             │
├─────────────────────────────────────────────────────────────────────┤
│                      Webcam / Audio Output                          │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```text
Camera → Capture Thread → Queue → Processing Thread → Detection → Results
                                                                     │
                                          ┌──────────────────────────┘
                                          ▼
                                   ┌──────────────┐
                                   │   Display    │
                                   │   (OpenCV)   │
                                   └──────────────┘
                                          │
                                          ├─── Audio Alert
                                          ├─── CSV Logging
                                          └─── Telemetry Graph
```

---

## 🧰 Technology Stack

### Core Technologies

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Language** | Python | 3.10+ | Core development |
| **Computer Vision** | OpenCV | 4.8.1 | Image processing |
| **Face Detection** | MediaPipe | 0.10.7 | Facial landmark detection |
| **Numerical Computing** | NumPy | 1.24.3 | Mathematical operations |
| **Data Visualization** | Matplotlib | 3.7.2 | Telemetry plotting |
| **Audio** | PyGame | 2.5.2 | Alarm playback |
| **Configuration** | PyYAML | 6.0.1 | Configuration management |

### Optional Tools

| Tool | Purpose |
|------|---------|
| **CUDA** | GPU acceleration |
| **TensorRT** | Model optimization |
| **Docker** | Containerization |
| **Flask** | REST API |

### Development Tools

- **VS Code** / PyCharm: IDE
- **Git**: version control
- **Pytest**: testing
- **Black**: code formatting
- **Flake8**: linting

---

## 📦 Installation

### Prerequisites

- **Python 3.10 or higher**
- **Webcam** (built-in or external)
- **Audio output** device
- **Minimum 4 GB RAM** (8 GB recommended)
- **2 GB free disk space**

### Quick Install

#### 1. Clone the Repository

```bash
git clone https://github.com/528664-007/drowsiness-detection.git
cd drowsiness-detection
```

#### 2. Create a Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> **GPU note:** the standard `opencv-python` wheel is CPU-only. GPU acceleration needs an OpenCV build compiled with CUDA, and is optional.

#### 4. Set Up the Alarm Sound

Either download a free alarm sound (for example from [Zapsplat](https://www.zapsplat.com/sound-effect-category/alarms/)) and save it as `assets/alarm.wav`, or generate a simple beep with this script (save as `generate_alarm.py`):

```python
import math
import os
import struct
import wave

os.makedirs("assets", exist_ok=True)
with wave.open("assets/alarm.wav", "w") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(44100)
    for i in range(44100):
        sample = int(32767 * 0.5 * math.sin(2 * math.pi * 880 * i / 44100))
        wf.writeframes(struct.pack("<h", sample))
print("Created assets/alarm.wav")
```

```bash
python generate_alarm.py
```

#### 5. Verify the Installation

```bash
# Test camera
python -c "import cv2; cap=cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera failed')"

# Test audio
python -c "import pygame; pygame.mixer.init(); print('Audio OK')"

# Run the system
python drowsiness_system.py
```

### Docker Installation (Alternative)

Create a `Dockerfile` in the project root:

```dockerfile
FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["python", "drowsiness_system.py"]
```

Build and run (Linux host with a webcam and X11):

```bash
docker build -t drowsiness-detection .

docker run -it --rm \
    --device=/dev/video0:/dev/video0 \
    --device=/dev/snd:/dev/snd \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    drowsiness-detection
```

---

## 📝 Configuration

### Configuration File (`config.yaml`)

```yaml
# ============================================================
# REAL-TIME DRIVER DROWSINESS DETECTION SYSTEM
# Configuration File
# ============================================================

# Camera Configuration
camera:
  device_id: 0              # 0 for default webcam
  width: 640                # Capture width (pixels)
  height: 480               # Capture height (pixels)
  fps: 30                   # Target frames per second
  buffer_size: 10           # Frame buffer size

# Detection Parameters
detection:
  # Eye Aspect Ratio (EAR) threshold
  # Higher = more sensitive to drowsiness (alarms sooner)
  # Range: 0.15 - 0.35 (typically)
  eye_aspect_ratio_threshold: 0.25

  # Frames needed to trigger drowsy state
  # At 30 FPS: 20 frames is about 0.67 seconds
  consecutive_frames_drowsy: 20

  # Seconds of eye closure to trigger sleep state
  sleeping_seconds: 3.0

  # Smoothing window for EAR values
  # Higher = smoother but slower response
  ear_smoothing_window: 5

  # Calibration frames for threshold adjustment
  calibration_frames: 30

# Audio Alarm Configuration
alarm:
  sound_file: "assets/alarm.wav"   # Path to WAV file
  volume: 0.7                      # Volume (0.0 - 1.0)
  loop: true                       # Loop alarm while drowsy
  cooldown_seconds: 1.0            # Prevent rapid triggering

# Logging Configuration
logging:
  csv_file: "logs/drowsiness_log.csv"
  log_interval_seconds: 1.0
  max_log_size_mb: 100
  backup_count: 5

  # Fields to log
  fields:
    - timestamp
    - ear_value
    - status
    - closure_duration
    - fps
    - face_position
    - confidence_score

# Visualization Configuration
visualization:
  # Status colors (BGR format)
  status_colors:
    active: [0, 255, 0]       # Green
    drowsy: [0, 165, 255]     # Orange
    sleeping: [0, 0, 255]     # Red
    no_face: [255, 255, 255]  # White

  font_scale: 0.7
  thickness: 2
  show_landmarks: true
  show_ear_meter: true
  show_fps: true

# Telemetry Configuration
telemetry:
  max_points: 200            # Points to display
  update_interval_ms: 100    # Update frequency
  window_title: "EAR Telemetry"
  show_stats: true

# API Configuration (Optional)
api:
  enabled: false
  host: "0.0.0.0"
  port: 5000
  cors_origins: ["*"]

# Performance Tuning
performance:
  use_gpu: false             # Experimental, needs a CUDA build of OpenCV
  num_threads: 4             # Processing threads
  priority: "high"           # Thread priority
  cache_frames: true         # Cache frames for processing
```

### Environment Variables

Create a `.env` file for local overrides:

```bash
# .env file
CAMERA_DEVICE=0
EAR_THRESHOLD=0.25
ALARM_VOLUME=0.7
LOG_LEVEL=INFO
TELEMETRY_ENABLED=true
```

---

## 🚀 Usage Guide

### Basic Usage

```bash
# Run with default configuration
python drowsiness_system.py

# Run with custom configuration
python drowsiness_system.py --config custom_config.yaml

# Run with GUI disabled (headless)
python drowsiness_system.py --no-gui

# Run with debug logging
python drowsiness_system.py --debug

# Run with a specific camera
python drowsiness_system.py --camera 1
```

### Command Line Arguments

```bash
python drowsiness_system.py --help
```

```text
usage: drowsiness_system.py [-h] [--config CONFIG] [--camera CAMERA]
                            [--no-gui] [--debug] [--telemetry]
                            [--log-level {DEBUG,INFO,WARNING,ERROR}]

Optional arguments:
  -h, --help            Show this help message
  --config CONFIG       Path to configuration file
  --camera CAMERA       Camera device ID (default: 0)
  --no-gui              Run without GUI (headless mode)
  --debug               Enable debug logging
  --telemetry           Enable telemetry plotting
  --log-level {DEBUG,INFO,WARNING,ERROR}
                        Set logging level
```

### GUI Controls

| Key | Action |
|-----|--------|
| `q` or `ESC` | Quit application |
| `f` | Toggle fullscreen |
| `s` | Save current frame |
| `r` | Reset calibration |
| `m` | Toggle mute alarm |
| `Space` | Pause / resume detection |

### Telemetry Graph Controls

| Action | Effect |
|--------|--------|
| Mouse wheel | Zoom in / out |
| Click & drag | Pan left / right |
| Right-click | Reset view |
| `h` | Toggle legend |
| `g` | Toggle grid |

---

## 🔬 How It Works

### 1. Face Detection & Landmark Extraction

The system uses **MediaPipe Face Mesh** to detect 468 facial landmarks in real time:

```python
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)
```

### 2. Eye Aspect Ratio (EAR) Calculation

EAR compares the vertical distances between the eyelids with the horizontal width of the eye, using six landmarks per eye:

```text
        p2     p3
   p1 ──┴──────┴── p4
        p6     p5

EAR = ( ||p2 - p6|| + ||p3 - p5|| ) / ( 2 * ||p1 - p4|| )
```

Where:
- `p1`, `p4`: horizontal eye corners (eye width)
- `p2`, `p6`: first vertical pair (upper and lower eyelid)
- `p3`, `p5`: second vertical pair (upper and lower eyelid)

**Typical EAR values:**
- Open eye: `0.25 – 0.35`
- Half-closed: `0.15 – 0.25`
- Closed eye: `< 0.15`

### 3. Drowsiness Detection Logic

Simplified pseudocode:

```python
def detect_state(ear, dt):
    global consecutive_frames, closure_duration

    if ear < threshold:
        consecutive_frames += 1
        closure_duration += dt
        if closure_duration >= 3.0:
            return "SLEEPING"
        if consecutive_frames >= 20:
            return "DROWSY"
    else:
        consecutive_frames = 0
        closure_duration = 0.0
    return "ACTIVE"
```

### 4. Multi-Threaded Architecture

```text
Thread 1 (Capture):    ──► Frame Buffer ──►
Thread 2 (Process):    ◄── Frame Buffer ──► Result Queue
Thread 3 (Display):    ◄── Result Queue ──► Screen
Thread 4 (Alarm):      ◄── Status Update ──► Audio
Thread 5 (Telemetry):  ◄── EAR Data ───────► Graph
```

### 5. Calibration Process

The system automatically calibrates during the first 30 frames:

1. Collect EAR values from the user
2. Calculate the baseline EAR
3. Set threshold to 60% of the baseline
4. Adjust for individual eye characteristics

---

## 📊 Performance Metrics

> ⚠️ **Replace the numbers below with your own measured results before publishing.** Figures that were not measured on your hardware can mislead recruiters and reviewers.

### Benchmark Results

| Hardware | Resolution | FPS | CPU Usage | Memory |
|----------|------------|-----|-----------|--------|
| *Your laptop CPU* | 640x480 | *measure* | *measure* | *measure* |
| *Your second device (optional)* | 480x360 | *measure* | *measure* | *measure* |

### Accuracy Metrics

| Metric | Value | Description |
|--------|-------|-------------|
| **Detection Accuracy** | *measure* | Correct drowsiness detection |
| **False Positive Rate** | *measure* | False alarms per hour |
| **False Negative Rate** | *measure* | Missed drowsiness events |
| **Average Detection Delay** | *measure* | Time from drowsiness onset to alarm |
| **Calibration Time** | ~1.0 s | 30 frames at 30 FPS |

### Real-World Testing

| Scenario | Detection Rate | Notes |
|----------|---------------|-------|
| Daytime, good lighting | *measure* | Optimal conditions |
| Nighttime, low light | *measure* | |
| Sunglasses | *measure* | |
| Eyeglasses | *measure* | |
| Side view | *measure* | Not recommended |

---

## 📁 Project Structure

```text
drowsiness-detection/
│
├── drowsiness_system.py      # Complete system implementation
├── config.yaml               # Configuration file
├── requirements.txt          # Python dependencies
├── README.md                 # Documentation
├── CONTRIBUTING.md           # Contribution guidelines
├── LICENSE                   # MIT License
├── .gitignore                # Git ignore file
│
├── assets/                   # Static assets
│   └── alarm.wav             # Alarm sound
│
├── logs/                     # Log files
│   └── drowsiness_log.csv    # Detection logs
│
├── tests/                    # Test suite
│   ├── test_detector.py
│   ├── test_video_handler.py
│   └── test_alarm.py
│
├── docs/                     # Documentation
│   ├── api.md
│   ├── architecture.md
│   └── user_guide.md
│
└── examples/                 # Example scripts
    ├── headless_mode.py
    ├── api_server.py
    └── custom_threshold.py
```

> Remove any folders listed here that your repository does not actually contain.

---

## 📚 API Documentation

### Core Classes

#### `VideoHandler`

```python
class VideoHandler:
    """Handles video capture with buffering."""

    def start(self) -> bool:
        """Initialize camera and start capture."""

    def read(self) -> Optional[np.ndarray]:
        """Read next frame from camera."""

    def get_fps(self) -> float:
        """Get current FPS."""

    def stop(self) -> None:
        """Release camera resources."""
```

#### `DrowsinessDetector`

```python
class DrowsinessDetector:
    """Detects drowsiness using EAR calculation."""

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """Process frame and return detection results."""

    def get_statistics(self) -> Dict:
        """Get current detection statistics."""

    def reset(self) -> None:
        """Reset detector state."""

    def calibrate_threshold(self, frames: int) -> None:
        """Manually calibrate threshold."""
```

#### `AudioAlarm`

```python
class AudioAlarm:
    """Manages audio alarm playback."""

    def trigger(self) -> None:
        """Start alarm."""

    def stop(self) -> None:
        """Stop alarm."""

    def set_volume(self, volume: float) -> None:
        """Set alarm volume."""

    def is_playing(self) -> bool:
        """Check if alarm is playing."""
```

#### `CSVLogger`

```python
class CSVLogger:
    """Handles CSV logging."""

    def log_data(self, ear: float, status: str, duration: float, fps: float) -> None:
        """Log detection data."""

    def get_recent_logs(self, count: int) -> List:
        """Get recent log entries."""

    def clear_logs(self) -> None:
        """Clear all logs."""

    def export_to_json(self, filename: str) -> None:
        """Export logs to JSON format."""
```

### Events & Callbacks

```python
# Register callbacks for custom behavior
def on_state_change(old_state: str, new_state: str):
    print(f"State changed from {old_state} to {new_state}")

def on_alarm_triggered(status: str):
    print(f"Alarm triggered: {status}")

# Usage
detector.register_state_callback(on_state_change)
alarm.register_trigger_callback(on_alarm_triggered)
```

> Make sure this section matches the method names in your actual `drowsiness_system.py`.

---

## 🔧 Troubleshooting

### Common Issues & Solutions

#### 1. Camera Not Detected

**Symptoms:** "Cannot open camera" error, black screen, no video feed.

```bash
# Linux: check permissions
ls -la /dev/video*
sudo chmod 666 /dev/video0

# Test camera
python -c "import cv2; cap=cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAILED')"

# Try a different camera ID
python drowsiness_system.py --camera 1
```

On Windows, check **Settings → Privacy → Camera** and allow apps to access the camera.

#### 2. Low FPS

**Symptoms:** choppy video, FPS below 20, laggy detection. Lower the resolution and FPS in `config.yaml` and close other applications:

```yaml
camera:
  width: 320
  height: 240
  fps: 15
```

#### 3. No Alarm Sound

**Symptoms:** status changes to drowsy or sleeping, but no audio.

```bash
# Check the sound file exists
ls -la assets/alarm.wav

# Test pygame playback
python -c "import pygame, time; pygame.mixer.init(); pygame.mixer.Sound('assets/alarm.wav').play(); time.sleep(2)"
```

Also check the system volume. Use WAV, 16-bit PCM, 44100 Hz.

#### 4. False Positives / Negatives

**Symptoms:** alarm triggers while awake, or does not trigger when drowsy. Adjust the thresholds in `config.yaml`:

```yaml
detection:
  eye_aspect_ratio_threshold: 0.20   # Less sensitive (fewer false alarms)
  # eye_aspect_ratio_threshold: 0.30 # More sensitive (alarms sooner)
  consecutive_frames_drowsy: 30      # Less sensitive
```

Make sure the face is well lit and not backlit.

#### 5. High CPU Usage

```yaml
camera:
  width: 320
  height: 240
  fps: 15
detection:
  ear_smoothing_window: 10
```

Or run in headless mode:

```bash
python drowsiness_system.py --no-gui
```

### Debug Mode

```bash
python drowsiness_system.py --debug
```

Debug output includes frame-by-frame analysis, EAR history, detection confidence, processing times, and error traces.

### Logging

Logs are written to `logs/drowsiness_log.csv`:

```csv
timestamp,ear_value,status,closure_duration,fps
2026-01-15 14:30:25,0.283,active,0.00,30.2
2026-01-15 14:30:26,0.152,drowsy,1.23,29.8
2026-01-15 14:30:27,0.098,sleeping,2.15,30.1
```

---

## 📸 Outputs

<div align="center">
  <img width="32%" alt="Output screenshot 1" src="https://github.com/user-attachments/assets/c077f08b-7b63-4f2a-8591-148ad6df020f" />
  <img width="32%" alt="Output screenshot 2" src="https://github.com/user-attachments/assets/3732cfc7-d011-44c6-9fcb-30eff7aaea56" />
  <img width="32%" alt="Output screenshot 3" src="https://github.com/user-attachments/assets/667ecec7-0b5b-4b90-90a1-885d49e5ed9c" />
</div>

---

## 🤝 Contributing

Contributions are welcome. Please see the [Contributing Guidelines](CONTRIBUTING.md).

### Development Setup

```bash
# Clone repository
git clone https://github.com/528664-007/drowsiness-detection.git
cd drowsiness-detection

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run linter
flake8 drowsiness_system.py

# Format code
black drowsiness_system.py
```

### How to Contribute

1. **Fork** the repository
2. **Create** a feature branch
3. **Commit** your changes
4. **Push** to your fork
5. **Submit** a pull request

### Reporting Issues

Please include:
- System information (OS, Python version)
- Steps to reproduce
- Expected vs actual behavior
- Log files or screenshots

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

### Open Source Libraries
- **MediaPipe**: face mesh detection
- **OpenCV**: image processing
- **PyGame**: audio playback
- **Matplotlib**: data visualization

### Research Papers
- Soukupová, T., & Čech, J. (2016). *Real-Time Eye Blink Detection using Facial Landmarks.* 21st Computer Vision Winter Workshop.
- Rosebrock, A. (2017). *Eye blink detection with OpenCV, Python, and dlib.* PyImageSearch.

---

## 📞 Contact & Support

- **GitHub Issues**: [Issues page](https://github.com/528664-007/drowsiness-detection/issues)
- **Email**: sameerfayaz1028@gmail.com
- **Author**: [Sameer Yaseen A S](https://github.com/528664-007)

---

<div align="center">

**⭐ If you find this project useful, please give it a star! ⭐**

**Made with ❤️ by Sameer Yaseen A S**

</div>
