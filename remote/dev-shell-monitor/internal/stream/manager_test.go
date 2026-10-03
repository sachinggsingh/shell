package stream

import (
	"bytes"
	"encoding/json"
	"testing"
	"time"

	"dev-shell-monitor/internal/model"
)

func TestManagerBroadcastAndRemove(t *testing.T) {
	m := NewManager(8, nil)
	a := m.RegisterClient("a")
	b := m.RegisterClient("b")
	if m.ClientCount() != 2 {
		t.Fatalf("count=%d", m.ClientCount())
	}
	event, err := model.NewEvent("heartbeat", "server-1", 1, map[string]any{})
	if err != nil {
		t.Fatal(err)
	}
	m.Broadcast(event)
	select {
	case got := <-a.Events:
		if got.Sequence != 1 {
			t.Fatalf("seq=%d", got.Sequence)
		}
	case <-time.After(time.Second):
		t.Fatal("client a received nothing")
	}
	select {
	case <-b.Events:
	case <-time.After(time.Second):
		t.Fatal("client b received nothing")
	}
	m.RemoveClient("a")
	if m.ClientCount() != 1 {
		t.Fatalf("count=%d", m.ClientCount())
	}
	m.Close()
	if m.ClientCount() != 0 {
		t.Fatal("expected no clients after close")
	}
}

func TestSlowClientDropsOldest(t *testing.T) {
	dropped := 0
	m := NewManager(1, func(string) { dropped++ })
	client := m.RegisterClient("slow")
	first, _ := model.NewEvent("metric", "server-1", 1, map[string]any{"n": 1})
	second, _ := model.NewEvent("metric", "server-1", 2, map[string]any{"n": 2})
	m.Broadcast(first)
	m.Broadcast(second)
	if m.DropCount() == 0 && dropped == 0 {
		// buffer size 1: second broadcast should drop
		t.Fatal("expected a drop for the slow client")
	}
	select {
	case <-client.Events:
	default:
		t.Fatal("expected remaining event")
	}
}

func TestEncoder(t *testing.T) {
	event, _ := model.NewEvent("ready", "server-1", 1, map[string]any{})
	var buf bytes.Buffer
	if err := Encode(&buf, event); err != nil {
		t.Fatal(err)
	}
	var parsed map[string]any
	if err := json.Unmarshal(bytes.TrimSpace(buf.Bytes()), &parsed); err != nil {
		t.Fatal(err)
	}
	if parsed["type"] != "ready" {
		t.Fatalf("%v", parsed)
	}
}

func TestSequencer(t *testing.T) {
	s := &Sequencer{}
	if s.Next() != 1 || s.Next() != 2 {
		t.Fatal("sequence numbers must increment from 1")
	}
}
