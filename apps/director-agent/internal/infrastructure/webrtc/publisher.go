package webrtcpub

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	"github.com/pion/webrtc/v4"
)

// Publisher connects to Platform signaling as role=publisher and offers VP8 to subscribers.
type Publisher struct {
	PlatformBase string
	MatchID      string
	Token        string
	VideoTrack   *webrtc.TrackLocalStaticSample

	mu       sync.Mutex
	peers    map[string]*peerSession
	iceURLs  []string
	iceUser  string
	iceCred  string
}

type peerSession struct {
	pc     *webrtc.PeerConnection
	peerID string
}

type turnCreds struct {
	URLs       []string `json:"urls"`
	Username   string   `json:"username"`
	Credential string   `json:"credential"`
}

// Run reconnects signaling independently of OBS Agent WS.
func (p *Publisher) Run(ctx context.Context) error {
	p.peers = map[string]*peerSession{}
	backoff := time.Second
	for {
		if err := ctx.Err(); err != nil {
			return err
		}
		_ = p.refreshTURN(ctx)
		err := p.runOnce(ctx)
		p.closeAllPeers()
		if err == nil || ctx.Err() != nil {
			return err
		}
		log.Printf("signaling disconnected: %v; reconnect in %s", err, backoff)
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

func (p *Publisher) refreshTURN(ctx context.Context) error {
	u, err := url.Parse(p.PlatformBase)
	if err != nil {
		return err
	}
	u.Path = fmt.Sprintf("/api/v1/matches/%s/turn-credentials", url.PathEscape(p.MatchID))
	u.RawQuery = ""
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, u.String(), bytes.NewReader([]byte("{}")))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-STK-Agent-Token", p.Token)
	res, err := http.DefaultClient.Do(req)
	if err != nil {
		log.Printf("turn credentials: %v (STUN-only)", err)
		return err
	}
	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)
	if res.StatusCode >= 300 {
		log.Printf("turn credentials HTTP %s: %s (STUN-only)", res.Status, body)
		return fmt.Errorf("turn http %s", res.Status)
	}
	var creds turnCreds
	if err := json.Unmarshal(body, &creds); err != nil {
		return err
	}
	p.mu.Lock()
	p.iceURLs = creds.URLs
	p.iceUser = creds.Username
	p.iceCred = creds.Credential
	p.mu.Unlock()
	log.Printf("turn credentials ok urls=%d ttl user=%s", len(creds.URLs), creds.Username)
	return nil
}

func (p *Publisher) runOnce(ctx context.Context) error {
	wsURL, err := BuildSignalingWSURL(p.PlatformBase, p.MatchID)
	if err != nil {
		return err
	}
	u, err := url.Parse(wsURL)
	if err != nil {
		return err
	}
	q := u.Query()
	q.Set("role", "publisher")
	q.Set("token", p.Token)
	u.RawQuery = q.Encode()

	dialer := websocket.Dialer{HandshakeTimeout: 10 * time.Second}
	conn, _, err := dialer.DialContext(ctx, u.String(), http.Header{})
	if err != nil {
		return fmt.Errorf("dial signaling: %w", err)
	}
	defer conn.Close()
	log.Printf("signaling connected %s", u.Redacted())

	var selfID string
	writeMu := sync.Mutex{}
	writeJSON := func(v any) error {
		writeMu.Lock()
		defer writeMu.Unlock()
		return conn.WriteJSON(v)
	}

	for {
		_ = conn.SetReadDeadline(time.Now().Add(90 * time.Second))
		_, data, err := conn.ReadMessage()
		if err != nil {
			return err
		}
		var msg map[string]any
		if err := json.Unmarshal(data, &msg); err != nil {
			continue
		}
		typ, _ := msg["type"].(string)
		switch typ {
		case "signaling.hello":
			selfID, _ = msg["peer_id"].(string)
			log.Printf("signaling hello peer_id=%s", selfID)
		case "signaling.peer_joined":
			subID, _ := msg["peer_id"].(string)
			if subID == "" || selfID == "" {
				continue
			}
			log.Printf("subscriber joined %s — sending offer", subID)
			if err := p.offerTo(ctx, selfID, subID, writeJSON); err != nil {
				log.Printf("offer failed: %v", err)
			}
		case "signaling.answer":
			from, _ := msg["from"].(string)
			sdp, _ := msg["sdp"].(string)
			p.handleAnswer(from, sdp)
		case "signaling.ice":
			from, _ := msg["from"].(string)
			candRaw, _ := msg["candidate"].(map[string]any)
			p.handleRemoteICE(from, candRaw)
		case "signaling.peer_left":
			id, _ := msg["peer_id"].(string)
			p.closePeer(id)
		case "error":
			log.Printf("signaling error: %v", msg["detail"])
		default:
			log.Printf("signaling ← %s", typ)
		}
	}
}

