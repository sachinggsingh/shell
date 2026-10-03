package logs

import (
	"context"

	"dev-shell-monitor/internal/config"
	"dev-shell-monitor/internal/model"
	"dev-shell-monitor/internal/stream"
)

type Publisher func(model.Log)

type Reader struct {
	cfg     config.LogsConfig
	host    string
	seq     *stream.Sequencer
	server  string
	publish func(model.Event)
}

func NewReader(cfg config.LogsConfig, serverID string, seq *stream.Sequencer, publish func(model.Event)) *Reader {
	return &Reader{cfg: cfg, server: serverID, seq: seq, publish: publish}
}

func (r *Reader) Start(ctx context.Context) {
	for _, source := range r.cfg.Journal {
		src := source
		go func() {
			err := ReadJournal(ctx, src, func(entry model.Log) {
				event, err := model.NewEvent("log", r.server, r.seq.Next(), entry)
				if err != nil {
					return
				}
				r.publish(event)
			})
			if err != nil {
				return
			}
		}()
	}
	for _, source := range r.cfg.Files {
		src := source
		go func() {
			err := ReadFile(ctx, src, func(entry model.Log) {
				event, err := model.NewEvent("log", r.server, r.seq.Next(), entry)
				if err != nil {
					return
				}
				r.publish(event)
			})
			if err != nil {
				return
			}
		}()
	}
}
