# dev_shell

`dev_shell` is a local developer shell plus a remote monitoring agent. You use one CLI for everyday work (files, network, git, docker) and for watching a server’s live CPU, memory, disk, network, and logs.

The point of the design is separation of jobs:

- **Python** is the user-facing shell: commands, server list, SSH tunnels, parsing the stream, drawing the terminal view.
- **Go** is the process that runs on the server: it collects metrics and logs and streams them as NDJSON over HTTP on loopback.
- **Bash + systemd** install, start, update, and stop that Go process. They do not collect metrics.

You do not scrape a public metrics API. The agent binds to `127.0.0.1:9477` on the remote machine. The CLI reaches it with OpenSSH local port forwarding (`ssh -N -L ...`). For local development you can skip SSH with `direct=true`.

Jaeger / OpenTelemetry tracing is optional and **off by default**. It is never the transport for metrics or logs.

---

## Why this is useful

Typical “SSH in and run `top` / `journalctl`” workflows are fine until you need the same view every day, on more than one host, without leaving a messy pile of one-off scripts.

`dev_shell` helps when you want:

- One prompt for local file/system work **and** remote health.
- A named server registry (`add-server`, `servers`) instead of retyping `user@host` and ports.
- Live metrics and logs in the terminal, with reconnect after a dropped tunnel or agent restart.
- A remote agent that is loopback-only by default, so the monitoring port is not on the public internet.
- Clear ownership: the `.service` file only starts the agent; Go collects; Python displays.

---

## How the system fits together

```text
You
  |
  v
Python CLI  (dev_shell)
  |  parse command, look up server
  |  start ssh -N -L local_port:127.0.0.1:9477   (unless direct=true)
  |  GET /health then GET /stream
  v
SSH tunnel
  v
Go agent on the server   127.0.0.1:9477
  |  collectors (cpu, memory, disk, network, system, optional process)
  |  log readers (journal units and explicit files you configure)
  v
NDJSON events: ready, heartbeat, metric, log, error
  v
Python validates events and renders metrics + logs
```

systemd’s only job is: start `/opt/dev-shell-monitor/dev-shell-monitor --config ...`, restart it if it dies.

---

## What each language does

### Python (`src/dev_shell`)

Python is the **client**. It:

- Runs the interactive shell and the one-shot CLI (`python -m dev_shell -- ...`).
- Registers commands (directory, file, system, network, servers, monitoring, …).
- Stores server connection details (host, user, SSH port, monitor port, identity file). It never stores private key material.
- Starts and stops OpenSSH port forwarding; checks that the local forwarded port actually works.
- Calls `GET /health` and `GET /stream`, parses one JSON object per line, rejects unknown protocol versions, and warns on sequence gaps.
- Reconnects with backoff (1s, 2s, 4s, … up to 30s) if the stream drops.
- Renders live metrics and logs. It does **not** collect remote CPU/memory itself (no `psutil` against the remote host).

Optional: OTLP export to Jaeger if you install extra packages and turn tracing on. Monitoring still works if tracing is missing or fails.

### Go (`remote/dev-shell-monitor`)

Go is the **remote runtime**. It:

- Loads YAML config (bind address, port, collector intervals, log sources, stream buffer).
- Runs collectors on a schedule and turns samples into typed `metric` events.
- Tails configured systemd journal units and log files into `log` events.
- Assigns increasing sequence numbers and broadcasts to all HTTP stream clients.
- Serves `GET /health` and `GET /stream` (NDJSON, flushed per event, heartbeats, `ready` first).
- Drops oldest events for a slow client so one stuck SSH session cannot stall the agent.
- Shuts down on SIGINT/SIGTERM (stop HTTP, close clients).

Go does **not** open your SSH keys or create the tunnel. It only listens where config says (default loopback).

### Bash (`scripts/`) and systemd (`deploy/systemd/`)

Bash is **lifecycle**, not collection:

| Script | Role |
|---|---|
| `scripts/install-server.sh` | Create `devshell` user, install binary and config, enable and start the unit, check `/health` |
| `scripts/update-server.sh` | Replace the binary and wait for health |
| `scripts/uninstall-server.sh` | Stop/disable unit; `--remove-config` also deletes `/etc/dev-shell-monitor` |
| `scripts/health-check.sh` | `systemctl is-active` (if systemd exists) and `curl` `/health` |
| `scripts/ssh-check.sh` | `ssh -o BatchMode=yes` connectivity check |
| `scripts/dev/test.sh` | Run Python tests |
| `scripts/dev/lint.sh` | `shellcheck` when installed |

