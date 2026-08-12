package obs

import (
	"context"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"sync/atomic"
	"time"

	"github.com/gorilla/websocket"
)

// Client is a minimal OBS WebSocket protocol 5 controller.
type Client struct {
	url      string
	password string

	mu   sync.Mutex
	conn *websocket.Conn
	req  atomic.Uint64
	wait map[string]chan rpcResult
}

type rpcResult struct {
	ok     bool
	errMsg string
	data   json.RawMessage
}

func NewClient(url, password string) *Client {
	if url == "" {
		url = "ws://127.0.0.1:4455"
	}
	return &Client{
		url:      url,
		password: password,
		wait:     make(map[string]chan rpcResult),
	}
}

func (c *Client) Connect(ctx context.Context) error {
	dialer := websocket.Dialer{HandshakeTimeout: 10 * time.Second}
	conn, _, err := dialer.DialContext(ctx, c.url, http.Header{})
	if err != nil {
		return fmt.Errorf("obs dial: %w", err)
	}

	_ = conn.SetReadDeadline(time.Now().Add(10 * time.Second))
	var hello struct {
		Op int `json:"op"`
		D  struct {
			Authentication *struct {
				Challenge string `json:"challenge"`
				Salt      string `json:"salt"`
			} `json:"authentication"`
		} `json:"d"`
	}
	if err := conn.ReadJSON(&hello); err != nil {
		_ = conn.Close()
		return fmt.Errorf("obs hello: %w", err)
	}
	if hello.Op != 0 {
		_ = conn.Close()
		return fmt.Errorf("obs expected Hello op=0 got %d", hello.Op)
	}

	identifyD := map[string]any{"rpcVersion": 1}
	if hello.D.Authentication != nil && c.password != "" {
		secret := sha256.Sum256([]byte(c.password + hello.D.Authentication.Salt))
		secretB64 := base64.StdEncoding.EncodeToString(secret[:])
		auth := sha256.Sum256([]byte(secretB64 + hello.D.Authentication.Challenge))
		identifyD["authentication"] = base64.StdEncoding.EncodeToString(auth[:])
	}
	if err := conn.WriteJSON(map[string]any{"op": 1, "d": identifyD}); err != nil {
		_ = conn.Close()
		return err
	}

	var identified struct {
		Op int `json:"op"`
	}
	if err := conn.ReadJSON(&identified); err != nil {
		_ = conn.Close()
		return fmt.Errorf("obs identified: %w", err)
	}
	if identified.Op != 2 {
		_ = conn.Close()
		return fmt.Errorf("obs expected Identified op=2 got %d", identified.Op)
	}
	_ = conn.SetReadDeadline(time.Time{})

	c.mu.Lock()
	c.conn = conn
	c.mu.Unlock()
	go c.readLoop()
	return nil
}

func (c *Client) Close() error {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.conn == nil {
		return nil
	}
	err := c.conn.Close()
	c.conn = nil
	return err
}

func (c *Client) Status() string {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.conn == nil {
		return "disconnected"
	}
	return "connected"
}

func (c *Client) GetCurrentProgramScene(ctx context.Context) (string, error) {
	raw, err := c.request(ctx, "GetCurrentProgramScene", nil)
	if err != nil {
		return "", err
	}
	var out struct {
		CurrentProgramSceneName string `json:"currentProgramSceneName"`
	}
	if err := json.Unmarshal(raw, &out); err != nil {
		return "", err
	}
	return out.CurrentProgramSceneName, nil
}

func (c *Client) SetCurrentProgramScene(ctx context.Context, scene string) error {
	_, err := c.request(ctx, "SetCurrentProgramScene", map[string]any{
		"sceneName": scene,
	})
	return err
}

func (c *Client) request(ctx context.Context, reqType string, data map[string]any) (json.RawMessage, error) {
	id := fmt.Sprintf("stk-%d", c.req.Add(1))
	ch := make(chan rpcResult, 1)
	c.mu.Lock()
	c.wait[id] = ch
	conn := c.conn
	c.mu.Unlock()
	if conn == nil {
		return nil, fmt.Errorf("obs not connected")
	}
	defer func() {
		c.mu.Lock()
		delete(c.wait, id)
		c.mu.Unlock()
	}()

	payload := map[string]any{
		"op": 6,
		"d": map[string]any{
			"requestType": reqType,
			"requestId":   id,
			"requestData": data,
		},
	}
	c.mu.Lock()
	err := c.conn.WriteJSON(payload)
	c.mu.Unlock()
	if err != nil {
		return nil, err
	}
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	case res := <-ch:
		if !res.ok {
			return nil, fmt.Errorf("obs %s: %s", reqType, res.errMsg)
		}
		return res.data, nil
	case <-time.After(10 * time.Second):
		return nil, fmt.Errorf("obs %s: timeout", reqType)
	}
}

func (c *Client) readLoop() {
	for {
		c.mu.Lock()
		conn := c.conn
		c.mu.Unlock()
		if conn == nil {
			return
		}
		var envelope struct {
			Op int             `json:"op"`
			D  json.RawMessage `json:"d"`
		}
		if err := conn.ReadJSON(&envelope); err != nil {
			return
		}
		if envelope.Op != 7 {
			continue
		}
		var resp struct {
			RequestID     string `json:"requestId"`
			RequestStatus struct {
				Result  bool   `json:"result"`
				Comment string `json:"comment"`
			} `json:"requestStatus"`
			ResponseData json.RawMessage `json:"responseData"`
		}
		if err := json.Unmarshal(envelope.D, &resp); err != nil {
			continue
		}
		c.mu.Lock()
		ch := c.wait[resp.RequestID]
		c.mu.Unlock()
		if ch == nil {
			continue
		}
		ch <- rpcResult{
			ok:     resp.RequestStatus.Result,
			errMsg: resp.RequestStatus.Comment,
			data:   resp.ResponseData,
		}
	}
}
