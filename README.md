# Engram + OpenCode Integration Setup
This document describes how to set up Engram integration for OpenCode and verify that tracking is working.

## Prerequisites
- `opencode` CLI installed and available in `PATH`
- `engram` CLI installed and available in `PATH`

Quick checks:
```bash
opencode --version
engram version
```

## 1) Configure Engram integration for OpenCode
Run:
```bash
engram setup opencode
```

Expected outcome:
- OpenCode plugin installed under `~/.config/opencode/plugins`
- Engram MCP integration configured for OpenCode

Optional verification:
```bash
ls -1 ~/.config/opencode/plugins
```
You should see `engram.ts`.

## 2) Start the Engram tracking server
Run in the background:
```bash
engram serve &
```

Verify process and listening port:
```bash
pgrep -fl "engram serve"
lsof -nP -iTCP:7437 -sTCP:LISTEN
```

Health check:
```bash
engram doctor --json
```
Expected: `"status": "ok"`.

## 3) Verify integration with a tracked test event
Trigger a test prompt through OpenCode:
```bash
opencode run "ENGRAM_INTEGRATION_TEST_<timestamp>: respond with ACK-<timestamp> only."
```

Check recent Engram context:
```bash
engram context
```
Expected: prompt appears under recent user prompts.

Check aggregate tracking stats:
```bash
engram stats
```
Expected:
- session count increases
- prompt count increases

Note: `engram search` may return no results if observations have not been created yet, even when prompts and sessions are tracked.

## Troubleshooting
- `zsh: command not found: opencode`
  - Install OpenCode CLI and re-check `opencode --version`.
- `opencode run` errors with: `You must provide a message or a command`
  - Pass a prompt string, e.g.:
  ```bash
  opencode run "hello"
  ```
- Engram server not running
  - Start it again with `engram serve &` and re-run doctor/port checks.
