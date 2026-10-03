package collector

import (
	"context"
	"time"

	"github.com/shirou/gopsutil/v4/cpu"

	"dev-shell-monitor/internal/model"
)

type CPUCollector struct {
	host string
}

func NewCPUCollector(host string) *CPUCollector {
	return &CPUCollector{host: host}
}

func (c *CPUCollector) Name() string { return "cpu" }

func (c *CPUCollector) Collect(ctx context.Context) ([]model.Metric, error) {
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	default:
	}
	percents, err := cpu.PercentWithContext(ctx, 200*time.Millisecond, false)
	if err != nil {
		return nil, err
	}
	value := 0.0
	if len(percents) > 0 {
		value = percents[0]
	}
	return withHost([]model.Metric{{
		Name:  "cpu.percent",
		Value: value,
		Unit:  "percent",
	}}, c.host), nil
}
