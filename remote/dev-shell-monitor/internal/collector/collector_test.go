package collector

import (
	"context"
	"testing"
)

func TestCPUCollector(t *testing.T) {
	c := NewCPUCollector("server-1")
	metrics, err := c.Collect(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if len(metrics) == 0 {
		t.Fatal("expected cpu metrics")
	}
	if metrics[0].Name != "cpu.percent" {
		t.Fatalf("name=%s", metrics[0].Name)
	}
	if metrics[0].Value < 0 || metrics[0].Value > 100 {
		t.Fatalf("percent=%v", metrics[0].Value)
	}
}

func TestMemoryCollector(t *testing.T) {
	c := NewMemoryCollector("server-1")
	metrics, err := c.Collect(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if len(metrics) == 0 {
		t.Fatal("expected memory metrics")
	}
	var total, used float64
	for _, m := range metrics {
		switch m.Name {
		case "memory.total_bytes":
			total = m.Value
		case "memory.used_bytes":
			used = m.Value
		case "memory.percent":
			if m.Value < 0 || m.Value > 100 {
				t.Fatalf("percent=%v", m.Value)
			}
		}
	}
	if total <= 0 {
		t.Fatal("total must be > 0")
	}
	if used < 0 || used > total {
		t.Fatalf("used=%v total=%v", used, total)
	}
}

func TestDiskCollector(t *testing.T) {
	c := NewDiskCollector("server-1", []string{"/"})
	metrics, err := c.Collect(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if len(metrics) == 0 {
		t.Fatal("expected disk metrics")
	}
}

func TestNetworkCollector(t *testing.T) {
	c := NewNetworkCollector("server-1")
	metrics, err := c.Collect(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if len(metrics) == 0 {
		t.Skip("no network interfaces visible in this environment")
	}
}

func TestSystemCollector(t *testing.T) {
	c := NewSystemCollector("server-1")
	metrics, err := c.Collect(context.Background())
	if err != nil {
		t.Skipf("system collector unavailable: %v", err)
	}
	found := false
	for _, m := range metrics {
		if m.Name == "uptime.seconds" {
			found = true
			if m.Value < 0 {
				t.Fatal("uptime must be >= 0")
			}
		}
	}
	if !found && len(metrics) == 0 {
		t.Fatal("expected at least one system metric")
	}
}
