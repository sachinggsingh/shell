package model

import (
	"encoding/json"
	"time"
)

const ProtocolVersion = 1

type Event struct {
	Type      string          `json:"type"`
	Version   int             `json:"version"`
	Timestamp time.Time       `json:"timestamp"`
	ServerID  string          `json:"server_id"`
	Sequence  uint64          `json:"sequence"`
	Data      json.RawMessage `json:"data"`
}

func NewEvent(eventType, serverID string, sequence uint64, data any) (Event, error) {
	payload, err := json.Marshal(data)
	if err != nil {
		return Event{}, err
	}
	if payload == nil {
		payload = []byte("{}")
	}
	return Event{
		Type:      eventType,
		Version:   ProtocolVersion,
		Timestamp: time.Now().UTC(),
		ServerID:  serverID,
		Sequence:  sequence,
		Data:      payload,
	}, nil
}
