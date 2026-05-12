---
name: skill-manager
description: Manage installed Agent Skills on this machine. Use when the user asks to list skills, inspect their metadata, track local vs upstream versions, sync/update skills from GitHub, or install/remove skills.
license: MIT
compatibility: Requires Python 3 and internet access for GitHub sync.
metadata:
  default_repo: iChiv/skills
---

# Skill Manager

This skill manages skills installed under `~/.claude/skills/`.

OpenCode (via oh-my-opencode) uses the Agent Skills format and this same directory layout, so the `~/.claude` path is expected even when you are not using Claude Code.

DeepSeek TUI also discovers skills from `~/.claude/skills/` using the same Agent Skills format. Use `load_skill skill-manager` inside DeepSeek TUI to activate skill management.

It can:
- List installed skills (name + description + license + files)
- Track upstream source (repo/path) and show local vs upstream version
- Install / update / remove skills safely (backup + trash)

## Where skills live

- User-level skills root: `~/.claude/skills/`
- Each skill is a folder containing `SKILL.md` and optional `scripts/`, `references/`, `assets/`, etc.

This manager stores its own state in:

- `~/.claude/skills/.skill-manager/registry.json`
- Backups: `~/.claude/skills/.skill-manager/backups/`
- Trash (for removed skills): `~/.claude/skills/.skill-manager/trash/`

## Versioning model

Many skill repos (including `anthropics/skills`) have no releases/tags. The manager uses Git commit SHA as the upstream "repo version".

Local version is:
- `installed_commit` if the skill was installed/updated via this manager
- otherwise `untracked`

## CLI helper

Use the helper script:

`scripts/skill_manager.py`

Run examples:

```bash
python "~/.claude/skills/skill-manager/scripts/skill_manager.py" list
python "~/.claude/skills/skill-manager/scripts/skill_manager.py" status

# Install a skill from anthropics/skills (default)
python "~/.claude/skills/skill-manager/scripts/skill_manager.py" install pdf

# Update one skill (backs up existing first)
python "~/.claude/skills/skill-manager/scripts/skill_manager.py" update pdf

# Update all skills that have a known upstream
python "~/.claude/skills/skill-manager/scripts/skill_manager.py" update --all

# Remove a skill (moves to trash instead of deleting)
python "~/.claude/skills/skill-manager/scripts/skill_manager.py" remove pdf
```

Windows PowerShell:

```powershell
python "$env:USERPROFILE\.claude\skills\skill-manager\scripts\skill_manager.py" list
python "$env:USERPROFILE\.claude\skills\skill-manager\scripts\skill_manager.py" status
```

## Source mapping

By default, skills with names that match `anthropics/skills` are treated as:

- repo: `anthropics/skills`
- path: `skills/<skill-name>`

For custom skills, set an upstream explicitly:

```bash
python "/c/Users/happyelements/.claude/skills/skill-manager/scripts/skill_manager.py" set-source yt-dlp --repo yt-dlp/yt-dlp --path .
```

Notes:
- `set-source` only records metadata; it does not attempt to install from repos that are not in Agent Skills format.
- For non-Agent-Skills repos (like `yt-dlp/yt-dlp`), keep the skill itself local and just record the origin repo for reference.

## Safety rules

- Update/install always supports `--dry-run`.
- Update/install backs up existing skill folders before overwriting.
- Remove moves a skill folder into trash (restorable) instead of deleting.