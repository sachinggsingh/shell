package stream

import (
	"encoding/json"
	"io"
	"time"

	"dev-shell-monitor/internal/model"
)

func Encode(w io.Writer, event model.Event) error {
	type wire struct {
		Type      string          `json:"type"`
		Version   int             `json:"version"`
		Timestamp string          `json:"timestamp"`
		ServerID  string          `json:"server_id"`
		Sequence  uint64          `json:"sequence"`
		Data      json.RawMessage `json:"data"`
	}
	payload := wire{
		Type:      event.Type,
		Version:   event.Version,
		Timestamp: event.Timestamp.UTC().Format(time.RFC3339Nano),
		ServerID:  event.ServerID,
		Sequence:  event.Sequence,
		Data:      event.Data,
	}
	if len(payload.Data) == 0 {
		payload.Data = json.RawMessage("{}")
	}
	enc := json.NewEncoder(w)
	return enc.Encode(payload)
}
