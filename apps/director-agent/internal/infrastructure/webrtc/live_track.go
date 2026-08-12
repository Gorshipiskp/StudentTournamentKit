package webrtcpub

import (
	"context"
	"fmt"
	"io"
	"log"
	"os"
	"os/exec"
	"strings"
	"time"

	"github.com/pion/webrtc/v4"
	"github.com/pion/webrtc/v4/pkg/media"
	"github.com/pion/webrtc/v4/pkg/media/ivfreader"
)

const DefaultWebRTCDevice = "OBS Virtual Camera"

// LiveTrack captures OBS Virtual Camera via FFmpeg (dshow) into a VP8 TrackLocalStaticSample.
type LiveTrack struct {
	Track      *webrtc.TrackLocalStaticSample
	FFmpegPath string
	Device     string
}

// ResolveFFmpeg returns an absolute-enough path to ffmpeg or a clear error.
func ResolveFFmpeg(explicit string) (string, error) {
	if explicit != "" {
		if _, err := os.Stat(explicit); err != nil {
			return "", fmt.Errorf("ffmpeg not found at %q: %w (install FFmpeg or set --webrtc-ffmpeg / STK_WEBRTC_FFMPEG)", explicit, err)
		}
		return explicit, nil
	}
	path, err := exec.LookPath("ffmpeg")
	if err != nil {
		return "", fmt.Errorf("ffmpeg not on PATH: %w — install FFmpeg or pass --webrtc-ffmpeg (see webrtc/README)", err)
	}
	return path, nil
}

// BuildLiveFFmpegArgs builds dshow → VP8 IVF pipe args (no audio). Windows DirectShow.
func BuildLiveFFmpegArgs(device string) []string {
	if device == "" {
		device = DefaultWebRTCDevice
	}
	return []string{
		"-hide_banner",
		"-loglevel", "warning",
		"-f", "dshow",
		"-rtbufsize", "100M",
		"-i", "video=" + device,
		"-an",
		"-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,format=yuv420p",
		"-c:v", "libvpx",
		"-b:v", "3500k",
		"-maxrate", "4000k",
		"-bufsize", "7000k",
		"-deadline", "good",
		"-cpu-used", "4",
		"-r", "30",
		"-g", "60",
		"-f", "ivf",
		"pipe:1",
	}
}
// NewLiveTrack prepares a VP8 track; call Run to start FFmpeg capture.
func NewLiveTrack(ffmpegPath, device string) (*LiveTrack, error) {
	ff, err := ResolveFFmpeg(ffmpegPath)
	if err != nil {
		return nil, err
	}
	if device == "" {
		device = DefaultWebRTCDevice
	}
	track, err := webrtc.NewTrackLocalStaticSample(
		webrtc.RTPCodecCapability{MimeType: webrtc.MimeTypeVP8},
		"video",
		"stk-live",
	)
	if err != nil {
		return nil, err
	}
	return &LiveTrack{Track: track, FFmpegPath: ff, Device: device}, nil
}

// Run starts FFmpeg and pumps IVF frames until ctx cancel. Restarts on transient failure.
func (l *LiveTrack) Run(ctx context.Context) error {
	backoff := time.Second
	for {
		if err := ctx.Err(); err != nil {
			return err
		}
		err := l.runOnce(ctx)
		if ctx.Err() != nil {
			return ctx.Err()
		}
		log.Printf("live-webrtc capture ended: %v; retry in %s", err, backoff)
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(backoff):
		}
		if backoff < 8*time.Second {
			backoff *= 2
		}
	}
}

func (l *LiveTrack) runOnce(ctx context.Context) error {
	args := BuildLiveFFmpegArgs(l.Device)
	cmd := exec.CommandContext(ctx, l.FFmpegPath, args...)
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return err
	}
	stderr, err := cmd.StderrPipe()
	if err != nil {
		return err
	}
	if err := cmd.Start(); err != nil {
		return fmt.Errorf("start ffmpeg: %w", err)
	}

	errCh := make(chan error, 1)
	go func() {
		b, _ := io.ReadAll(stderr)
		msg := strings.TrimSpace(string(b))
		waitErr := cmd.Wait()
		if waitErr == nil {
			errCh <- nil
			return
		}
		if msg == "" {
			errCh <- fmt.Errorf("ffmpeg exited: %w (is OBS Virtual Camera started? device=%q)", waitErr, l.Device)
			return
		}
		errCh <- fmt.Errorf("ffmpeg: %s (%v) — start OBS Virtual Camera; device=%q", msg, waitErr, l.Device)
	}()

	readErr := l.pumpIVF(ctx, stdout)
	_ = stdout.Close()
	// Ensure process stopped
	if cmd.Process != nil {
		_ = cmd.Process.Kill()
	}
	procErr := <-errCh
	if readErr != nil && ctx.Err() == nil {
		if procErr != nil {
			return fmt.Errorf("%v; also: %w", procErr, readErr)
		}
		return readErr
	}
	if procErr != nil && ctx.Err() == nil {
		return procErr
	}
	return ctx.Err()
}

func (l *LiveTrack) pumpIVF(ctx context.Context, r io.Reader) error {
	reader, header, err := ivfreader.NewWith(r)
	if err != nil {
		return fmt.Errorf("ivf header (ffmpeg/device?): %w", err)
	}
	frameDuration := time.Second / 30
	if header.TimebaseDenominator != 0 && header.TimebaseNumerator != 0 {
		frameDuration = time.Duration(float64(time.Second) *
			float64(header.TimebaseNumerator) / float64(header.TimebaseDenominator))
	}
	if frameDuration <= 0 {
		frameDuration = time.Second / 30
	}

	for {
		frame, _, err := reader.ParseNextFrame()
		if err == io.EOF {
			return io.EOF
		}
		if err != nil {
			return err
		}
		if err := ctx.Err(); err != nil {
			return err
		}
		if err := l.Track.WriteSample(media.Sample{Data: frame, Duration: frameDuration}); err != nil {
			return err
		}
	}
}
