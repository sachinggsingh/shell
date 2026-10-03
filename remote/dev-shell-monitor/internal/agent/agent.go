package agent

import (
	"context"
	"log/slog"
	"sync"
	"time"

	"dev-shell-monitor/internal/collector"
	"dev-shell-monitor/internal/config"
	"dev-shell-monitor/internal/logs"
	"dev-shell-monitor/internal/model"
	"dev-shell-monitor/internal/stream"
)

type Agent struct {
	cfg     config.Config
	log     *slog.Logger
	manager *stream.Manager
	seq     *stream.Sequencer
	started time.Time
}

func New(cfg config.Config, log *slog.Logger, manager *stream.Manager, seq *stream.Sequencer) *Agent {
	return &Agent{cfg: cfg, log: log, manager: manager, seq: seq, started: time.Now()}
}

func (a *Agent) Started() time.Time { return a.started }

func (a *Agent) UptimeSeconds() int64 {
	return int64(time.Since(a.started).Seconds())
}

func (a *Agent) Publish(event model.Event) {
	a.manager.Broadcast(event)
}

func (a *Agent) emitMetrics(name string, metrics []model.Metric) {
	for _, metric := range metrics {
		event, err := model.NewEvent("metric", a.cfg.Server.ID, a.seq.Next(), metric)
		if err != nil {
			a.log.Error("encode metric event", "collector", name, "error", err)
			continue
		}
		a.Publish(event)
	}
}

func (a *Agent) emitError(component, message string) {
	event, err := model.NewEvent("error", a.cfg.Server.ID, a.seq.Next(), model.ErrorData{
		Component: component,
		Message:   message,
	})
	if err != nil {
		return
	}
	a.Publish(event)
}

func (a *Agent) schedule(ctx context.Context, col collector.Collector, interval time.Duration, wg *sync.WaitGroup) {
	wg.Add(1)
	go func() {
		defer wg.Done()
		ticker := time.NewTicker(interval)
		defer ticker.Stop()
		a.runCollector(ctx, col)
		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				a.runCollector(ctx, col)
			}
		}
	}()
}

func (a *Agent) runCollector(ctx context.Context, col collector.Collector) {
	metrics, err := col.Collect(ctx)
	if err != nil {
		a.log.Error("collector failed", "collector", col.Name(), "error", err)
		a.emitError(col.Name(), err.Error())
		return
	}
	a.emitMetrics(col.Name(), metrics)
}

func (a *Agent) Start(ctx context.Context) {
	var wg sync.WaitGroup
	host := a.cfg.Server.ID
	a.schedule(ctx, collector.NewCPUCollector(host), a.cfg.Collection.CPUInterval, &wg)
	a.schedule(ctx, collector.NewMemoryCollector(host), a.cfg.Collection.MemoryInterval, &wg)
	a.schedule(ctx, collector.NewDiskCollector(host, a.cfg.Collection.DiskPaths), a.cfg.Collection.DiskInterval, &wg)
	a.schedule(ctx, collector.NewNetworkCollector(host), a.cfg.Collection.NetworkInterval, &wg)
	a.schedule(ctx, collector.NewSystemCollector(host), a.cfg.Collection.SystemInterval, &wg)
	if a.cfg.Process.Enabled {
		a.schedule(ctx, collector.NewProcessCollector(host, a.cfg.Process.TopN), a.cfg.Process.Interval, &wg)
	}
	logs.NewReader(a.cfg.Logs, a.cfg.Server.ID, a.seq, a.Publish).Start(ctx)
	a.startHeartbeat(ctx, &wg)
	go func() {
		<-ctx.Done()
		wg.Wait()
	}()
}

func (a *Agent) startHeartbeat(ctx context.Context, wg *sync.WaitGroup) {
	wg.Add(1)
	go func() {
		defer wg.Done()
		interval := a.cfg.Stream.HeartbeatInterval
		if interval <= 0 {
			interval = 5 * time.Second
		}
		ticker := time.NewTicker(interval)
		defer ticker.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				event, err := model.NewEvent("heartbeat", a.cfg.Server.ID, a.seq.Next(), map[string]any{})
				if err != nil {
					continue
				}
				a.Publish(event)
			}
		}
	}()
}
