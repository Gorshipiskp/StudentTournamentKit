package platform

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/url"
	"sync"
	"time"

	"github.com/gorilla/websocket"

	"github.com/bestcstournaments/director-agent/internal/application"
	"github.com/bestcstournaments/director-agent/internal/domain"
)

// Session talks to Platform Agent WS: receives desired, reports actual.
type Session struct {
	WSURL   string
	Token   string
	MatchID string

	Reconciler *application.Reconciler

	mu   sync.Mutex
	conn *websocket.Conn
}

func (s *Session) ReportActual(ctx context.Context, actual domain.Actual, obsStatus string) error {
	_ = ctx
	msg := map[string]any{
		"protocol": 1,
		"type":     "production.actual",
		"match_id": s.MatchID,
		"actual": map[string]any{
			"scene":  actual.Scene,
			"stream": actual.Stream,
		},
		"obs_status":       obsStatus,
		"broadcast_status": "unknown",
	}
	return s.writeJSON(msg)
}

func (s *Session) writeJSON(v any) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.conn == nil {
		return fmt.Errorf("platform ws not connected")
	}
	return s.conn.WriteJSON(v)
}

// Run connects, handles messages until ctx cancel. Reconnects with backoff.
func (s *Session) Run(ctx context.Context) error {
	backoff := time.Second
	for {
		if err := ctx.Err(); err != nil {
			return err
		}
		err := s.runOnce(ctx)
		if err == nil || ctx.Err() != nil {
			return err
		}
		log.Printf("platform ws disconnected: %v; reconnect in %s", err, backoff)
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

func (s *Session) runOnce(ctx context.Context) error {
	u, err := url.Parse(s.WSURL)
	if err != nil {
		return err
	}
	q := u.Query()
	q.Set("token", s.Token)
	u.RawQuery = q.Encode()

	dialer := websocket.Dialer{HandshakeTimeout: 10 * time.Second}
	conn, _, err := dialer.DialContext(ctx, u.String(), http.Header{})
	if err != nil {
		return fmt.Errorf("dial platform: %w", err)
	}
	s.mu.Lock()
	s.conn = conn
	s.mu.Unlock()
	defer func() {
		s.mu.Lock()
		_ = conn.Close()
		s.conn = nil
		s.mu.Unlock()
	}()

	log.Printf("connected to platform %s", u.Redacted())

	// Hello — Platform replies with current desired (A12)
	_ = s.writeJSON(map[string]any{
		"protocol":         1,
		"type":             "agent.hello",
		"match_id":         s.MatchID,
		"protocol_version": "1",
		"agent_version":    "0.1.0",
	})

	for {
		_ = conn.SetReadDeadline(time.Now().Add(60 * time.Second))
		_, data, err := conn.ReadMessage()
		if err != nil {
			return err
		}
		var msg map[string]any
		if err := json.Unmarshal(data, &msg); err != nil {
			log.Printf("bad json from platform: %v", err)
			continue
		}
		typ, _ := msg["type"].(string)
		switch typ {
		case "production.desired":
			desired := parseDesired(msg)
			s.Reconciler.SetDesired(desired)
			if err := s.Reconciler.ApplyDesired(ctx); err != nil {
				log.Printf("apply desired failed: %v", err)
			}
		case "production.actual_ack", "agent.pong", "error":
			log.Printf("platform ← %s", typ)
		default:
			log.Printf("platform ← ignore type=%s", typ)
		}
	}
}

func parseDesired(msg map[string]any) domain.Desired {
	d := domain.Desired{Scene: domain.SceneWaiting, Stream: "off"}
	raw, ok := msg["desired"].(map[string]any)
	if !ok {
		return d
	}
	if sc, ok := raw["scene"].(string); ok && sc != "" {
		d.Scene = sc
	}
	if st, ok := raw["stream"].(string); ok && st != "" {
		d.Stream = st
	}
	return d
}

// BuildAgentWSURL builds ws://host/ws/agent/{matchId} from platform base.
func BuildAgentWSURL(platformBase, matchID string) (string, error) {
	u, err := url.Parse(platformBase)
	if err != nil {
		return "", err
	}
	switch u.Scheme {
	case "http":
		u.Scheme = "ws"
	case "https":
		u.Scheme = "wss"
	case "ws", "wss":
		// ok
	default:
		return "", fmt.Errorf("unsupported platform scheme %q", u.Scheme)
	}
	u.Path = fmt.Sprintf("/ws/agent/%s", url.PathEscape(matchID))
	u.RawQuery = ""
	u.Fragment = ""
	return u.String(), nil
}
