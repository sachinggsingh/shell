package server

import (
	"net/http"

	"dev-shell-monitor/internal/config"
)

func (s *Server) Health(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"status":         "ok",
		"version":        "0.1.0",
		"server_id":      s.cfg.Server.ID,
		"uptime_seconds": s.agent.UptimeSeconds(),
		"protocol":       1,
		"bind":           s.cfg.Server.Bind,
	})
}

func HealthPayload(cfg config.Config, uptime int64) map[string]any {
	return map[string]any{
		"status":         "ok",
		"version":        "0.1.0",
		"server_id":      cfg.Server.ID,
		"uptime_seconds": uptime,
	}
}
