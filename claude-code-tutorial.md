
# Claude Code: Complete Tutorial for Windows WSL

> **Repository:** [claude-code-healthcare-tutorial](https://github.com/niket-sharma/claude-code-healthcare-tutorial)  
> **File:** `docs/01-claude-code-tutorial.md`  
> **Part 1 of 2** — feature reference guide. For the hands-on project, see `docs/02-caretriage-project.md`.

> Covering the daily workflow, Permissions, Slash Commands, Checkpoints, MCP, Skills, Plugins, Hooks, Sub-Agents, Agent Teams, Ralph Loops, GSD, and Gas Town — foundations first, then the advanced stack.

---

## Table of Contents

1. [Installation on Windows WSL](#1-installation-on-windows-wsl)
2. [CLAUDE.md — Your Agent's Constitution](#2-claudemd-your-agents-constitution)
3. [Daily Workflow Fundamentals](#3-daily-workflow-fundamentals)
4. [Permissions & Safety](#4-permissions-safety)
5. [Slash Commands](#5-slash-commands)
6. [Checkpoints (File Rewinding)](#6-checkpoints-file-rewinding)
7. [MCP — Model Context Protocol](#7-mcp-model-context-protocol)
8. [Skills](#8-skills)
9. [Plugins](#9-plugins)
10. [Hooks](#10-hooks)
11. [Sub-Agents](#11-sub-agents)
12. [Multi-Agents & Agent Teams](#12-multi-agents-agent-teams)
13. [Ralph Loops](#13-ralph-loops)
14. [GSD — Get Shit Done Framework](#14-gsd-get-shit-done-framework)
15. [Gas Town — Your Personal Agent Factory](#15-gas-town-your-personal-agent-factory)
16. [Putting It All Together: Full Stack Demo](#16-putting-it-all-together-full-stack-demo)

---

## How to Use This Tutorial

The sections are ordered so you can read top to bottom, but the *learning* priority isn't the same as the section order. A suggested path:

1. **Get running and fluent first** (§1–§4): install, write a CLAUDE.md, learn the interaction loop and plan mode, set up permissions. This alone makes you productive — most people never need more.
2. **Add structure as you need it** (§5–§10): slash commands, checkpoints, MCP, skills, plugins, hooks. Reach for each when a real pain point shows up, not preemptively.
3. **Scale to autonomy last** (§11–§16): sub-agents, agent teams, Ralph loops, GSD, Gas Town. These are powerful but easy to misuse before the fundamentals are second nature. Don't start here.

If you only learn three things, learn: CLAUDE.md, plan mode, and `/clear` between tasks.

---

## 1. Installation on Windows WSL

Claude Code runs natively inside WSL2 (Ubuntu). Do **not** install it in Windows PowerShell directly — WSL gives you the Linux toolchain Claude Code expects.

### Prerequisites

```bash
# In your WSL2 Ubuntu terminal
node --version   # Need Node.js 18+ (or use the native installer — no Node required)
git --version    # Need Git
```

### Option A: Native Installer (Recommended — no Node.js required)

```bash
# Inside WSL2
curl -fsSL https://claude.ai/install.sh | bash

# Restart your shell, then authenticate
claude
# → Opens browser for OAuth login
```

### Option B: npm (legacy, still works)

```bash
npm install -g @anthropic-ai/claude-code
claude --version
```

### WSL-Specific Tips

```bash
# If you get Cloudflare/network errors, set DNS explicitly
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf

# Open VS Code from WSL (Remote-WSL extension)
code .

# Verify Claude Code is on PATH
which claude
# → /home/<you>/.local/bin/claude  or  ~/.nvm/bin/claude
```

### First Launch

```bash
cd ~/projects/my-project
claude
# Claude reads your repo, asks what you want to do
```

Authentication happens once via browser — tokens are cached in `~/.claude/`.

### A Note on Model Names

Throughout this tutorial, `--model claude-opus-4-7` and `--model claude-sonnet-4-6` are used (the current flagship and daily-driver models as of May 2026). But you'll usually want the **aliases** instead, which auto-resolve to the latest version:

```bash
claude --model opus      # latest Opus
claude --model sonnet    # latest Sonnet (great default — Opus-level quality, lower cost)
claude --model haiku     # latest Haiku (cheap, fast — ideal for subagents)
claude --model opusplan  # Opus for planning, auto-switches to Sonnet for execution
```

Switch mid-session with `/model sonnet`. Pin exact versions (e.g. for reproducible CI) via the `ANTHROPIC_MODEL` env var or `--model claude-opus-4-7`. Aliases are convenient but shift when new models ship — pin for production.

> Cost reality: Opus burns tokens fast. For most coding, `sonnet` is the right default; reserve `opus` for architecture, hard debugging, and orchestration. Subagents on `haiku` keep parallel workflows affordable.

---

## 2. CLAUDE.md — Your Agent's Constitution

Before any advanced feature, get `CLAUDE.md` right. Claude reads this file **every session**, so it's your project-level memory.

```bash
# Create in your project root
touch CLAUDE.md
```

```markdown
<!-- CLAUDE.md -->
# Project: my-ai-pipeline

## Stack
- Python 3.11, FastAPI, PostgreSQL
- Poetry for dependency management

## Commands
- Build: `poetry run build`
- Test:  `poetry run pytest -x`
- Lint:  `poetry run ruff check . --fix`
- Run:   `uvicorn app.main:app --reload`

## Conventions
- Type hints on all functions
- No default exports (Python modules)
- Commit format: feat/fix/chore(scope): description
- Never edit files in `generated/` — those are auto-generated

## Critical Rules
- Always run tests before committing
- API keys live in .env, never in code
- Ask before deleting files
```

Claude will follow these rules automatically, session after session, without you repeating yourself.

---

## 3. Daily Workflow Fundamentals

Before the power features, here's how you actually *work* with Claude Code turn to turn. This is 90% of real usage — get fluent here first.

### The Interaction Loop

You type a request; Claude thinks, then proposes actions (reading files, running commands, editing code). For anything that changes your system, it shows you what it wants to do and waits for approval — unless you've pre-approved that action (see Permissions below).

The moves you'll use constantly:

- **Approve / reject** an action when prompted. Rejecting isn't failure — it's steering. You can reject and immediately type *why*, and Claude adjusts.
- **Interrupt with `Esc`.** If Claude is heading the wrong direction mid-task, hit Esc to stop it, then redirect. You don't have to let a bad plan finish.
- **`Esc` twice** opens the rewind menu (see Checkpoints) when the input is empty.
- **Queue follow-ups.** You can keep typing while Claude works; messages are picked up in order.
- **`Ctrl+C`** cancels the current input; press again to exit the session. **`/exit`** quits cleanly.

The mental model: you're the senior engineer reviewing a fast junior. Read the diffs, don't rubber-stamp. The people who get the most out of Claude Code are the ones who steer early and often, not the ones who write one giant prompt and hope.

### Plan Mode — the single best habit

Plan mode puts Claude in **read-only** mode: it can read files and analyze your codebase but cannot edit anything until you approve a plan. Toggle it with **Shift+Tab** (cycles through permission modes) or `/plan`.

```
Shift+Tab        → cycle: normal → auto-accept edits → plan mode
```

Use it for anything non-trivial: production-critical files, database migrations, multi-file refactors, or any task where you want to understand scope *before* code changes. Claude proposes a plan, you refine it in conversation, and only then does it execute. This single habit prevents most "it went and rewrote half my repo" moments.

### Managing Context (this is a skill)

Claude's quality degrades as its context window fills — the "context rot" problem. A session that's thorough at 20% full starts cutting corners past 50% and hallucinating past 70%. Manage it deliberately:

- **`/context`** — see how full the window is. Check it during long sessions.
- **`/compact`** — summarize the conversation so far, reclaiming space while keeping the gist. Good when you're deep in a task but the window's getting full.
- **`/clear`** — wipe context entirely and start fresh. Use this between unrelated tasks. Cheaper and cleaner than letting one session sprawl across three different problems.
- **`/rewind`** — roll back code and/or conversation (see Checkpoints).

Rule of thumb: one session per coherent task. When you switch to something unrelated, `/clear`. When a single task is genuinely large, that's when subagents and frameworks like GSD earn their keep — they keep the main window lean by offloading work to fresh contexts.

### Checking Cost and Usage

- **`/cost`** — spend so far (API billing users)
- **`/stats`** — usage so far (Pro/Max subscription users)
- **`/usage`** — how close you are to a rate limit

Worth glancing at during heavy sessions, especially before you start anything that spawns parallel agents — those multiply token burn.

---

## 4. Permissions & Safety

Every action Claude wants to take goes through a permission check: the harness decides whether to **allow** it, **ask** you, or **deny** it. If you don't configure this, you'll spend half your day clicking Approve on `git status`. Configure it once and Claude runs smoothly while staying inside guardrails.

### The settings.json Permission Block

Permissions live in `.claude/settings.json` (project, committed to git and shared with your team) or `~/.claude/settings.json` (user, applies everywhere):

```json
{
  "permissions": {
    "defaultMode": "default",
    "allow": [
      "Bash(git status)",
      "Bash(git diff:*)",
      "Bash(npm run lint:*)",
      "Bash(poetry run pytest:*)",
      "Read(./**)"
    ],
    "ask": [
      "Bash(git push:*)",
      "Bash(gh pr merge:*)"
    ],
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(curl:*)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./**/credentials*)"
    ]
  }
}
```

### How Rules Are Evaluated

The order is **deny → ask → allow**, and **first match wins**. Deny always has the highest priority — a deny rule blocks a tool even in the most permissive mode. This means:

- A user-level `deny` on `Bash(rm -rf:*)` is a safety net no individual project can override.
- `allow`/`deny` lists from user and project settings **merge** (they don't replace each other).
- Anything matching no rule falls through to `defaultMode`.

### Pattern Syntax

Rules are `ToolName` or `ToolName(specifier)`:

- `Bash(npm:*)` — any npm command
- `Bash(git diff:*)` — git diff with any arguments
- `Read(./.env*)` — reading any .env file
- `Edit(./src/**)` — editing anything under src/
- MCP tools use a different format: `mcp__servername__toolname` (double underscores, no parentheses)

### The Four Permission Modes

`defaultMode` (and the `--permission-mode` CLI flag) controls what happens to unmatched actions:

- **`default`** — ask for anything not explicitly allowed. Safest interactive mode.
- **`acceptEdits`** — auto-approve file reads/writes, still confirm shell commands. The sweet spot for active development.
- **`plan`** — read-only; Claude can analyze and propose but not change anything (this is Plan mode).
- **`bypassPermissions`** — approve everything that reaches the mode check. **This is what `--dangerously-skip-permissions` turns on.** Deny rules and hooks still fire, but otherwise Claude has full access. Only use in a sandboxed/containerized environment you fully trust.

> The Ralph Loop and Gas Town sections use `--dangerously-skip-permissions` so the loop runs unattended. Now you know what that flag actually does: it puts Claude in `bypassPermissions` mode. **Run those loops in a container or VM, never on your main machine** — your `deny` rules are the only thing still protecting you, so make them good.

### Recommended Starter Deny List

Drop this into `~/.claude/settings.json` before your first real task — 30 seconds of setup that prevents the worst accidents:

```json
{
  "permissions": {
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(git push --force:*)",
      "Read(./**/.env*)",
      "Read(./**/secrets/*)",
      "Read(./**/credentials*)",
      "Edit(./**/.env*)"
    ]
  }
}
```

### Interactive Management

You don't have to hand-edit JSON. Run **`/permissions`** inside a session to review and modify rules interactively. There's also **`additionalDirectories`** in settings to grant Claude access beyond the working directory (e.g. a shared monorepo package or a logs folder) — by default it can only touch the current directory and its subdirectories.

---

## 5. Slash Commands

Slash commands turn Claude from a chatbot into a **deterministic workflow engine**. Custom ones traditionally live in `.claude/commands/`, though Claude Code increasingly treats **Skills** (`.claude/skills/`) as the richer form of the same slash-command interface (see Skills, §8).

### Built-in Commands (a useful subset)

```
/help          List available commands
/clear         Clear the conversation/context (start fresh)
/compact       Summarize context to reclaim space
/rewind        Open the rewind menu (alias: /checkpoint) — see Checkpoints, §6
/model         Switch model mid-session (e.g. /model sonnet)
/agents        Create and manage subagents interactively
/context       See how full your context window is
/cost          (API billing) spend so far
/stats         (Pro/Max) usage so far
/usage         Check rate-limit headroom
```

`/plan` (or Shift+Tab) puts Claude in read-only mode — it analyzes and proposes changes but can't edit until you approve. Good for production-critical files. The exact built-in set evolves; run `/help` to see what your installed version offers.

### Creating a Custom Slash Command

```bash
mkdir -p .claude/commands
```

```markdown
<!-- .claude/commands/code-review.md -->
---
description: Full code review: bugs, security, performance, style
allowed-tools: Read, Glob, Grep
---

You are a senior engineer doing a code review. For each file touched in the last commit:
1. Read the file
2. Check for: bugs, security issues, performance problems, style violations
3. Output a structured Markdown report with sections: Bugs · Security · Performance · Style
4. Rate overall quality 1-10

Files to review: $ARGUMENTS
```

Usage:

```
/code-review src/api/routes.py
```

### Multi-Step Command with Subagent

```markdown
<!-- .claude/commands/feature.md -->
---
description: Full feature cycle — spec, plan, implement, test
allowed-tools: Read, Write, Bash, Glob
context: fork
---

Given the feature request: $ARGUMENTS

Step 1 — Spec: Write a feature spec to docs/specs/$ARGUMENTS.md
Step 2 — Plan: Break into atomic tasks, each fitting in 50% context
Step 3 — Implement: Execute each task using a fresh subagent
Step 4 — Test: Run the test suite and fix any failures
Step 5 — Commit: Stage all changes with a conventional commit message
```

Usage:

```
/feature "add JWT refresh token rotation"
```

---

## 6. Checkpoints (File Rewinding)

Checkpoints are a **built-in, automatic safety net** — nothing to enable, no manual "save" step. Claude Code snapshots your code before each edit, and **every prompt you send automatically creates a checkpoint**. This lets you attempt ambitious changes knowing you can return to a prior state.

### Opening the Rewind Menu

```
/rewind          (alias: /checkpoint)
```

Or press **Esc twice** when the prompt input is empty. (If the input has text, double-Esc clears it instead — the cleared text is saved to history; press Up to recall it.)

### The Rewind Options

When you rewind, you pick a point in your session, then choose what to restore:

- **Restore code and conversation** — revert both files and messages. Use after a bad tangent.
- **Restore conversation** — rewind messages only, keep current code. Use to re-phrase a prompt without losing code progress.
- **Restore code** — revert files only, keep the full conversation. Use to undo bad AI code but keep the diagnostic discussion.
- **Summarize from here** — summarize the session from that point. Use when context is getting too long.

### What Checkpointing Does NOT Track

Critical — checkpoints are **not** a git replacement:

- **Bash command changes are NOT tracked.** If Claude runs `rm file.txt`, `mv`, or `cp`, those cannot be undone via rewind. Only direct file edits made through Claude's editing tools are captured.
- **Manual edits and edits from other concurrent sessions** are normally not captured.
- Checkpoints are **session-level** and are cleaned up automatically after ~30 days.

Keep using git for permanent version history. Checkpoints are for fast, in-session recovery.

### In Code (Agent SDK) — for autonomous loops

If you're scripting Claude (e.g. inside a Ralph loop), enable file checkpointing and capture checkpoint UUIDs so you can rewind to the last safe state:

```python
async with ClaudeSDKClient(
    ClaudeAgentOptions(enable_file_checkpointing=True, resume=session_id)
) as client:
    await client.query("")  # empty prompt to open the connection
    async for message in client.receive_response():
        await client.rewind_files(checkpoint_id)
        break
```

From the CLI, given a captured session and checkpoint UUID:

```bash
claude -p --resume <session-id> --rewind-files <checkpoint-uuid>
```

The common pattern: keep only the most recent checkpoint UUID, updating it before each agent turn. If something goes wrong, immediately rewind to the last safe state and break out of the loop.

---

## 7. MCP — Model Context Protocol

MCP connects Claude Code to **external systems**: GitHub, databases, browsers, internal APIs. Think of MCP servers as plugins that give Claude new senses.

### Adding an MCP Server to Your Project

```bash
# Global config (all projects)
claude mcp add github npx @github/mcp-server
claude mcp add postgres npx @modelcontextprotocol/server-postgres \
    "postgresql://localhost/mydb"

# Project-level (committed to repo — team shares it)
claude mcp add --scope project filesystem npx @modelcontextprotocol/server-filesystem /home/niket/projects
```

### Project-Level Config (`.claude/mcp.json`)

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["@github/mcp-server"],
      "env": { "GITHUB_TOKEN": "${GITHUB_TOKEN}" }
    },
    "postgres": {
      "command": "npx",
      "args": [
        "@modelcontextprotocol/server-postgres",
        "postgresql://localhost/mydb"
      ]
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "@modelcontextprotocol/server-filesystem",
        "/home/niket/projects"
      ]
    }
  }
}
```

### What MCP Gives Claude

Once connected, Claude can:
- **GitHub MCP**: Create issues, PRs, read commits, search code
- **Postgres MCP**: Query your DB, inspect schemas, run migrations
- **Filesystem MCP**: Read/write files outside the current directory
- **Browser MCP**: Control a browser for E2E testing or scraping

### Usage Example

```
You: Find all open GitHub issues labeled "bug" and create a fix plan

Claude: [Uses GitHub MCP]
Found 7 open bugs. Here's the priority plan:
1. #142 — NullPointerException in auth handler (P0)
2. #138 — Memory leak in cache layer (P1)
...
```

---

## 8. Skills

Skills are **reusable, token-efficient workflows** stored as Markdown files. Claude loads only the description at startup (~100 tokens); full instructions load on demand — saving 70–90% tokens vs. stuffing everything in CLAUDE.md.

### Structure

```
.claude/
  skills/
    code-review/
      SKILL.md          ← instructions + frontmatter
      checklist.md      ← referenced by SKILL.md on demand
      security.md       ← referenced by SKILL.md on demand
```

### Example: Code Review Skill

```markdown
<!-- .claude/skills/code-review/SKILL.md -->
---
name: code-review
description: Thorough code review covering security, perf, style
allowed-tools: Read, Grep, Glob
context: fork
---

# Code Review Skill

1. Read the file(s) specified: $ARGUMENTS
2. Read checklist.md for review criteria
3. Read security.md for security-specific checks
4. Produce a Markdown report:
   ## Summary
   ## Bugs Found
   ## Security Issues
   ## Performance Notes
   ## Style
   ## Score: X/10
```

### Example: Deploy Skill (Human-Only Trigger)

```markdown
<!-- .claude/skills/deploy/SKILL.md -->
---
name: deploy
description: Deploy to production — human must invoke, Claude cannot auto-trigger
disable-model-invocation: true
allowed-tools: Bash(npm:*), Bash(git:*)
---

Deploy to production:
1. Run: npm test
2. Run: npm run build
3. Run: git push origin main
4. Run: npm run deploy:prod
5. Verify health endpoint returns 200
```

The `disable-model-invocation: true` flag means Claude can never auto-call this — only you can type `/deploy`.

### Invoking a Skill

Skills become slash commands automatically:

```
/code-review src/auth/
/deploy
```

---

## 9. Plugins

Plugins are **packaged, installable skills + subagents + MCP configs** — think npm packages for Claude Code workflows. They appeared in the official marketplace in October 2025.

### Installing from the Marketplace

```bash
# View available plugins
claude plugin list

# Install a plugin
claude plugin install ralph-wiggum    # autonomous loop plugin
claude plugin install sequential-thinking
claude plugin install deep-research
```

### What a Plugin Contains

```
my-plugin/
  plugin.json           ← metadata + permissions
  skills/
    SKILL.md
  agents/
    researcher.md
  mcp/
    config.json
  hooks/
    post-edit.sh
```

### `plugin.json`

```json
{
  "name": "deep-research",
  "version": "1.2.0",
  "description": "Multi-step web research with citations",
  "permissions": ["WebFetch", "Read", "Write"],
  "skills": ["skills/research.md"],
  "agents": ["agents/researcher.md"],
  "hooks": {
    "PostToolUse": "hooks/post-edit.sh"
  }
}
```

### Installing a Local Plugin

```bash
# From a local directory
claude plugin install ./my-plugin/

# From GitHub
claude plugin install github:niket-sharma/my-claude-plugin
```

### The `ralph-wiggum` Plugin

The official autonomous loop plugin from the marketplace:

```bash
claude plugin install ralph-wiggum
```

After installing:

```
/ralph "refactor the auth module to use JWT"
# → Runs autonomous loop until task complete or max-iterations hit
```

---

## 10. Hooks

Hooks run **your own code automatically** at specific points in Claude Code's lifecycle. They turn best-practice guidelines into enforced rules — auto-format on every edit, block dangerous commands deterministically, run tests before a commit lands, ping you when a long task finishes.

The difference between a hook and a CLAUDE.md instruction: CLAUDE.md *asks* Claude to do something (it might forget); a hook *guarantees* it runs (Claude can't skip it).

### The Lifecycle Events

Hooks fire at defined points, in three cadences:

- **Once per session:** `SessionStart` (great for injecting fresh project context at startup), `SessionEnd`
- **Once per turn:** `UserPromptSubmit`, `Stop`, `StopFailure`
- **On every tool call:** `PreToolUse` (before — can block), `PostToolUse` (after — for cleanup/formatting)
- **Other:** `Notification`, `SubagentStop` (fires when a subagent completes — so your gates apply recursively)

You'll use `PreToolUse` and `PostToolUse` for ~80% of hooks. `SessionStart` is the next most useful.

### Exit Codes Are the Control Mechanism

For command hooks, the exit code decides what happens:

- **Exit 0** — success, proceed
- **Exit 2** — **block the action** (this is the enforcement power: a `PreToolUse` hook that exits 2 stops the tool cold; a `Stop` hook that exits 2 forces Claude to keep working)
- **Exit 1** — non-blocking error; logs a warning but the action still proceeds

Every security-critical hook must use exit 2 to actually enforce its gate.

### Configuration

Set hooks up the easy way with the interactive **`/hooks`** command (it walks you through event → matcher → command), or hand-write them in `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "poetry run ruff format ." }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": ".claude/hooks/block-dangerous.sh" }
        ]
      }
    ]
  }
}
```

The `matcher` is a regex against the tool name (`Bash`, `Write`, `Edit`, etc.). Each event passes JSON context to your handler on **stdin** — for `PreToolUse` that includes `tool_name` and the full `tool_input`, so your script can inspect exactly what Claude is about to do.

### Example: Block Dangerous Bash Commands

```bash
#!/bin/bash
# .claude/hooks/block-dangerous.sh
# Reads the PreToolUse JSON on stdin, blocks rm -rf

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // ""')

if echo "$command" | grep -qE 'rm -rf|git push --force'; then
  echo '{"message": "Blocked: destructive command caught by hook"}'
  exit 2   # exit 2 = block
fi
exit 0
```

(Install `jq` in WSL first: `sudo apt-get install -y jq`.)

### Handler Types

Command hooks (shell scripts) handle ~90% of cases. There are also **HTTP hooks** (POST the event JSON to a URL — for team-wide remote policy servers), **prompt hooks** (ask Claude a yes/no question), and **agent hooks** (spawn a subagent for deeper verification). Start with command hooks; reach for the others only when you need AI judgment or external integration.

### Two Gotchas

- **PostToolUse loops:** a `PostToolUse` hook that *edits* a file triggers another `PostToolUse` event → infinite loop. Guard with specific matchers.
- **Stop hooks should be passive:** if a `Stop` hook writes a file or runs a command that makes Claude respond, you've created a loop. Keep `Stop` hooks to logging, notifying, cleanup.

---

## 11. Sub-Agents

Sub-agents are **specialized Claude instances** that run in isolated context windows. The key insight: sub-agent context never flows back to the main dialogue, so the main agent stays lean while sub-agents do heavy lifting.

### Why Sub-Agents?

Without sub-agents: one long session → context fills → quality degrades → hallucinations.

With sub-agents: main session stays at 30–40% context while sub-agents each get a clean 200k-token window. Task 50 has the same quality as Task 1.

### Frontmatter Fields

A subagent is just a Markdown file with YAML frontmatter. The body is the system prompt.

- `name` (**required**) - the agent's identifier
- `description` (**required**) - when to use this agent. The main agent reads this to decide whether to delegate, so write it with explicit trigger conditions, not just a summary. Vague descriptions never get auto-invoked.
- `tools` (optional) - restrict which tools the agent can use. **Omit to inherit the parent's full toolset.** Restricting is a safety feature: give a reviewer only `Read, Grep` so it physically cannot modify files.
- `model` (optional) - `haiku`, `sonnet`, `opus`, or `inherit`. Use `haiku` for fast/cheap search agents, `opus` for hard reasoning.

> Note: only `name` and `description` are required. The three built-in subagents are **Explore** (read-only, runs on Haiku), **Plan** (gathers context for plan mode), and **general-purpose**.

The easiest way to create one is the interactive `/agents` command. Or drop a file into `.claude/agents/` (project, shared via git) or `~/.claude/agents/` (personal). Project-level wins on name conflicts.

### Sub-Agent File (researcher)

```markdown
<!-- .claude/agents/researcher.md -->
---
name: researcher
description: Use PROACTIVELY for research tasks - fetches docs and summarizes findings. Trigger when the user asks to investigate a library, API, or technique.
tools: WebFetch, Read, Write
model: sonnet
---

You are a research specialist. Given a topic:
1. Fetch the official documentation
2. Search for recent blog posts and tutorials
3. Synthesize findings into a structured Markdown summary
4. Save to docs/research/$TOPIC.md

Topic: $ARGUMENTS
```

### Sub-Agent File (planner)

```markdown
<!-- .claude/agents/planner.md -->
---
name: planner
description: MUST BE USED before implementation. Breaks a feature spec into atomic, dependency-ordered tasks.
tools: Read, Write
model: opus
---

You are a senior technical lead. Given a feature spec:
1. Read the spec from docs/specs/$ARGUMENTS.md
2. Break it into atomic tasks (each < 200 lines of code change)
3. Order tasks by dependency
4. Write the plan to docs/plans/$ARGUMENTS.md
5. Each task must have: title, files affected, acceptance criteria
```

> Cost note: subagent-heavy workflows can use **~7x the tokens** of a single-thread session, since each subagent maintains its own context. There's no separate billing - it all draws from your plan. Background subagents run concurrently with the main conversation via `Ctrl+B`.

### Invoking Sub-Agents from a Slash Command

```markdown
<!-- .claude/commands/full-feature.md -->
---
description: Research → Plan → Implement → Test → Commit
allowed-tools: Read, Write, Bash
---

For feature: $ARGUMENTS

1. Launch researcher subagent: /agent researcher "$ARGUMENTS"
2. Wait for docs/research/$ARGUMENTS.md
3. Launch planner subagent: /agent planner "$ARGUMENTS"
4. Wait for docs/plans/$ARGUMENTS.md
5. Execute each task from the plan
6. Run tests: bash -c "npm test"
7. Commit: git commit -am "feat: $ARGUMENTS"
```

---

## 12. Multi-Agents & Agent Teams

**Agent Teams** (launched February 2026) let multiple Claude instances work **in parallel**, each owning a piece of the codebase. Requires Claude Code v2.1.139+.

### Agent View

Claude Code's Agent View — a dashboard showing running agents, their status, token usage, and current task — is available in recent versions (a research preview at the time of writing, requiring Claude Code v2.1.139+). Check `/help` or the docs for the exact keybinding in your version.

### How Agent Teams Differ from Subagents

Subagents work *within* a single session: they delegate a focused task to an isolated worker, and the result flows back to the main agent. Agent teams scale this up - a lead agent coordinates multiple teammates that share a task list, claim work, and can run in parallel across separate git worktrees.

> Heads up: agent-team orchestration is newer and evolving fast (the Agent View dashboard is a research preview as of mid-2026). Treat the team setup below as a **working pattern**, not frozen official syntax - check `https://code.claude.com/docs` for the current frontmatter and commands before relying on it in production. The individual subagent files use only confirmed fields (`name`, `description`, `tools`, `model`).

### Worktree Isolation (the key technique)

Parallel agents collide if they edit the same files. The fix is git worktrees - each agent gets its own checkout on its own branch:

```bash
git worktree add ../proj-backend  -b feature/backend
git worktree add ../proj-frontend -b feature/frontend
# Run a Claude session in each, scoped to its worktree
```

### Backend Agent

```markdown
<!-- .claude/agents/backend-agent.md -->
---
name: backend-agent
description: FastAPI backend specialist. Owns src/api, src/models, src/db.
tools: Read, Write, Edit, Bash
model: opus
---

Responsible for: src/api/, src/models/, src/db/
Never touch: src/frontend/, tests/ (test-agent owns those)

When starting:
1. Read CLAUDE.md for project conventions
2. Read your assigned task from tasks/backend.md
3. Implement, run `poetry run pytest src/`, iterate until green
4. Write a completion note to tasks/backend-done.md
```

### Frontend Agent

```markdown
<!-- .claude/agents/frontend-agent.md -->
---
name: frontend-agent
description: React/TypeScript frontend specialist. Owns src/frontend.
tools: Read, Write, Edit, Bash
model: sonnet
---

Responsible for: src/frontend/
Never touch: src/api/, src/models/

When starting:
1. Read tasks/frontend.md
2. Implement components, run `npm test`, iterate until green
3. Write completion to tasks/frontend-done.md
```

### Orchestrator (main session)

The orchestrator is your main Claude Code session. It splits the work, spawns the worker agents, then waits for their completion signals. A slash command captures the workflow:

```markdown
<!-- .claude/commands/build-feature.md -->
---
description: Coordinate a full-stack feature build across worktree agents
allowed-tools: Read, Write, Bash, Task
---

Feature: $ARGUMENTS

1. Write task specs to tasks/backend.md and tasks/frontend.md
2. Delegate to backend-agent and frontend-agent (they run in their own worktrees)
3. Poll tasks/*-done.md for completion signals
4. Once both complete, delegate to test-agent to run the full suite
5. Once tests pass, delegate to reviewer-agent
6. Collect review output, fix issues, commit
```

> The `Task` tool is how the main agent spawns subagents. In practice you'll often just describe what you want ("use the backend-agent on the auth tasks") and let Claude route — explicit orchestration commands are for when you want a repeatable, deterministic pipeline.

### Cost Warning

Each parallel agent consumes tokens from your plan simultaneously. Running 5 agents = 5x token burn rate. Use agent teams for genuinely parallelizable work, not just to feel fast.

---

## 13. Ralph Loops

The Ralph Loop (by Geoffrey Huntley, named after Ralph Wiggum from The Simpsons) is a **bash loop that gives a fresh Claude process to each iteration**, with Git as the memory layer.

The insight: instead of fighting context rot in one long session, embrace fresh context every iteration. Git history IS the memory.

### The Original Ralph Loop (Bash)

```bash
#!/bin/bash
# ralph-loop.sh — Geoffrey Huntley's original technique

MAX_ITER=${1:-50}
PROMPT_FILE=${2:-AGENT_PROMPT.md}

for i in $(seq 1 $MAX_ITER); do
    echo "=== Ralph Iteration $i / $MAX_ITER ==="
    
    # Each iteration: fresh Claude process, clean context
    claude \
        --dangerously-skip-permissions \
        -p "$(cat $PROMPT_FILE)" \
        --model claude-opus-4-7
    
    EXIT=$?
    
    # Check if Claude declared completion
    if grep -q "TASK_COMPLETE" AGENT_PROMPT.md; then
        echo "Task complete at iteration $i"
        break
    fi
    
    # Git is the memory — commit after each iteration
    git add -A
    git commit -m "ralph: iteration $i" --allow-empty
    
    echo "--- Sleeping 2s ---"
    sleep 2
done
```

Usage:

```bash
# Write your goal to AGENT_PROMPT.md first
echo "Implement OAuth2 login. Read existing code, make progress, commit. Write TASK_COMPLETE when done." > AGENT_PROMPT.md

chmod +x ralph-loop.sh
./ralph-loop.sh 20 AGENT_PROMPT.md
```

### WSL-Specific Ralph Setup

```bash
# Install jq for JSON parsing in hooks
sudo apt-get install -y jq

# Make sure Claude is on PATH in non-interactive shells
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Test non-interactive Claude
claude -p "say hello" --model claude-sonnet-4-6
```

### Ralph Loop with Checkpoint + Rewind

```bash
#!/bin/bash
# ralph-safe.sh — with checkpointing

for i in $(seq 1 30); do
    echo "=== Iteration $i ==="
    
    # Save state before each run
    claude /checkpoint "iter-$i"
    
    claude \
        --dangerously-skip-permissions \
        -p "$(cat AGENT_PROMPT.md)" \
        --model claude-opus-4-7
    
    # Run tests after each iteration
    if ! npm test 2>/dev/null; then
        echo "Tests failed — rewinding to iter-$i checkpoint"
        claude /rewind "iter-$i"
    else
        git add -A && git commit -m "ralph: iter $i [passing]"
    fi
done
```

### Why Not the ralph-wiggum Plugin?

The plugin lets Claude control the loop. The bash script gives **you (bash)** control over Claude. The original technique is more robust because:
- No context rot (each invocation is truly fresh)
- You control iteration logic, not Claude
- Bash exit codes give reliable completion detection

Use the plugin for simple tasks; use the bash loop for overnight autonomous runs.

---

## 14. GSD — Get Shit Done Framework

GSD is a **spec-driven development system** built entirely from native Claude Code features (Skills + Sub-agents + Hooks). It launched December 2025 and became one of the most popular Claude Code workflow systems (tens of thousands of GitHub stars). Note: the project changed hands in spring 2026 — see the install note below before adopting it.

It solves the #1 Claude Code problem: context rot degrading quality over long sessions.

### How GSD Works

GSD uses a chain of slash commands, each phase in a **fresh subagent context**:

```
/gsd-init      → Generate project spec
/gsd-plan      → Break spec into phases
/gsd-build     → Execute each phase (fresh context per phase)
/gsd-verify    → Run tests + quality gates
/gsd-done      → Final commit + changelog
```

### Install GSD

```bash
# In your WSL terminal, in your project directory
npx get-shit-done-cc --claude --local    # project-specific
# or --global for all your repos
npx get-shit-done-cc --claude --global

# Start GSD
/gsd-help
```

> ⚠️ **Important status note (verify before installing).** GSD's situation changed in spring 2026: the original maintainer (TÂCHES) became unreachable, an associated "$GSD" crypto token was publicly linked to a rug-pull, and the original `gsd-build/get-shit-done` repo is no longer the active development home. The community has forked it forward as **GSD Redux** under the `open-gsd` organization. None of this affects the *technique* (spec-driven workflows are sound), but **check the current canonical repo and audit the install command before running `npx` against it** — supply-chain caution applies to any tool that runs in your shell. See the Resources section for current links.

### GSD's Internal Architecture

GSD is built from pure Claude Code primitives (no proprietary runtime) — roughly:
- **~29 Skills** — the slash commands you invoke (exact count varies by version)
- **~12 Custom Sub-Agents** — specialized workers for research, planning, execution, verification
- **A couple of Hooks** — e.g. a status bar and an update checker

Newer GSD versions package these as Skills (`.claude/skills/`) rather than the older `.claude/commands/` directory — Claude Code now treats skills as the richer form of slash command, and the legacy commands directory has been effectively superseded.

### The Context Engineering Secret

GSD keeps the main session at 30–40% context by offloading all heavy work to sub-agents. Each sub-agent gets a clean 200k-token window. Compare:

```
Without GSD:
Session 0%   → Peak quality, thorough
Session 50%  → Starts rushing, "I'll be brief"  
Session 70%  → Hallucinations, forgotten requirements
Session 90%  → Broken code, contradictions

With GSD:
Every subagent → 0% → Peak quality
Main session  → 30% → Stays clean
```

### Example GSD Workflow

```bash
# Start a new feature
/gsd-init "build a marketing mix modeling module with adstock and saturation curves"

# GSD generates: docs/gsd/spec.md
# Review and approve spec, then:

/gsd-plan
# GSD generates: docs/gsd/phases.md with atomic tasks

/gsd-build phase-1
# Fresh subagent implements phase 1, tests, commits

/gsd-build phase-2
# Fresh subagent for phase 2...

/gsd-verify
# Runs full test suite, reports quality score

/gsd-done
# Final changelog, version bump, PR description
```

---

## 15. Gas Town — Your Personal Agent Factory

"Gas Town" is Geoffrey Huntley's term for an **automated agent infrastructure** running continuously, producing code like an assembly line.

The name is from Mad Max: Fury Road — Gas Town is where fuel (computation) is manufactured at scale. In Claude Code terms, your machine becomes a factory where agents work in parallel, overnight, autonomously.

### Gas Town Architecture

```
Gas Town
├── Orchestrator Agent        (decides what to build next)
├── Worker Agents × N         (Ralph loops building in parallel)
├── Quality Gate Agent        (runs tests, blocks bad output)
├── Reviewer Agent            (code review before merge)
└── Git (the shared memory)
```

### Setting Up a Local Gas Town in WSL

```bash
# Directory structure
mkdir -p ~/gas-town/{prompts,logs,output,checkpoints}
cd ~/gas-town
```

**Orchestrator prompt** (`prompts/orchestrator.md`):

```markdown
You are the orchestrator for an autonomous development factory.

Read the backlog from backlog.md.
Pick the highest-priority unstarted task.
Mark it as IN_PROGRESS.
Write its spec to prompts/worker-current.md.
Write TASK_ASSIGNED when done.
```

**Worker loop** (`worker.sh`):

```bash
#!/bin/bash
WORKER_ID=$1
LOG="logs/worker-${WORKER_ID}.log"

while true; do
    # Wait for orchestrator to assign a task
    until grep -q "TASK_ASSIGNED" prompts/worker-current.md 2>/dev/null; do
        sleep 5
    done
    
    echo "[Worker $WORKER_ID] Starting task" >> $LOG
    
    # Ralph loop for this task
    for iter in $(seq 1 20); do
        claude \
            --dangerously-skip-permissions \
            -p "$(cat prompts/worker-current.md)" \
            --model claude-sonnet-4-6 \
            >> $LOG 2>&1
        
        if npm test >> $LOG 2>&1; then
            git add -A && git commit -m "gas-town: worker-$WORKER_ID iter-$iter"
            echo "TASK_COMPLETE" >> prompts/worker-current.md
            break
        fi
    done
    
    sleep 10
done
```

**Launch Gas Town**:

```bash
# Start 3 parallel workers
for i in 1 2 3; do
    ./worker.sh $i &
done

# Start orchestrator loop
while true; do
    claude -p "$(cat prompts/orchestrator.md)" --model claude-opus-4-7
    sleep 30
done
```

### Real Results

A Y Combinator hackathon team used a Gas Town setup to produce **1,100+ commits across 6 repos overnight** for ~$800 in AI costs. This is the power of treating Claude Code as an assembly line, not a chatbot.

### Gas Town Safety Rules

1. **Always use git worktrees** — each worker gets its own branch
2. **Always set max-iterations** — never let a worker loop forever
3. **Gate on tests** — never merge unless test suite passes
4. **Monitor token spend** — parallel agents = parallel billing
5. **Start small** — test with 1 worker, 5 iterations before scaling

---

## 16. Putting It All Together: Full Stack Demo

Here's a complete project structure combining every feature:

```
my-project/
├── CLAUDE.md                          ← Project constitution
├── .claude/
│   ├── mcp.json                       ← MCP server config
│   ├── commands/
│   │   ├── feature.md                 ← /feature slash command
│   │   ├── code-review.md             ← /code-review slash command
│   │   └── ship.md                    ← /ship (full cycle)
│   ├── agents/
│   │   ├── researcher.md              ← Research subagent
│   │   ├── planner.md                 ← Planning subagent
│   │   ├── backend-agent.md           ← Backend worker
│   │   ├── frontend-agent.md          ← Frontend worker
│   │   └── reviewer-agent.md          ← Review subagent
│   └── skills/
│       ├── code-review/SKILL.md
│       ├── deploy/SKILL.md
│       └── security-audit/SKILL.md
├── backlog.md                         ← Gas Town task queue
├── prompts/
│   ├── orchestrator.md                ← Gas Town orchestrator
│   └── worker-current.md              ← Current worker task
├── scripts/
│   ├── ralph-loop.sh                  ← Ralph loop runner
│   └── gas-town.sh                    ← Gas Town launcher
└── src/
    ├── api/
    ├── frontend/
    └── tests/
```

### The `/ship` Command (Master Workflow)

```markdown
<!-- .claude/commands/ship.md -->
---
description: Full feature lifecycle: research → plan → build → test → review → PR
allowed-tools: Read, Write, Bash
context: orchestrator
---

Feature to ship: $ARGUMENTS

Phase 1 — Research (researcher subagent in fork context):
  /agent researcher "$ARGUMENTS"
  Wait for: docs/research/$ARGUMENTS.md

Phase 2 — Planning (planner subagent):
  /agent planner "$ARGUMENTS"
  Wait for: docs/plans/$ARGUMENTS.md
  Checkpoint: /checkpoint "post-plan-$ARGUMENTS"

Phase 3 — Build (parallel agents via worktrees):
  Spawn backend-agent and frontend-agent simultaneously
  Monitor tasks/*-done.md

Phase 4 — Test:
  bash -c "npm test && poetry run pytest"
  If fail: /rewind "post-plan-$ARGUMENTS", retry once

Phase 5 — Review (reviewer-agent):
  /agent reviewer-agent "$ARGUMENTS"

Phase 6 — PR:
  git push origin feature/$ARGUMENTS
  gh pr create --title "feat: $ARGUMENTS" --body "$(cat docs/plans/$ARGUMENTS.md)"
```

### Starting a Session

```bash
# In WSL
cd ~/projects/my-project
claude

# Kick off a full feature
/ship "add JWT refresh token rotation with Redis session store"

# Or run a Ralph Loop overnight
./scripts/ralph-loop.sh 50 prompts/refactor-auth.md

# Or launch Gas Town for a backlog sprint
./scripts/gas-town.sh 3   # 3 parallel workers
```

---

## Reference: Feature Comparison

| Feature | What It Solves | When to Use |
|---|---|---|
| **CLAUDE.md** | Agent amnesia between sessions | Always — foundation of everything |
| **Plan mode** | Editing before you understand scope | Any non-trivial task; production files |
| **Context mgmt** (`/clear`, `/compact`) | Context rot degrading quality | One session per task; clear between tasks |
| **Permissions** | Approval fatigue + safety | Configure once per project, before real work |
| **Slash Commands** | Repetitive workflows | Any workflow you do more than twice |
| **Checkpoints** | Risky operations / agent mistakes | Built-in; rewind when a change goes wrong |
| **MCP** | External system access | GitHub, DBs, browsers, APIs |
| **Skills** | Token-efficient reusable prompts | Knowledge you need on-demand |
| **Plugins** | Packaged multi-feature extensions | Community workflows |
| **Hooks** | Guaranteed automation/enforcement | Auto-format, block dangerous commands, gate commits |
| **Sub-Agents** | Context isolation for heavy tasks | Tasks > 30% of context window |
| **Agent Teams** | Parallel development | Features with independent frontend/backend work |
| **Ralph Loops** | Autonomous overnight runs | Mechanical tasks with clear completion |
| **GSD** | Structured spec-driven delivery | Complex features, team workflows |
| **Gas Town** | Agent assembly line at scale | Sprinting through a large backlog |

---

## Resources

- **This repo:** [claude-code-healthcare-tutorial](https://github.com/niket-sharma/claude-code-healthcare-tutorial)
- **Project tutorial (Part 2):** `docs/02-caretriage-project.md` in the same repo
- Official docs: https://docs.claude.com/en/docs/claude-code/overview
- Slash commands SDK: https://code.claude.com/docs/en/agent-sdk/slash-commands
- GSD (current/community fork): https://github.com/open-gsd/get-shit-done-redux — original repo `gsd-build/get-shit-done` is no longer actively maintained; audit before installing
- Geoffrey Huntley (Ralph Loop inventor): https://ghuntley.com
- MCP spec: https://modelcontextprotocol.io
- Claude Code changelog: https://code.claude.com/changelog