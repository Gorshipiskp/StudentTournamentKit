package webrtcpub

import (
	"embed"
	"fmt"
	"io"
	"os"
	"path/filepath"
)

//go:embed testdata/pattern.ivf
var embeddedIVF embed.FS

// DefaultIVFPath returns a filesystem path to the embedded pattern IVF
// (written to a temp file once if needed).
func DefaultIVFPath() (string, error) {
	data, err := embeddedIVF.ReadFile("testdata/pattern.ivf")
	if err != nil {
		return "", err
	}
	dir := filepath.Join(os.TempDir(), "stk-director-agent")
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return "", err
	}
	path := filepath.Join(dir, "pattern.ivf")
	if err := os.WriteFile(path, data, 0o644); err != nil {
		return "", err
	}
	return path, nil
}

func openIVF(path string) (io.ReadCloser, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open ivf %s: %w", path, err)
	}
	return f, nil
}
