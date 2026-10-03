.PHONY: help setup venv install build test test-python test-go lint \
	run agent agent-start agent-stop agent-restart agent-status \
	health stream wait-health cli \
	shell help-cli add-local servers sources connect watch dashboard traces \
	demo clean \
	install-server update-server uninstall-server server-health ssh-check

ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
GO_DIR := $(ROOT)/remote/dev-shell-monitor
AGENT_CONFIG := $(GO_DIR)/configs/dev-shell-monitor.example.yaml
BIN := $(ROOT)/dist/dev-shell-monitor
VENV := $(ROOT)/.venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
CLIENT_CONFIG := $(ROOT)/.dev-shell-client.json
PID_FILE := $(ROOT)/.dev-shell-monitor.pid
LOG_FILE := $(ROOT)/.dev-shell-monitor.log
HEALTH_URL := http://127.0.0.1:9477/health
STREAM_URL := http://127.0.0.1:9477/stream
SERVER ?= local
HOST ?= 127.0.0.1
USER ?= devshell
SSH_PORT ?= 22
MONITOR_PORT ?= 9477
IDENTITY_FILE ?=
DIRECT ?= true
CMD ?= help

.DEFAULT_GOAL := help

## help: Show this list
help:
	@printf '%s\n' "dev_shell Make targets"
	@printf '%s\n' ""
	@printf '%s\n' "Setup"
	@printf '%s\n' "  make setup             Create venv, install Python package, fetch Go modules"
	@printf '%s\n' "  make build             Build dist/dev-shell-monitor"
	@printf '%s\n' ""
	@printf '%s\n' "Run locally"
	@printf '%s\n' "  make run               setup + build + start agent + register local server"
	@printf '%s\n' "  make demo              run, then watch live metrics (Ctrl+C to stop the view)"
	@printf '%s\n' "  make agent             Start the Go agent in the background"
	@printf '%s\n' "  make agent-stop        Stop the background agent"
	@printf '%s\n' "  make agent-restart     Restart the agent"
	@printf '%s\n' "  make agent-status      Show whether the agent is listening"
	@printf '%s\n' "  make health            GET /health"
	@printf '%s\n' "  make stream            Print a few /stream events"
	@printf '%s\n' "  make shell             Interactive Python CLI"
	@printf '%s\n' ""
	@printf '%s\n' "CLI (uses .dev-shell-client.json)"
	@printf '%s\n' "  make help-cli          List CLI commands"
	@printf '%s\n' "  make add-local         Register SERVER=$(SERVER) (direct=$(DIRECT))"
	@printf '%s\n' "  make servers           List registered servers"
	@printf '%s\n' "  make sources           Show monitor sources for SERVER"
	@printf '%s\n' "  make connect           monitor connect SERVER"
	@printf '%s\n' "  make watch             watch-server SERVER (live view)"
	@printf '%s\n' "  make dashboard         Same as watch"
	@printf '%s\n' "  make traces            monitor traces SERVER"
	@printf '%s\n' "  make CMD='sysinfo' cli Run an arbitrary CLI command"
	@printf '%s\n' ""
	@printf '%s\n' "Tests"
	@printf '%s\n' "  make test              Python + Go tests"
	@printf '%s\n' "  make test-python"
	@printf '%s\n' "  make test-go"
	@printf '%s\n' "  make lint              shellcheck when installed"
	@printf '%s\n' ""
	@printf '%s\n' "Remote systemd (root, Linux)"
	@printf '%s\n' "  make install-server    Install binary + unit + start service"
	@printf '%s\n' "  make update-server     Replace the installed binary"
	@printf '%s\n' "  make uninstall-server  Stop and remove the service"
	@printf '%s\n' "  make server-health     scripts/health-check.sh"
	@printf '%s\n' "  make ssh-check HOST=... USER=... [SSH_PORT=22]"
	@printf '%s\n' ""
	@printf '%s\n' "  make clean             Stop agent and remove venv/build artifacts"
	@printf '%s\n' ""
	@printf '%s\n' "Typical first run:  make run && make watch"

## setup: Python venv + editable install + Go modules
setup: venv install
	cd "$(GO_DIR)" && go mod download

venv:
	@if [ ! -x "$(PYTHON)" ]; then python3 -m venv "$(VENV)"; fi

install: venv
	"$(PIP)" install -e ".[dev]"

## build: Compile the Go monitoring agent
build:
	mkdir -p "$(ROOT)/dist"
	cd "$(GO_DIR)" && go build -o "$(BIN)" ./cmd/dev-shell-monitor
	@echo "built $(BIN)"

## run: Prepare the local stack and start the agent
run: setup build agent-start wait-health add-local
	@printf '%s\n' ""
	@printf '%s\n' "Agent is up at $(HEALTH_URL)"
	@printf '%s\n' "CLI config: $(CLIENT_CONFIG)"
	@printf '%s\n' ""
	@printf '%s\n' "Next:"
	@printf '%s\n' "  make health"
	@printf '%s\n' "  make stream"
	@printf '%s\n' "  make watch"
	@printf '%s\n' "  make shell"

## demo: Start everything and open the live dashboard
demo: run watch

agent: agent-start

