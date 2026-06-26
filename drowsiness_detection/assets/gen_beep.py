#!/usr/bin/env python3
"""Run this once to create assets/alarm.wav:  python assets/gen_beep.py"""
import numpy as np, wave, struct, os

out = os.path.join(os.path.dirname(__file__), "alarm.wav")
freq, dur, rate = 880, 1.0, 44100
t = np.linspace(0, dur, int(rate * dur))
# two-tone beep (880 + 1320 Hz) for better audibility
s = (np.sin(2*np.pi*freq*t) + 0.5*np.sin(2*np.pi*1320*t))
s = (s / s.max() * 32767 * 0.9).astype(np.int16)
with wave.open(out, "w") as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(rate)
    f.writeframes(b"".join(struct.pack("<h", x) for x in s))
print(f"Created: {out}  ({dur}s, {rate} Hz, mono)")
