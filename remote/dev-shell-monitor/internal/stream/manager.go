package stream

import (
	"sync"
	"sync/atomic"

	"dev-shell-monitor/internal/model"
)

type Client struct {
	ID     string
	Events chan model.Event
}

type Manager struct {
	mu         sync.RWMutex
	clients    map[string]*Client
	bufferSize int
	drops      atomic.Uint64
	logDrop    func(clientID string)
}

func NewManager(bufferSize int, logDrop func(clientID string)) *Manager {
	if bufferSize < 1 {
		bufferSize = 256
	}
	if logDrop == nil {
		logDrop = func(string) {}
	}
	return &Manager{
		clients:    make(map[string]*Client),
		bufferSize: bufferSize,
		logDrop:    logDrop,
	}
}

func (m *Manager) RegisterClient(id string) *Client {
	client := &Client{
		ID:     id,
		Events: make(chan model.Event, m.bufferSize),
	}
	m.mu.Lock()
	m.clients[id] = client
	m.mu.Unlock()
	return client
}

func (m *Manager) RemoveClient(id string) {
	m.mu.Lock()
	client, ok := m.clients[id]
	if ok {
		delete(m.clients, id)
		close(client.Events)
	}
	m.mu.Unlock()
}

func (m *Manager) ClientCount() int {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return len(m.clients)
}

func (m *Manager) Broadcast(event model.Event) {
	m.mu.RLock()
	clients := make([]*Client, 0, len(m.clients))
	for _, client := range m.clients {
		clients = append(clients, client)
	}
	m.mu.RUnlock()
	for _, client := range clients {
		m.send(client, event)
	}
}

func (m *Manager) send(client *Client, event model.Event) {
	defer func() {
		_ = recover()
	}()
	select {
	case client.Events <- event:
		return
	default:
	}
	select {
	case <-client.Events:
		m.drops.Add(1)
		m.logDrop(client.ID)
	default:
	}
	select {
	case client.Events <- event:
	default:
		m.drops.Add(1)
		m.logDrop(client.ID)
	}
}

func (m *Manager) DropCount() uint64 {
	return m.drops.Load()
}

func (m *Manager) Close() {
	m.mu.Lock()
	defer m.mu.Unlock()
	for id, client := range m.clients {
		close(client.Events)
		delete(m.clients, id)
	}
}
