"""
Alarm v5 — ZERO background threads. Called from the main loop only.

Root cause of camera lag (v3/v4):
  pygame.mixer is NOT thread-safe on Windows. When a background thread
  calls channel.play() / channel.get_busy(), it acquires an internal
  pygame SDL mutex. cv2.waitKey() on Windows pumps the Win32 message
  queue which also touches that mutex → main loop BLOCKS → camera lags.

Fix:
  No threads at all. update(status) is called once per frame from the
  main loop. It issues play(loops=-1) on transition to alarm, and
  channel.stop() on transition back to active. Sub-millisecond overhead.
"""
from pathlib import Path

try:
    import pygame as _pg
    _HAVE_PG = True
except ImportError:
    _HAVE_PG = False


class AudioAlarm:

    def __init__(self, config: dict):
        self._file    = config.get("sound_file", "assets/alarm.wav")
        self._volume  = float(config.get("volume", 0.9))
        self._channel = None
        self._sound   = None
        self._active  = False        # current playback state

        if not _HAVE_PG:
            print("[Alarm] pygame not installed — audio disabled")
            return

        # Try mixer configs in order of preference
        inited = False
        for freq, ch, buf in ((44100,2,2048),(44100,1,2048),(22050,1,1024)):
            try:
                if _pg.mixer.get_init():
                    _pg.mixer.quit()
                _pg.mixer.pre_init(frequency=freq, size=-16,
                                   channels=ch, buffer=buf)
                _pg.mixer.init()
                inited = True
                print(f"[Alarm] Mixer: {freq} Hz  {ch}ch  buf={buf}")
                break
            except Exception:
                pass
        if not inited:
            print("[Alarm] Could not init pygame mixer — audio disabled")
            return

        _pg.mixer.set_num_channels(2)
        self._channel = _pg.mixer.Channel(0)   # dedicated channel

        path = Path(self._file)
        if not path.exists():
            print(f"[Alarm] {self._file} not found — run: python assets/gen_beep.py")
            return
        try:
            self._sound = _pg.mixer.Sound(str(path))
            self._sound.set_volume(self._volume)
            dur = self._sound.get_length()
            print(f"[Alarm] Loaded: {self._file}  ({dur:.2f}s)")
        except Exception as e:
            print(f"[Alarm] Load error: {e}")

    # ── called every frame from the main loop ──────────────────────────────
    def update(self, want_alarm: bool):
        """
        Call once per frame from the main thread.
        Transitions:  off→on : play(loops=-1)   on→off : stop()
        No-ops when state hasn't changed — extremely cheap.
        """
        if self._channel is None or self._sound is None:
            return
        if want_alarm and not self._active:
            try:
                self._channel.play(self._sound, loops=-1)
                self._active = True
            except Exception as e:
                print(f"[Alarm] play error: {e}")
        elif not want_alarm and self._active:
            try:
                self._channel.stop()
                self._active = False
            except Exception as e:
                print(f"[Alarm] stop error: {e}")

    # ── convenience wrappers (kept for API compatibility) ──────────────────
    def trigger(self):
        self.update(True)

    def stop(self):
        self.update(False)

    def shutdown(self):
        self.update(False)
        try:
            if _HAVE_PG and _pg.mixer.get_init():
                _pg.mixer.quit()
        except Exception:
            pass
