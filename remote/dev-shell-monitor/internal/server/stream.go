package server

import (
	"crypto/rand"
	"encoding/hex"
	"net/http"

	"dev-shell-monitor/internal/model"
	"dev-shell-monitor/internal/stream"
)

func (s *Server) Stream(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "streaming unsupported", http.StatusInternalServerError)
		return
	}
	id := newClientID()
	client := s.manager.RegisterClient(id)
	defer s.manager.RemoveClient(id)
	s.log.Info("stream client connected", "client", id)

	w.Header().Set("Content-Type", "application/x-ndjson")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.WriteHeader(http.StatusOK)

	ready, err := model.NewEvent("ready", s.cfg.Server.ID, s.seq.Next(), map[string]any{"client": id})
	if err == nil {
		_ = stream.Encode(w, ready)
		flusher.Flush()
	}

	notify := r.Context().Done()
	for {
		select {
		case <-notify:
			s.log.Info("stream client disconnected", "client", id)
			return
		case event, ok := <-client.Events:
			if !ok {
				return
			}
			if err := stream.Encode(w, event); err != nil {
				s.log.Info("stream write failed", "client", id, "error", err)
				return
			}
			flusher.Flush()
		}
	}
}

func newClientID() string {
	buf := make([]byte, 8)
	_, _ = rand.Read(buf)
	return hex.EncodeToString(buf)
}
