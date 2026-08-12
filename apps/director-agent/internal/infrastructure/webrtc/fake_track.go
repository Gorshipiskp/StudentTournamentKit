package webrtcpub

import (
	"context"
	"fmt"
	"io"
	"log"
	"time"

	"github.com/pion/webrtc/v4"
	"github.com/pion/webrtc/v4/pkg/media"
	"github.com/pion/webrtc/v4/pkg/media/ivfreader"
)

// FakeTrack loops an IVF (VP8) file into a TrackLocalStaticSample.
type FakeTrack struct {
	Track *webrtc.TrackLocalStaticSample
	path  string
}

func NewFakeTrackFromIVF(path string) (*FakeTrack, error) {
	track, err := webrtc.NewTrackLocalStaticSample(
		webrtc.RTPCodecCapability{MimeType: webrtc.MimeTypeVP8},
		"video",
		"stk-fake",
	)
	if err != nil {
		return nil, err
	}
	return &FakeTrack{Track: track, path: path}, nil
}

// Run writes samples until ctx cancel. Loops the IVF forever.
func (f *FakeTrack) Run(ctx context.Context) error {
	for {
		if err := ctx.Err(); err != nil {
			return err
		}
		if err := f.playOnce(ctx); err != nil {
			if ctx.Err() != nil {
				return ctx.Err()
			}
			log.Printf("fake-webrtc ivf loop: %v; retry", err)
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(time.Second):
			}
		}
	}
}

func (f *FakeTrack) playOnce(ctx context.Context) error {
	file, err := openIVF(f.path)
	if err != nil {
		return err
	}
	defer file.Close()

	reader, header, err := ivfreader.NewWith(file)
	if err != nil {
		return fmt.Errorf("ivf reader: %w", err)
	}
	// Duration from IVF timescale (fps ≈ timebase)
	frameDuration := time.Second / 30
	if header.TimebaseDenominator != 0 && header.TimebaseNumerator != 0 {
		frameDuration = time.Duration(float64(time.Second) *
			float64(header.TimebaseNumerator) / float64(header.TimebaseDenominator))
	}
	if frameDuration <= 0 {
		frameDuration = time.Second / 10
	}

	ticker := time.NewTicker(frameDuration)
	defer ticker.Stop()

	for {
		frame, _, err := reader.ParseNextFrame()
		if err == io.EOF {
			return nil // restart loop
		}
		if err != nil {
			return err
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-ticker.C:
			if err := f.Track.WriteSample(media.Sample{Data: frame, Duration: frameDuration}); err != nil {
				return err
			}
		}
	}
}
