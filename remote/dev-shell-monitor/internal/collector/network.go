package collector

import (
	"context"
	"strings"

	"github.com/shirou/gopsutil/v4/net"

	"dev-shell-monitor/internal/model"
)

type NetworkCollector struct {
	host string
}

func NewNetworkCollector(host string) *NetworkCollector {
	return &NetworkCollector{host: host}
}

func (c *NetworkCollector) Name() string { return "network" }

func (c *NetworkCollector) Collect(ctx context.Context) ([]model.Metric, error) {
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	default:
	}
	counters, err := net.IOCountersWithContext(ctx, true)
	if err != nil {
		return nil, err
	}
	var metrics []model.Metric
	for _, item := range counters {
		if item.Name == "" || strings.HasPrefix(item.Name, "lo") {
			continue
		}
		labels := map[string]string{"interface": item.Name}
		metrics = append(metrics,
			model.Metric{Name: "network.rx_bytes", Value: float64(item.BytesRecv), Unit: "bytes", Labels: clone(labels)},
			model.Metric{Name: "network.tx_bytes", Value: float64(item.BytesSent), Unit: "bytes", Labels: clone(labels)},
		)
	}
	if len(metrics) == 0 {
		for _, item := range counters {
			labels := map[string]string{"interface": item.Name}
			metrics = append(metrics,
				model.Metric{Name: "network.rx_bytes", Value: float64(item.BytesRecv), Unit: "bytes", Labels: clone(labels)},
				model.Metric{Name: "network.tx_bytes", Value: float64(item.BytesSent), Unit: "bytes", Labels: clone(labels)},
			)
		}
	}
	return withHost(metrics, c.host), nil
}
