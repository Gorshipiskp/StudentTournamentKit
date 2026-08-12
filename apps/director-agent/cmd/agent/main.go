package main

import (
	"context"
	"flag"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/bestcstournaments/director-agent/internal/application"
	"github.com/bestcstournaments/director-agent/internal/infrastructure/obs"
	webrtcpub "github.com/bestcstournaments/director-agent/internal/infrastructure/webrtc"
	"github.com/bestcstournaments/director-agent/internal/presentation/platform"
)

func main() {
	platformBase := flag.String("platform", envOr("STK_PLATFORM_URL", "http://127.0.0.1:8000"), "Platform HTTP base (ws derived)")
	matchID := flag.String("match", envOr("STK_MATCH_ID", ""), "Match id")
	token := flag.String("token", envOr("STK_AGENT_TOKEN", "dev_agent_token_change_me"), "Agent WS token")
	fakeOBS := flag.Bool("fake-obs", false, "Use in-memory Fake OBS (CI/GATE without OBS Studio)")
	fakeWebRTC := flag.Bool("fake-webrtc", false, "Publish synthetic VP8 test pattern via Platform signaling (Pion)")
	liveWebRTC := flag.Bool("live-webrtc", false, "Publish OBS Virtual Camera via FFmpeg → Pion (TZ008); or STK_LIVE_WEBRTC=1")
	webrtcDevice := flag.String("webrtc-device", envOr("STK_WEBRTC_DEVICE", webrtcpub.DefaultWebRTCDevice), "DirectShow video device name")
	webrtcFFmpeg := flag.String("webrtc-ffmpeg", envOr("STK_WEBRTC_FFMPEG", ""), "Path to ffmpeg (default: PATH)")
	obsURL := flag.String("obs-url", envOr("STK_OBS_URL", "ws://127.0.0.1:4455"), "OBS WebSocket v5 URL")
	obsPassword := flag.String("obs-password", envOr("STK_OBS_PASSWORD", ""), "OBS WebSocket password")
	flag.Parse()

	if *matchID == "" {
		log.Fatal("required: --match or STK_MATCH_ID")
	}
	live := *liveWebRTC || os.Getenv("STK_LIVE_WEBRTC") == "1"
	if *fakeWebRTC && live {
		log.Fatal("use either --fake-webrtc or --live-webrtc, not both")
	}

	wsURL, err := platform.BuildAgentWSURL(*platformBase, *matchID)
	if err != nil {
		log.Fatalf("platform url: %v", err)
	}

	var ctrl obs.Controller
	if *fakeOBS {
		log.Printf("using FakeOBS")
		ctrl = obs.NewFakeOBS("waiting")
	} else {
		log.Printf("using OBS WebSocket %s", *obsURL)
		ctrl = obs.NewClient(*obsURL, *obsPassword)
	}

	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()

	if err := ctrl.Connect(ctx); err != nil {
		log.Fatalf("obs connect: %v", err)
	}
	defer ctrl.Close()

	session := &platform.Session{
		WSURL:   wsURL,
		Token:   *token,
		MatchID: *matchID,
	}
	rec := application.NewReconciler(ctrl, session)
	session.Reconciler = rec

	if *fakeWebRTC {
		ivfPath, err := webrtcpub.DefaultIVFPath()
		if err != nil {
			log.Fatalf("fake-webrtc ivf: %v", err)
		}
		fake, err := webrtcpub.NewFakeTrackFromIVF(ivfPath)
		if err != nil {
			log.Fatalf("fake-webrtc track: %v", err)
		}
		pub := &webrtcpub.Publisher{
			PlatformBase: *platformBase,
			MatchID:      *matchID,
			Token:        *token,
			VideoTrack:   fake.Track,
		}
		go func() {
			if err := fake.Run(ctx); err != nil && ctx.Err() == nil {
				log.Printf("fake track ended: %v", err)
			}
		}()
		go func() {
			if err := pub.Run(ctx); err != nil && ctx.Err() == nil {
				log.Printf("webrtc publisher ended: %v", err)
			}
		}()
		log.Printf("fake-webrtc publisher started (signaling separate from OBS reconcile)")
	}

	if live {
		liveTrack, err := webrtcpub.NewLiveTrack(*webrtcFFmpeg, *webrtcDevice)
		if err != nil {
			log.Fatalf("live-webrtc: %v", err)
		}
		pub := &webrtcpub.Publisher{
			PlatformBase: *platformBase,
			MatchID:      *matchID,
			Token:        *token,
			VideoTrack:   liveTrack.Track,
		}
		go func() {
			if err := liveTrack.Run(ctx); err != nil && ctx.Err() == nil {
				log.Printf("live track ended: %v", err)
			}
		}()
		go func() {
			if err := pub.Run(ctx); err != nil && ctx.Err() == nil {
				log.Printf("webrtc publisher ended: %v", err)
			}
		}()
		log.Printf("live-webrtc publisher started device=%q ffmpeg=%s", liveTrack.Device, liveTrack.FFmpegPath)
	}

	log.Printf("director-agent match=%s platform=%s fake-obs=%v fake-webrtc=%v live-webrtc=%v",
		*matchID, wsURL, *fakeOBS, *fakeWebRTC, live)
	if err := session.Run(ctx); err != nil && ctx.Err() == nil {
		log.Fatalf("session: %v", err)
	}
	log.Printf("shutdown")
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
