package model

type Log struct {
	Level   string `json:"level"`
	Service string `json:"service"`
	Message string `json:"message"`
	Source  string `json:"source"`
}

type ErrorData struct {
	Component string `json:"component"`
	Message   string `json:"message"`
}
