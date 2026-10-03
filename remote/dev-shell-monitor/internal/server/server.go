package server

import (
	"context"
	"encoding/json"
	"log/slog"
	"net"
	"net/http"
	"time"

	"dev-shell-monitor/internal/agent"
	"dev-shell-monitor/internal/config"
	"dev-shell-monitor/internal/stream"
)

type Server struct {
	cfg     config.Config
	log     *slog.Logger
	manager *stream.Manager
	agent   *agent.Agent
	seq     *stream.Sequencer
	http    *http.Server
}

func New(cfg config.Config, log *slog.Logger, manager *stream.Manager, ag *agent.Agent, seq *stream.Sequencer) *Server {
	s := &Server{cfg: cfg, log: log, manager: manager, agent: ag, seq: seq}
	mux := http.NewServeMux()
	mux.HandleFunc("/health", s.Health)
	mux.HandleFunc("/stream", s.Stream)
	s.http = &http.Server{
		Addr:              cfg.Addr(),
		Handler:           mux,
		ReadHeaderTimeout: 5 * time.Second,
	}
	return s
}

func (s *Server) Start() error {
	ln, err := net.Listen("tcp", s.cfg.Addr())
	if err != nil {
		return err
	}
	s.log.Info("monitoring server listening", "addr", s.cfg.Addr())
	go func() {
		if err := s.http.Serve(ln); err != nil && err != http.ErrServerClosed {
			s.log.Error("http server error", "error", err)
		}
	}()
	return nil
}

func (s *Server) Shutdown(ctx context.Context) error {
	s.manager.Close()
	return s.http.Shutdown(ctx)
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}
