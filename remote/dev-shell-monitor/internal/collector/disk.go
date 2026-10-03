package collector

import (
	"context"

	"github.com/shirou/gopsutil/v4/disk"

	"dev-shell-monitor/internal/model"
)

type DiskCollector struct {
	host  string
	paths []string
}

func NewDiskCollector(host string, paths []string) *DiskCollector {
	if len(paths) == 0 {
		paths = []string{"/"}
	}
	return &DiskCollector{host: host, paths: paths}
}

func (c *DiskCollector) Name() string { return "disk" }

func (c *DiskCollector) Collect(ctx context.Context) ([]model.Metric, error) {
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	default:
	}
	var metrics []model.Metric
	for _, path := range c.paths {
		usage, err := disk.UsageWithContext(ctx, path)
		if err != nil {
			return nil, err
		}
		labels := map[string]string{"path": path}
		metrics = append(metrics,
			model.Metric{Name: "disk.total_bytes", Value: float64(usage.Total), Unit: "bytes", Labels: clone(labels)},
			model.Metric{Name: "disk.used_bytes", Value: float64(usage.Used), Unit: "bytes", Labels: clone(labels)},
			model.Metric{Name: "disk.available_bytes", Value: float64(usage.Free), Unit: "bytes", Labels: clone(labels)},
			model.Metric{Name: "disk.percent", Value: usage.UsedPercent, Unit: "percent", Labels: clone(labels)},
		)
	}
	return withHost(metrics, c.host), nil
}

func clone(in map[string]string) map[string]string {
	out := make(map[string]string, len(in))
	for k, v := range in {
		out[k] = v
	}
	return out
}
