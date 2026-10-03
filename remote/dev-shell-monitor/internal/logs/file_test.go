package logs

import (
	"context"
	"os"
	"path/filepath"
	"testing"
	"time"

	"dev-shell-monitor/internal/config"
	"dev-shell-monitor/internal/model"
)

func TestReadFileFollowsNewLines(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "app.log")
	if err := os.WriteFile(path, []byte("old\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	got := make(chan model.Log, 4)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	go func() {
		_ = ReadFile(ctx, config.FileSource{Name: "api", Path: path}, func(entry model.Log) {
			got <- entry
		})
	}()
	time.Sleep(200 * time.Millisecond)
	f, err := os.OpenFile(path, os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := f.WriteString("request completed\n"); err != nil {
		t.Fatal(err)
	}
	_ = f.Close()
	select {
	case entry := <-got:
		if entry.Message != "request completed" {
			t.Fatalf("message=%q", entry.Message)
		}
		if entry.Source != "file" || entry.Service != "api" {
			t.Fatalf("%+v", entry)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("did not receive appended log line")
	}
}
