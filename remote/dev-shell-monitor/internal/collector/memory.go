package collector

import (
	"context"

	"github.com/shirou/gopsutil/v4/mem"

	"dev-shell-monitor/internal/model"
)

type MemoryCollector struct {
	host string
}

func NewMemoryCollector(host string) *MemoryCollector {
	return &MemoryCollector{host: host}
}

func (c *MemoryCollector) Name() string { return "memory" }

func (c *MemoryCollector) Collect(ctx context.Context) ([]model.Metric, error) {
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	default:
	}
	stat, err := mem.VirtualMemoryWithContext(ctx)
	if err != nil {
		return nil, err
	}
	return withHost([]model.Metric{
		{Name: "memory.total_bytes", Value: float64(stat.Total), Unit: "bytes"},
		{Name: "memory.used_bytes", Value: float64(stat.Used), Unit: "bytes"},
		{Name: "memory.available_bytes", Value: float64(stat.Available), Unit: "bytes"},
		{Name: "memory.percent", Value: stat.UsedPercent, Unit: "percent"},
	}, c.host), nil
}
