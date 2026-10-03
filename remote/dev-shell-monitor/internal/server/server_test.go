package server

import (
	"bufio"
	"context"
	"encoding/json"
	"io"
	"log/slog"
	"net"
	"net/http"
	"testing"
	"time"

	"dev-shell-monitor/internal/agent"
	"dev-shell-monitor/internal/config"
	"dev-shell-monitor/internal/stream"
)

func TestHealthAndStream(t *testing.T) {
	cfg := config.Defaults()
	cfg.Collection.CPUInterval = 50 * time.Millisecond
	cfg.Collection.MemoryInterval = time.Hour
	cfg.Collection.DiskInterval = time.Hour
	cfg.Collection.NetworkInterval = time.Hour
	cfg.Collection.SystemInterval = time.Hour
	cfg.Stream.HeartbeatInterval = 80 * time.Millisecond

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	addr := ln.Addr().String()
	log := slog.New(slog.NewTextHandler(io.Discard, nil))
	seq := &stream.Sequencer{}
	manager := stream.NewManager(64, nil)
	ag := agent.New(cfg, log, manager, seq)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	ag.Start(ctx)
	srv := New(cfg, log, manager, ag, seq)
	go func() {
		_ = srv.http.Serve(ln)
	}()
	t.Cleanup(func() {
		shutdownCtx, c := context.WithTimeout(context.Background(), 2*time.Second)
		defer c()
		_ = srv.Shutdown(shutdownCtx)
	})

	resp, err := http.Get("http://" + addr + "/health")
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		t.Fatalf("status=%d", resp.StatusCode)
	}
	var health map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&health); err != nil {
		t.Fatal(err)
	}
	if health["status"] != "ok" {
		t.Fatalf("%v", health)
	}

	streamResp, err := http.Get("http://" + addr + "/stream")
	if err != nil {
		t.Fatal(err)
	}
	defer streamResp.Body.Close()
	scanner := bufio.NewScanner(streamResp.Body)
	if scanner.Err() != nil {
		t.Fatal(scanner.Err())
	}
	seen := map[string]bool{}
	deadline := time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) {
		if !scanner.Scan() {
			t.Fatal("stream ended early")
		}
		var event map[string]any
		if err := json.Unmarshal(scanner.Bytes(), &event); err != nil {
			t.Fatal(err)
		}
		typ, _ := event["type"].(string)
		seen[typ] = true
		if seen["ready"] && seen["heartbeat"] && seen["metric"] {
			return
		}
	}
	t.Fatalf("missing events, seen=%v", seen)
}
