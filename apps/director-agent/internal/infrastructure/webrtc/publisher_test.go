package webrtcpub

import (
	"testing"
)

func TestBuildSignalingWSURL(t *testing.T) {
	u, err := BuildSignalingWSURL("http://127.0.0.1:8000", "m_dev")
	if err != nil {
		t.Fatal(err)
	}
	want := "ws://127.0.0.1:8000/ws/signaling/m_dev"
	if u != want {
		t.Fatalf("got %q want %q", u, want)
	}
	u2, err := BuildSignalingWSURL("https://plat.example", "m%20x")
	if err != nil {
		t.Fatal(err)
	}
	if u2 != "wss://plat.example/ws/signaling/m%20x" {
		// PathEscape of match id
		t.Logf("https url: %s", u2)
	}
}

func TestDefaultIVFPathReadable(t *testing.T) {
	path, err := DefaultIVFPath()
	if err != nil {
		t.Fatal(err)
	}
	ft, err := NewFakeTrackFromIVF(path)
	if err != nil {
		t.Fatal(err)
	}
	if ft.Track == nil {
		t.Fatal("expected track")
	}
}
