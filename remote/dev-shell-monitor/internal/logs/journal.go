package logs

import (
	"bufio"
	"context"
	"encoding/json"
	"os/exec"
	"strings"

	"dev-shell-monitor/internal/config"
	"dev-shell-monitor/internal/model"
)

func ReadJournal(ctx context.Context, source config.JournalSource, publish func(model.Log)) error {
	if source.Unit == "" {
		return nil
	}
	cmd := exec.CommandContext(ctx, "journalctl", "-u", source.Unit, "-f", "-n", "0", "-o", "json")
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return err
	}
	if err := cmd.Start(); err != nil {
		return err
	}
	scanner := bufio.NewScanner(stdout)
	if scanner.Err() != nil {
		return scanner.Err()
	}
	scanner.Buffer(make([]byte, 0, 64*1024), 1024*1024)
	for scanner.Scan() {
		select {
		case <-ctx.Done():
			_ = cmd.Process.Kill()
			return ctx.Err()
		default:
		}
		line := scanner.Bytes()
		var raw map[string]any
		if err := json.Unmarshal(line, &raw); err != nil {
			continue
		}
		message, _ := raw["MESSAGE"].(string)
		priority := "INFO"
		if p, ok := raw["PRIORITY"].(string); ok {
			priority = journalPriority(p)
		}
		publish(model.Log{
			Level:   priority,
			Service: source.Unit,
			Message: message,
			Source:  "journal",
		})
	}
	return cmd.Wait()
}

func journalPriority(value string) string {
	switch strings.TrimSpace(value) {
	case "0", "1", "2", "3":
		return "ERROR"
	case "4":
		return "WARN"
	case "7":
		return "DEBUG"
	default:
		return "INFO"
	}
}