func (p *Publisher) iceServers() []webrtc.ICEServer {
	servers := []webrtc.ICEServer{{URLs: []string{"stun:stun.l.google.com:19302"}}}
	p.mu.Lock()
	defer p.mu.Unlock()
	if len(p.iceURLs) > 0 {
		servers = append(servers, webrtc.ICEServer{
			URLs:       p.iceURLs,
			Username:   p.iceUser,
			Credential: p.iceCred,
		})
	}
	return servers
}

func (p *Publisher) offerTo(ctx context.Context, selfID, subID string, writeJSON func(any) error) error {
	_ = ctx
	p.closePeer(subID)

	pc, err := webrtc.NewPeerConnection(webrtc.Configuration{ICEServers: p.iceServers()})
	if err != nil {
		return err
	}
	if _, err := pc.AddTrack(p.VideoTrack); err != nil {
		_ = pc.Close()
		return err
	}

	pc.OnICECandidate(func(c *webrtc.ICECandidate) {
		if c == nil {
			return
		}
		init := c.ToJSON()
		_ = writeJSON(map[string]any{
			"protocol":  1,
			"type":      "signaling.ice",
			"from":      selfID,
			"to":        subID,
			"candidate": init,
		})
	})
	pc.OnConnectionStateChange(func(s webrtc.PeerConnectionState) {
		log.Printf("webrtc peer=%s state=%s", subID, s.String())
		if s == webrtc.PeerConnectionStateFailed || s == webrtc.PeerConnectionStateClosed {
			p.closePeer(subID)
		}
	})

	offer, err := pc.CreateOffer(nil)
	if err != nil {
		_ = pc.Close()
		return err
	}
	if err := pc.SetLocalDescription(offer); err != nil {
		_ = pc.Close()
		return err
	}

	p.mu.Lock()
	p.peers[subID] = &peerSession{pc: pc, peerID: subID}
	p.mu.Unlock()

	return writeJSON(map[string]any{
		"protocol": 1,
		"type":     "signaling.offer",
		"from":     selfID,
		"to":       subID,
		"sdp":      offer.SDP,
	})
}

func (p *Publisher) handleAnswer(from, sdp string) {
	p.mu.Lock()
	peer := p.peers[from]
	p.mu.Unlock()
	if peer == nil || peer.pc == nil {
		log.Printf("answer from unknown peer %s", from)
		return
	}
	if err := peer.pc.SetRemoteDescription(webrtc.SessionDescription{
		Type: webrtc.SDPTypeAnswer,
		SDP:  sdp,
	}); err != nil {
		log.Printf("set remote answer: %v", err)
	}
}

func (p *Publisher) handleRemoteICE(from string, cand map[string]any) {
	p.mu.Lock()
	peer := p.peers[from]
	p.mu.Unlock()
	if peer == nil || peer.pc == nil || cand == nil {
		return
	}
	b, _ := json.Marshal(cand)
	var init webrtc.ICECandidateInit
	if err := json.Unmarshal(b, &init); err != nil {
		return
	}
	if err := peer.pc.AddICECandidate(init); err != nil {
		log.Printf("add ice: %v", err)
	}
}

func (p *Publisher) closePeer(id string) {
	p.mu.Lock()
	peer := p.peers[id]
	delete(p.peers, id)
	p.mu.Unlock()
	if peer != nil && peer.pc != nil {
		_ = peer.pc.Close()
	}
}

func (p *Publisher) closeAllPeers() {
	p.mu.Lock()
	ids := make([]string, 0, len(p.peers))
	for id := range p.peers {
		ids = append(ids, id)
	}
	p.mu.Unlock()
	for _, id := range ids {
		p.closePeer(id)
	}
}

// BuildSignalingWSURL builds ws://host/ws/signaling/{matchId}.
func BuildSignalingWSURL(platformBase, matchID string) (string, error) {
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
	default:
		return "", fmt.Errorf("unsupported platform scheme %q", u.Scheme)
	}
	u.Path = fmt.Sprintf("/ws/signaling/%s", url.PathEscape(matchID))
	u.RawQuery = ""
	u.Fragment = ""
	return u.String(), nil
}
