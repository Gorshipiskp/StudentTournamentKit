package webrtcpub

import (
	"strings"
	"testing"
)

func TestBuildLiveFFmpegArgs(t *testing.T) {
	args := BuildLiveFFmpegArgs("")
	joined := strings.Join(args, " ")
	if !strings.Contains(joined, "video="+DefaultWebRTCDevice) {
		t.Fatalf("expected default device in %v", args)
	}
	if !strings.Contains(joined, "-f ivf") && !containsPair(args, "-f", "ivf") {
		t.Fatalf("expected ivf muxer in %v", args)
	}
	if containsArg(args, "-an") == false {
		t.Fatal("expected -an (no audio)")
	}
	args2 := BuildLiveFFmpegArgs("Custom Cam")
	if !containsArg(args2, "video=Custom Cam") {
		t.Fatalf("custom device: %v", args2)
	}
}

func TestResolveFFmpegMissing(t *testing.T) {
	_, err := ResolveFFmpeg(`C:\no\such\ffmpeg-stk-test.exe`)
	if err == nil {
		t.Fatal("expected error for missing ffmpeg")
	}
	if !strings.Contains(err.Error(), "ffmpeg") {
		t.Fatalf("error should mention ffmpeg: %v", err)
	}
}

func TestNewLiveTrackMissingFFmpeg(t *testing.T) {
	_, err := NewLiveTrack(`C:\no\such\ffmpeg-stk-test.exe`, DefaultWebRTCDevice)
	if err == nil {
		t.Fatal("expected error")
	}
}

func TestBuildLiveFFmpegArgsNoAudioCodec(t *testing.T) {
	args := BuildLiveFFmpegArgs(DefaultWebRTCDevice)
	for i, a := range args {
		if a == "-c:a" || a == "libopus" || a == "aac" {
			t.Fatalf("audio encode not allowed in live args: %v near %s", args, args[i])
		}
	}
}

func TestResolveFFmpegEmptyUsesLookPathOrError(t *testing.T) {
	// Either finds ffmpeg on PATH or returns a clear error — never panics / empty path.
	path, err := ResolveFFmpeg("")
	if err != nil {
		if !strings.Contains(err.Error(), "ffmpeg") {
			t.Fatalf("expected ffmpeg in error: %v", err)
		}
		return
	}
	if path == "" {
		t.Fatal("empty path without error")
	}
}

func containsArg(args []string, want string) bool {
	for _, a := range args {
		if a == want {
			return true
		}
	}
	return false
}

func containsPair(args []string, a, b string) bool {
	for i := 0; i+1 < len(args); i++ {
		if args[i] == a && args[i+1] == b {
			return true
		}
	}
	return false
}
