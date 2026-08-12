package obs

import (
	"context"
	"sync"
)

// FakeOBS in-memory scene store for CI / GATE without OBS Studio.
type FakeOBS struct {
	mu     sync.Mutex
	scene  string
	status string
}

func NewFakeOBS(initialScene string) *FakeOBS {
	if initialScene == "" {
		initialScene = "waiting"
	}
	return &FakeOBS{scene: initialScene, status: "disconnected"}
}

func (f *FakeOBS) Connect(ctx context.Context) error {
	_ = ctx
	f.mu.Lock()
	defer f.mu.Unlock()
	f.status = "connected"
	return nil
}

func (f *FakeOBS) Close() error {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.status = "disconnected"
	return nil
}

func (f *FakeOBS) GetCurrentProgramScene(ctx context.Context) (string, error) {
	_ = ctx
	f.mu.Lock()
	defer f.mu.Unlock()
	return f.scene, nil
}

func (f *FakeOBS) SetCurrentProgramScene(ctx context.Context, scene string) error {
	_ = ctx
	f.mu.Lock()
	defer f.mu.Unlock()
	f.scene = scene
	return nil
}

func (f *FakeOBS) Status() string {
	f.mu.Lock()
	defer f.mu.Unlock()
	return f.status
}

// Scene returns current scene (test helper).
func (f *FakeOBS) Scene() string {
	f.mu.Lock()
	defer f.mu.Unlock()
	return f.scene
}
