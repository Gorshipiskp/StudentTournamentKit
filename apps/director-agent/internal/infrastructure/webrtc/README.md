# WebRTC publisher — Fake + Live Virtual Cam (**legacy**)

> **Канон комментаторов (TZ011):** OBS **WHIP** → MediaMTX → `/watch` WHEP.  
> Этот README — Fake CI (`--fake-webrtc`) и **deprecated** `--live-webrtc` (Virtual Cam).  
> См. [Agent README §4d](../../../README.md) · [WEBRTC-CONTRACT](../../../../docs/WEBRTC-CONTRACT.md).

## Modes

| Mode | Flag | When |
|------|------|------|
| Fake | `--fake-webrtc` | CI / verify / репетиция (**default**) |
| Live VC | `--live-webrtc` | **deprecated** — owner debug only |

Same `Publisher` + Platform signaling for Fake/legacy. Live canon = WHIP (no Agent encode).

> Contract: [`docs/WEBRTC-CONTRACT.md`](../../../../docs/WEBRTC-CONTRACT.md). Audio WebRTC off (F4).

---

## Spike (2026-08-12, Windows @owner machine)

### List DirectShow devices

```powershell
# Adjust path if ffmpeg is on PATH
& C:\ffmpeg\bin\ffmpeg.exe -hide_banner -list_devices true -f dshow -i dummy
```

**Confirmed video device name:** `OBS Virtual Camera`  
(Other cams may appear — XSplit, DroidCam, etc. Default for STK = OBS.)

### One-frame probe (Virtual Cam must be started in OBS)

```powershell
& C:\ffmpeg\bin\ffmpeg.exe -hide_banner `
  -f dshow -rtbufsize 100M -i video="OBS Virtual Camera" `
  -frames:v 1 -update 1 -y $env:TEMP\stk_vcam_spike.png
```

Spike result: **OK** — 1920×1080, NV12, ~60 fps; PNG written.  
Note: without `-rtbufsize` dshow may warn «buffer too full» — use a large `rtbufsize` in P2.

If probe fails: OBS → **Start Virtual Camera**, then retry. Device still listed when cam is off, but frames may be black/stuck.

---

## Reproducible capture commands (Windows)

### A) List devices (always first on a new PC)

```powershell
ffmpeg -hide_banner -list_devices true -f dshow -i dummy
```

Expect a line: `"OBS Virtual Camera" (video)`.

### B) Raw preview / sanity (optional)

```powershell
ffmpeg -f dshow -rtbufsize 100M -i video="OBS Virtual Camera" -pix_fmt yuv420p -f sdl2 -
```

### C) VP8 IVF pipe (Agent live path)

Default in Agent (после GATE close): **1920×1080**, **~3500k**, `deadline=good`, `cpu-used=4`.  
Если CPU ноутбука не тянет — снизь в `BuildLiveFFmpegArgs` / будущем флаге bitrate или scale.

```powershell
ffmpeg -f dshow -rtbufsize 100M -i video="OBS Virtual Camera" `
  -an `
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,format=yuv420p" `
  -c:v libvpx -b:v 3500k -maxrate 4000k -bufsize 7000k `
  -deadline good -cpu-used 4 `
  -r 30 -g 60 `
  -f ivf -
```

### Device override (planned flag)

Default device string: `OBS Virtual Camera`.  
Override (P2): `--webrtc-device="OBS Virtual Camera"` or env `STK_WEBRTC_DEVICE`.

---

## Agent flags (TZ008)

| Flag / env | Meaning | Default |
|------------|---------|---------|
| `--fake-webrtc` | Synthetic VP8 IVF loop (CI) | off |
| `--live-webrtc` / `STK_LIVE_WEBRTC=1` | Capture Virtual Cam → publisher | off |
| `--webrtc-device` / `STK_WEBRTC_DEVICE` | dshow video device name | `OBS Virtual Camera` |
| `--webrtc-ffmpeg` / `STK_WEBRTC_FFMPEG` | Path to `ffmpeg` binary | `ffmpeg` on PATH |
| `--platform` / `STK_PLATFORM_URL` | Platform HTTP base | `http://127.0.0.1:8000` |
| `--match` / `STK_MATCH_ID` | Match id | required |
| `--token` / `STK_AGENT_TOKEN` | Agent token | required |

Do **not** pass `--fake-webrtc` and `--live-webrtc` together.

**CI / verify:** always `--fake-webrtc` (and usually `--fake-obs`).  
**Live day:** OBS Virtual Camera on + Agent `--live-webrtc`.

```powershell
# Fake (unchanged)
.\stk-director-agent.exe --fake-obs --fake-webrtc --match m_dev --token …

# Live Virtual Cam (OBS started + Virtual Camera on)
.\stk-director-agent.exe --fake-obs --live-webrtc --match m_dev --token … `
  --webrtc-device "OBS Virtual Camera" `
  --webrtc-ffmpeg C:\ffmpeg\bin\ffmpeg.exe
```

---

## Operator checklist (short)

1. OBS: scenes + overlay Browser Source; **Start Virtual Camera**.
2. Do **not** put Stream Delay on the Virtual Cam path (Twitch delay is separate).
3. `ffmpeg -list_devices` → see `OBS Virtual Camera`.
4. Run Agent live flags (P2); open `/watch?token=…`.

Templates delay note: [`templates/README.md`](../../templates/README.md) §3.
