// Package domain — production scene types (no OBS protocol details).
package domain

const (
	SceneWaiting = "waiting"
	SceneIntro   = "intro"
	SceneTeams   = "teams"
	SceneIngame  = "ingame"
	SceneBreak   = "break"
	SceneWinner  = "winner"
)

// Desired is platform-authoritative production desired state.
type Desired struct {
	Scene  string
	Stream string
}

// Actual is observed OBS/runtime state.
type Actual struct {
	Scene  string
	Stream string
}
