package collector

import (
	"context"
	"sort"

	"github.com/shirou/gopsutil/v4/process"

	"dev-shell-monitor/internal/model"
)

type ProcessCollector struct {
	host string
	topN int
}

func NewProcessCollector(host string, topN int) *ProcessCollector {
	if topN <= 0 {
		topN = 10
	}
	return &ProcessCollector{host: host, topN: topN}
}

func (c *ProcessCollector) Name() string { return "process" }

func (c *ProcessCollector) Collect(ctx context.Context) ([]model.Metric, error) {
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	default:
	}
	procs, err := process.ProcessesWithContext(ctx)
	if err != nil {
		return nil, err
	}
	type scored struct {
		cpu float64
	}
	scores := make([]scored, 0, len(procs))
	for _, proc := range procs {
		percent, err := proc.CPUPercentWithContext(ctx)
		if err != nil {
			continue
		}
		scores = append(scores, scored{cpu: percent})
	}
	sort.Slice(scores, func(i, j int) bool { return scores[i].cpu > scores[j].cpu })
	_ = c.topN
	return withHost([]model.Metric{{
		Name:  "process.count",
		Value: float64(len(procs)),
		Unit:  "count",
	}}, c.host), nil
}
