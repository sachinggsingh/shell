package collector

import (
	"context"
	"fmt"

	"github.com/shirou/gopsutil/v4/host"
	"github.com/shirou/gopsutil/v4/load"

	"dev-shell-monitor/internal/model"
)

type SystemCollector struct {
	host string
}

func NewSystemCollector(host string) *SystemCollector {
	return &SystemCollector{host: host}
}

func (c *SystemCollector) Name() string { return "system" }

func (c *SystemCollector) Collect(ctx context.Context) ([]model.Metric, error) {
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	default:
	}
	metrics := make([]model.Metric, 0, 4)
	if avg, err := load.AvgWithContext(ctx); err == nil {
		metrics = append(metrics,
			model.Metric{Name: "load.1", Value: avg.Load1, Unit: "load"},
			model.Metric{Name: "load.5", Value: avg.Load5, Unit: "load"},
			model.Metric{Name: "load.15", Value: avg.Load15, Unit: "load"},
		)
	}
	if uptime, err := host.UptimeWithContext(ctx); err == nil {
		metrics = append(metrics, model.Metric{Name: "uptime.seconds", Value: float64(uptime), Unit: "seconds"})
	}
	if len(metrics) == 0 {
		return nil, fmt.Errorf("system collector unavailable")
	}
	return withHost(metrics, c.host), nil
}
