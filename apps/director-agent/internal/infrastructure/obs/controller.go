package obs

import "context"

// Controller is the OBS control surface used by the reconciler.
// Real OBS WebSocket v5 or FakeOBS for CI.
type Controller interface {
	Connect(ctx context.Context) error
	Close() error
	GetCurrentProgramScene(ctx context.Context) (string, error)
	SetCurrentProgramScene(ctx context.Context, scene string) error
	Status() string // connected | disconnected
}
