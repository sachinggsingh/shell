package stream

import "dev-shell-monitor/internal/model"

func BroadcastAll(manager *Manager, event model.Event) {
	manager.Broadcast(event)
}
