package collector

import (
	"context"

	"dev-shell-monitor/internal/model"
)

type Collector interface {
	Name() string
	Collect(ctx context.Context) ([]model.Metric, error)
}

func withHost(metrics []model.Metric, host string) []model.Metric {
	for i := range metrics {
		if metrics[i].Labels == nil {
			metrics[i].Labels = map[string]string{}
		}
		if _, ok := metrics[i].Labels["host"]; !ok {
			metrics[i].Labels["host"] = host
		}
	}
	return metrics
}
