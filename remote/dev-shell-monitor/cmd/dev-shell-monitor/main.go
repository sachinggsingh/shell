package main

import (
	"context"
	"flag"
	"log/slog"
	"os"
	"time"

	"dev-shell-monitor/internal/agent"
	"dev-shell-monitor/internal/config"
	applogger "dev-shell-monitor/internal/logger"
	"dev-shell-monitor/internal/server"
	"dev-shell-monitor/internal/stream"
)

func main() {
	configPath := flag.String("config", "", "path to YAML config")
	flag.Parse()

	log := applogger.New()
	cfg, err := config.Load(*configPath)
	if err != nil {
		log.Error("load config", "error", err)
		os.Exit(1)
	}
	log.Info("starting dev-shell-monitor",
		"server_id", cfg.Server.ID,
		"addr", cfg.Addr(),
		"tracing", cfg.Tracing.Enabled,
	)

	seq := &stream.Sequencer{}
	manager := stream.NewManager(cfg.Stream.BufferSize, func(clientID string) {
		log.Warn("dropped event for slow client", "client", clientID)
	})
	ag := agent.New(cfg, log, manager, seq)
	ctx := agent.WaitForShutdown()
	ag.Start(ctx)

	srv := server.New(cfg, log, manager, ag, seq)
	if err := srv.Start(); err != nil {
		log.Error("start server", "error", err)
		os.Exit(1)
	}

	<-ctx.Done()
	log.Info("shutting down")
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := srv.Shutdown(shutdownCtx); err != nil {
		log.Error("shutdown", "error", err)
	}
	slog.Info("stopped")
}
