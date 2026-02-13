# opencode-skill-manager (Agent Skill)

Skill to manage Agent Skills installed for OpenCode (via oh-my-opencode).

OpenCode reuses the Agent Skills format and the default skills location:

- `~/.claude/skills/`

This repo is intended to be installed as a skill directory (OpenCode / oh-my-opencode discovery):

- `~/.claude/skills/skill-manager/`
  - `SKILL.md`
  - `scripts/skill_manager.py`

## What it does

- List installed skills and their upstream source
- Show status (local vs upstream) for:
  - Agent Skills repos (commit SHA)
  - Tool-based skills (e.g. yt-dlp: local `yt-dlp --version` vs GitHub `releases/latest`)
- Install/update skills from GitHub (with backups)
- Remove skills safely (move to trash)

## Quick start

Run via Python:

```bash
python "~/.claude/skills/skill-manager/scripts/skill_manager.py" list
python "~/.claude/skills/skill-manager/scripts/skill_manager.py" status
python "~/.claude/skills/skill-manager/scripts/skill_manager.py" update --all
```

Windows PowerShell:

```powershell
python "$env:USERPROFILE\.claude\skills\skill-manager\scripts\skill_manager.py" list
python "$env:USERPROFILE\.claude\skills\skill-manager\scripts\skill_manager.py" status
python "$env:USERPROFILE\.claude\skills\skill-manager\scripts\skill_manager.py" update --all
```

GitHub API access:

- Set `GITHUB_TOKEN` to avoid rate limits.

## Compatibility

- Works in OpenCode via oh-my-opencode.
- Uses the same `SKILL.md` format and `~/.claude/skills/` conventions as the upstream Agent Skills ecosystem.

## Files

- `SKILL.md`: skill metadata + usage
- `scripts/skill_manager.py`: CLI implementation