`deploy/systemd/dev-shell-monitor.service` only tells systemd **how to start** the Go binary. It does not scrape hosts or read logs itself.

---

## Repository layout

| Path | Purpose |
|---|---|
| `src/dev_shell/` | Python package: CLI, commands, monitoring client, renderers |
| `remote/dev-shell-monitor/` | Go module: collectors, stream, HTTP server |
| `deploy/systemd/` | Unit file for the agent |
| `scripts/` | Install/update/uninstall/health/SSH helpers |
| `tests/` | Python tests |
| `Makefile` | Local run, test, and install shortcuts |
| `SKILLs.md` | Full implementation contract |

---

## Requirements

- Python 3.11+
- Go 1.22+
- OpenSSH client (for real remote servers)
- systemd on the machine that **runs** the Go agent (typical Linux server)

---

## Quick start (Make)

From the repo root:

```bash
make setup          # venv, pip install -e ".[dev]", Go modules
make run            # build agent, start it, register server "local"
make health         # GET http://127.0.0.1:9477/health
make stream         # sample NDJSON from /stream
make watch          # live dashboard for server "local"
make shell          # interactive CLI (uses .dev-shell-client.json)
make test           # Python + Go tests
make agent-stop     # stop the background agent
make help           # every Make target
```

`make demo` is `make run` then `make watch`.

`make run` talks to the agent **directly** (`direct=true`) on your laptop. That is for development only. Production entries should use SSH (omit `direct`).

---

## Python CLI

Install and enter the shell:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m dev_shell
```

One-shot (no prompt):

```bash
python -m dev_shell -- help
python -m dev_shell --config ~/.config/dev_shell/config.json -- servers
```

`--config PATH` selects the JSON file that holds the server list. If you omit it, new servers are saved to `~/.config/dev_shell/config.json`.

Inside the prompt:

- `help` — commands grouped by category
- `help network` — one category
- `help add-server` — usage for one command
- `last` — print the previous command (`history` and `last` themselves are not stored as “last”)
- `history` — recent commands
- `!!` — run the last command again
- Tab completion for command names when readline is available
- `exit` / `quit` / Ctrl+D — leave

---

## CLI commands

### Shell

| Command | What it does |
|---|---|
| `help [topic]` | List categories, or usage for a command/category |
| `version` | Print `dev_shell` version |
| `clear` | Clear the terminal |
| `history` | Show recent commands |
| `last` | Show the last real command |
| `!!` | Re-run that command |

### Directory

| Command | How it works |
|---|---|
| `pwd` | Print the shell’s current directory (tracked in the CLI, not only the process cwd) |
| `cd [PATH]` | Change that directory; no args goes to your home |
| `ls [PATH]` | List names; directories get a trailing `/` |
| `mkdir [-p] PATH` | Create a directory (`-p` creates parents) |
| `rmdir PATH` | Remove an empty directory |

### File

| Command | How it works |
|---|---|
| `cat PATH` | Print file contents |
| `touch PATH` | Create an empty file (creates parent dirs) |
| `cp SOURCE DEST` | Copy a file |
| `mv SOURCE DEST` | Move/rename |
| `rm [-r] PATH` | Delete a file; `-r` for a directory tree |

Missing paths print an error and return a non-zero status instead of crashing the shell.

### System

| Command | How it works |
|---|---|
| `sysinfo` | Hostname, OS, machine, Python version, CLI cwd |
| `whoami` | Current user from the environment |
| `env [NAME]` | All environment variables, or one name |

These describe **this machine**, not the remote Go agent.

### Network

| Command | How it works |
|---|---|
| `ping HOST` | Runs the system `ping -c 3` |
| `dns HOSTNAME` | Resolves addresses via `getaddrinfo` |

### Servers

Servers are how monitoring knows where to SSH (or connect directly).

| Command | How it works |
|---|---|
| `add-server NAME HOST USER` | Register a server |
| `add-server name=… host=… user=…` | Same, as `key=value` |
| `add server NAME HOST USER` | Same as `add-server` |
| `servers` | Table of name, `user@host:ssh_port`, monitor port, `ssh`/`direct`, identity path |
| `remove-server NAME` | Drop a registration |
| `connect-server NAME` | Open tunnel (unless `direct`), check `/health`, report ready |

Optional fields: `ssh_port=22`, `monitor_port=9477`, `identity_file=~/.ssh/id_ed25519`, `direct=true`.

Examples:

```text
add-server lab 10.0.0.5 devshell
add-server name=prod host=203.0.113.10 user=devshell identity_file=~/.ssh/id_ed25519
add-server name=local host=127.0.0.1 user=devshell direct=true
```

`direct=true` means: connect to `host:monitor_port` with HTTP, no SSH. Use that only when the agent is on the same machine (or otherwise reachable on loopback/VPN by intent).

Private keys are never written into the JSON file—only a path to an identity file.

### Monitoring

These commands talk to a **registered server** (see `add-server` / `servers`) and to the Go agent’s `/health` and `/stream` endpoints. `monitor` with no subcommand prints usage and exits.

Prerequisite: the agent is running, and the name you pass exists in the server list (`servers`). Loopback hosts (`127.0.0.1`, `localhost`) skip SSH and use HTTP. Real hosts use `ssh -N -L`. Do not pass a URL as the host (`http://127.0.0.1:9477` is the health URL, not the hostname).

