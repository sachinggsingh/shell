package config

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestDefaults(t *testing.T) {
	cfg := Defaults()
	if err := cfg.Validate(); err != nil {
		t.Fatal(err)
	}
	if cfg.Server.Port != 9477 {
		t.Fatalf("expected port 9477, got %d", cfg.Server.Port)
	}
	if cfg.Process.Enabled {
		t.Fatal("process collector should be disabled by default")
	}
	if cfg.Tracing.Enabled {
		t.Fatal("tracing should be disabled by default")
	}
}

func TestLoadAndValidate(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "config.yaml")
	content := []byte("server:\n  id: test\n  bind: 127.0.0.1\n  port: 19477\ncollection:\n  cpu_interval: 2s\n")
	if err := os.WriteFile(path, content, 0o644); err != nil {
		t.Fatal(err)
	}
	cfg, err := Load(path)
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Server.Port != 19477 {
		t.Fatalf("port=%d", cfg.Server.Port)
	}
	if cfg.Collection.CPUInterval != 2*time.Second {
		t.Fatalf("cpu interval=%s", cfg.Collection.CPUInterval)
	}
}

func TestInvalidPort(t *testing.T) {
	cfg := Defaults()
	cfg.Server.Port = 0
	if err := cfg.Validate(); err == nil {
		t.Fatal("expected validation error")
	}
}
