# Optional: OBS Virtual Camera → WebRTC (not required for GATE)

Primary GATE uses `--fake-webrtc` (embedded VP8 test pattern via Pion).

For a real camera path later:

1. OBS → Start Virtual Camera
2. FFmpeg capture (Windows dshow), example:

```text
ffmpeg -f dshow -i video="OBS Virtual Camera" -c:v libvpx -f ivf - | …
```

3. Pipe IVF / raw frames into Pion `TrackLocalStaticSample` (same publisher signaling as fake).

Do **not** run arbitrary OBS RPCs from Agent — only the existing scene whitelist (A8).
Audio WebRTC remains off (F7).