| Command | Flags | What it does |
|---|---|---|
| `monitor` | none | Error + usage. You must pick a subcommand. |
| `monitor connect NAME` | none | Resolve `NAME`, open SSH tunnel unless direct/loopback, `GET /health`, print status. Does **not** open the live dashboard. Same idea as `connect-server NAME`. |
| `monitor sources NAME` | none | Resolve `NAME` (must exist). Prints metric families the pipeline supports: cpu, memory, disk, network, system. Logs are whatever the **agent YAML** lists (`journal` units / file paths), not auto-discovered. |
| `monitor dashboard NAME` | `-i` / `--interval` / `--interval=N` | Live metrics + log tail. Same as `watch-server`. |
| `monitor watch NAME` | same as dashboard | Alias of `monitor dashboard`. |
| `watch-server NAME` | same as dashboard | Preferred live view. |
| `monitor traces NAME` | none | Resolve `NAME`, then explain that Jaeger **query** is not implemented. Does not invent traces from metrics. |
| `monitor trace NAME TRACE_ID` | none | Needs two args. Prints a placeholder tree for `TRACE_ID`. Export-only tracing; no query API. |

#### Live view (`watch-server` / `monitor dashboard` / `monitor watch`)

Stream events are applied as they arrive. The **screen** is redrawn on a timer so it does not flood the terminal.

| Flag | Meaning |
|---|---|
| *(none)* | Refresh every **5** seconds |
| `-i SECONDS` | Refresh every `SECONDS` (must be `> 0`) |
| `--interval SECONDS` | Same as `-i` |
| `--interval=SECONDS` | Same, attached form |

```text
watch-server local
watch-server golang
watch-server golang -i 3
watch-server golang --interval 10
watch-server golang --interval=3
monitor dashboard golang -i 3
monitor watch golang --interval=5
```

The view shows: `SERVER`, `STATUS` (CONNECTING / CONNECTED / DEGRADED), CPU %, memory %, disk %, network RX/TX byte totals, uptime, then `LOGS` (last ~20 log events, or “no log events yet” if the agent has no log sources). Footer: refresh interval. **Ctrl+C** stops the view and closes the stream/tunnel; the shell prompt returns.

If `/stream` drops, the CLI waits with backoff (1s, 2s, 4s, … max 30s), reconnects, and keeps the same refresh interval. It does not crash the shell.

#### `monitor connect`

```text
monitor connect golang
connect-server golang
```

Prints connection mode (SSH tunnel vs direct HTTP), health `status`, protocol/version, and that the stream is ready. Use this to check the path without occupying the terminal on a dashboard.

#### `monitor sources`

```text
monitor sources golang
```

Does not start a stream. It only looks up the registered name and lists built-in metric groups. Remote log files/units are configured on the agent, not in this command.

#### Tracing subcommands

```text
monitor traces golang
monitor trace golang 4bf92f
```

`monitor trace` fails with usage if `TRACE_ID` is missing. Neither command reads `/stream`.

#### Related (not under `monitor`, but required for monitoring)

| Command | Role |
|---|---|
| `add-server NAME HOST USER` | Register the name you later pass to `watch-server` |
| `servers` | See names, `ssh` vs `direct`, monitor port |
| `connect-server NAME` | Same health/tunnel check as `monitor connect` |
| `remove-server NAME` | Drop a registration |

### Logs (local files)

| Command | How it works |
|---|---|
| `tail PATH` | Last 20 lines of a **local** file |

Remote logs come from the Go agent’s configured journal/file sources, then `watch-server`, not from this `tail` command.

### Permissions

| Command | How it works |
|---|---|
| `chmod MODE PATH` | Octal mode, e.g. `644` |
| `stat PATH` | Path, mode string, size |

### Integration

