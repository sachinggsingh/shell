package config

import (
	"fmt"
	"os"
	"time"

	"gopkg.in/yaml.v3"
)

type Config struct {
	Server     ServerConfig     `yaml:"server"`
	Collection CollectionConfig `yaml:"collection"`
	Process    ProcessConfig    `yaml:"process"`
	Stream     StreamConfig     `yaml:"stream"`
	Logs       LogsConfig       `yaml:"logs"`
	Tracing    TracingConfig    `yaml:"tracing"`
}

type ServerConfig struct {
	ID   string `yaml:"id"`
	Bind string `yaml:"bind"`
	Port int    `yaml:"port"`
}

type CollectionConfig struct {
	CPUInterval     time.Duration `yaml:"cpu_interval"`
	MemoryInterval  time.Duration `yaml:"memory_interval"`
	DiskInterval    time.Duration `yaml:"disk_interval"`
	NetworkInterval time.Duration `yaml:"network_interval"`
	SystemInterval  time.Duration `yaml:"system_interval"`
	DiskPaths       []string      `yaml:"disk_paths"`
}

type ProcessConfig struct {
	Enabled  bool          `yaml:"enabled"`
	Interval time.Duration `yaml:"interval"`
	TopN     int           `yaml:"top_n"`
}

type StreamConfig struct {
	BufferSize        int           `yaml:"buffer_size"`
	HeartbeatInterval time.Duration `yaml:"heartbeat_interval"`
}

type LogsConfig struct {
	Journal []JournalSource `yaml:"journal"`
	Files   []FileSource    `yaml:"files"`
}

type JournalSource struct {
	Unit string `yaml:"unit"`
}

type FileSource struct {
	Name string `yaml:"name"`
	Path string `yaml:"path"`
}

type TracingConfig struct {
	Enabled      bool   `yaml:"enabled"`
	OTLPEndpoint string `yaml:"otlp_endpoint"`
	ServiceName  string `yaml:"service_name"`
}

func Defaults() Config {
	return Config{
		Server: ServerConfig{ID: "server-1", Bind: "127.0.0.1", Port: 9477},
		Collection: CollectionConfig{
			CPUInterval:     time.Second,
			MemoryInterval:  2 * time.Second,
			DiskInterval:    5 * time.Second,
			NetworkInterval: 2 * time.Second,
			SystemInterval:  10 * time.Second,
			DiskPaths:       []string{"/"},
		},
		Process: ProcessConfig{Enabled: false, Interval: 5 * time.Second, TopN: 10},
		Stream:  StreamConfig{BufferSize: 256, HeartbeatInterval: 5 * time.Second},
		Logs:    LogsConfig{Journal: []JournalSource{}, Files: []FileSource{}},
		Tracing: TracingConfig{Enabled: false, ServiceName: "dev-shell-monitor"},
	}
}

func Load(path string) (Config, error) {
	cfg := Defaults()
	if path == "" {
		return cfg, nil
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return Config{}, fmt.Errorf("config: read %s: %w", path, err)
	}
	if err := yaml.Unmarshal(raw, &cfg); err != nil {
		return Config{}, fmt.Errorf("config: parse %s: %w", path, err)
	}
	if err := cfg.Validate(); err != nil {
		return Config{}, err
	}
	return cfg, nil
}

func (c Config) Validate() error {
	if c.Server.Bind == "" {
		return fmt.Errorf("config: server.bind is required")
	}
	if c.Server.Port < 1 || c.Server.Port > 65535 {
		return fmt.Errorf("config: server.port must be between 1 and 65535")
	}
	if c.Server.ID == "" {
		return fmt.Errorf("config: server.id is required")
	}
	if c.Stream.BufferSize < 1 {
		return fmt.Errorf("config: stream.buffer_size must be >= 1")
	}
	return nil
}

func (c Config) Addr() string {
	return fmt.Sprintf("%s:%d", c.Server.Bind, c.Server.Port)
}