## agent-start: Run dist/dev-shell-monitor in the background
agent-start: build
	@if [ -f "$(PID_FILE)" ] && kill -0 $$(cat "$(PID_FILE)") 2>/dev/null; then \
		echo "agent already running pid=$$(cat "$(PID_FILE)")"; \
	else \
		rm -f "$(PID_FILE)"; \
		"$(BIN)" --config "$(AGENT_CONFIG)" >"$(LOG_FILE)" 2>&1 & echo $$! >"$(PID_FILE)"; \
		echo "started agent pid=$$(cat "$(PID_FILE)") log=$(LOG_FILE)"; \
	fi

## agent-stop: Stop the background agent
agent-stop:
	@if [ -f "$(PID_FILE)" ]; then \
		pid=$$(cat "$(PID_FILE)"); \
		if kill -0 $$pid 2>/dev/null; then kill $$pid; sleep 0.3; fi; \
		if kill -0 $$pid 2>/dev/null; then kill -9 $$pid; fi; \
		rm -f "$(PID_FILE)"; \
		echo "stopped agent pid=$$pid"; \
	else \
		echo "agent is not running (no pid file)"; \
	fi
	@-pkill -f '$(BIN)' >/dev/null 2>&1 || true

agent-restart: agent-stop agent-start wait-health

agent-status:
	@if curl --fail --silent --max-time 1 "$(HEALTH_URL)" >/dev/null; then \
		echo "agent is healthy at $(HEALTH_URL)"; \
		curl --fail --silent "$(HEALTH_URL)"; echo; \
	else \
		echo "agent is not reachable at $(HEALTH_URL)"; \
		exit 1; \
	fi

wait-health:
	@i=0; \
	while [ $$i -lt 40 ]; do \
		if curl --fail --silent --max-time 1 "$(HEALTH_URL)" >/dev/null; then \
			echo "health ok"; \
			exit 0; \
		fi; \
		i=$$((i + 1)); \
		sleep 0.25; \
	done; \
	echo "health failed: $(HEALTH_URL) did not become ready"; \
	if [ -f "$(LOG_FILE)" ]; then tail -n 40 "$(LOG_FILE)"; fi; \
	exit 1

## health: Check GET /health
health:
	curl --fail --silent "$(HEALTH_URL)"
	@echo

## stream: Read a few NDJSON events from GET /stream
stream:
	curl -N --silent --max-time 4 "$(STREAM_URL)" | sed -n '1,20p'

cli: setup
	"$(PYTHON)" -m dev_shell --config "$(CLIENT_CONFIG)" -- $(CMD)

## shell: Interactive CLI
shell: setup
	"$(PYTHON)" -m dev_shell --config "$(CLIENT_CONFIG)"

help-cli: setup
	"$(PYTHON)" -m dev_shell --config "$(CLIENT_CONFIG)" -- help

add-local: setup
	@if [ "$(DIRECT)" = "true" ]; then extra="direct=true"; else extra=""; fi; \
	identity=""; \
	if [ -n "$(IDENTITY_FILE)" ]; then identity="identity_file=$(IDENTITY_FILE)"; fi; \
	"$(PYTHON)" -m dev_shell --config "$(CLIENT_CONFIG)" -- add-server \
		name=$(SERVER) host=$(HOST) user=$(USER) \
		ssh_port=$(SSH_PORT) monitor_port=$(MONITOR_PORT) $$identity $$extra

servers: setup
	"$(PYTHON)" -m dev_shell --config "$(CLIENT_CONFIG)" -- servers

sources: setup
	"$(PYTHON)" -m dev_shell --config "$(CLIENT_CONFIG)" -- monitor sources $(SERVER)

connect: setup
	"$(PYTHON)" -m dev_shell --config "$(CLIENT_CONFIG)" -- monitor connect $(SERVER)

watch: setup
	"$(PYTHON)" -m dev_shell --config "$(CLIENT_CONFIG)" -- watch-server $(SERVER)

dashboard: watch

traces: setup
	"$(PYTHON)" -m dev_shell --config "$(CLIENT_CONFIG)" -- monitor traces $(SERVER)

test: test-python test-go

test-python: setup
	"$(PYTEST)" tests

test-go:
	cd "$(GO_DIR)" && go test ./...

lint:
	"$(ROOT)/scripts/dev/lint.sh"

install-server: build
	BINARY_SRC="$(BIN)" "$(ROOT)/scripts/install-server.sh"

update-server: build
	"$(ROOT)/scripts/update-server.sh" "$(BIN)"

uninstall-server:
	"$(ROOT)/scripts/uninstall-server.sh"

server-health:
	"$(ROOT)/scripts/health-check.sh"

ssh-check:
	"$(ROOT)/scripts/ssh-check.sh" "$(HOST)" "$(USER)" "$(SSH_PORT)"

clean: agent-stop
	rm -rf "$(VENV)" "$(ROOT)/dist" "$(ROOT)/.pytest_cache" "$(ROOT)/src/"*.egg-info
	rm -f "$(PID_FILE)" "$(LOG_FILE)" "$(CLIENT_CONFIG)"
	find "$(ROOT)" -type d -name __pycache__ -prune -exec rm -rf {} +
	@echo "cleaned local build artifacts"