| Command | How it works |
|---|---|
| `git …` | Runs `git` in the CLI’s current directory |
| `docker …` | Runs `docker` in that directory |

---

## Make targets

| Target | What it does |
|---|---|
| `make setup` | Create `.venv`, install the package, `go mod download` |
| `make build` | Compile `dist/dev-shell-monitor` |
| `make run` | setup + build + start agent + `add-server` for `local` |
| `make demo` | `run` then `watch` |
| `make agent` / `agent-start` | Background agent, pid in `.dev-shell-monitor.pid` |
| `make agent-stop` / `agent-restart` / `agent-status` | Control / probe the local agent |
| `make health` / `make stream` | curl `/health` and a few `/stream` lines |
| `make shell` | Interactive CLI with `.dev-shell-client.json` |
| `make help-cli` | `help` through that config |
| `make add-local` | Register `SERVER` (default `local`) |
| `make servers` / `sources` / `connect` / `watch` / `traces` | CLI wrappers |
| `make CMD='sysinfo' cli` | Arbitrary CLI command |
| `make test` / `test-python` / `test-go` | Tests |
| `make lint` | shellcheck if present |
| `make install-server` | Root install of the built binary (Linux/systemd) |
| `make update-server` / `uninstall-server` / `server-health` | Matching scripts |
| `make ssh-check HOST=… USER=…` | BatchMode SSH check |
| `make clean` | Stop agent, remove venv, dist, local client json |

Override examples: `make add-local SERVER=prod HOST=203.0.113.10 USER=devshell DIRECT=false IDENTITY_FILE=~/.ssh/id_ed25519`.

---

## Go agent

Build and run (or use `make agent`):

```bash
cd remote/dev-shell-monitor
go test ./...
go run ./cmd/dev-shell-monitor --config ./configs/dev-shell-monitor.example.yaml
```

Default listen address: `127.0.0.1:9477`.

| Endpoint | Behavior |
|---|---|
| `GET /health` | JSON: `status`, `version`, `server_id`, `uptime_seconds` |
| `GET /stream` | `Content-Type: application/x-ndjson`; first event `ready`, then metrics/heartbeats/logs |

Example:

```bash
curl --fail http://127.0.0.1:9477/health
curl -N http://127.0.0.1:9477/stream
```

Each stream line is one event:

```json
{
  "type": "metric",
  "version": 1,
  "timestamp": "2026-09-29T09:30:01.120Z",
  "server_id": "server-1",
  "sequence": 1042,
  "data": { "name": "cpu.percent", "value": 31.2, "unit": "percent", "labels": { "host": "server-1" } }
}
```

Event types: `ready`, `heartbeat`, `metric`, `log`, `error`. Unknown types must not crash the Python client. Version must be `1`.

Metric names include `cpu.percent`, memory/disk byte and percent fields, `network.rx_bytes` / `network.tx_bytes` (with `interface` labels), `load.1` / `load.5` / `load.15`, `uptime.seconds`, and `process.count` when process collection is enabled.

Log sources are **only** what you list in YAML (`logs.journal`, `logs.files`). The agent does not scan the whole disk.

Process collection is **disabled** by default (`process.enabled: false`).

---

## Remote install (Linux + systemd)

As root, after `make build`:

```bash
make install-server
make server-health
make update-server
make uninstall-server
```

Or:

```bash
BINARY_SRC=./dist/dev-shell-monitor ./scripts/install-server.sh
./scripts/health-check.sh
```

Binary path: `/opt/dev-shell-monitor/dev-shell-monitor`. Config: `/etc/dev-shell-monitor/config.yaml`. Service user: `devshell`.

Then from your laptop (SSH, not `direct`):

```text
add-server prod YOUR_HOST devshell identity_file=~/.ssh/id_ed25519
watch-server prod
```

Host key verification stays on. The CLI does not use `StrictHostKeyChecking=no`.

---

## Optional tracing

If you enable tracing in client JSON and/or agent YAML and install OpenTelemetry extras (`pip install -e ".[tracing]"`), spans can be exported over OTLP to Jaeger.

Rules that stay true:

- Tracing disabled unless you turn it on
- Metrics and logs never go through Jaeger
- Export failure must not kill the agent or the CLI
- `monitor traces` does not invent traces from the metric stream

---

## Tests

```bash
make test
# or
python -m pytest tests
cd remote/dev-shell-monitor && go test ./...
```

---

## Implementation contract

`SKILLs.md` is the engineering spec this tree was built from (protocol, collectors, SSH options, definition of done). If behavior and that document disagree, treat the running code and this README as what is implemented today, and the spec as the intended contract.
