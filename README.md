# skill-manager (Agent Skill)

Manage Agent Skills installed under `~/.claude/skills/`.

This repo is intended to be installed as a skill directory:

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

GitHub API access:

- Set `GITHUB_TOKEN` to avoid rate limits.

## Files

- `SKILL.md`: skill metadata + usage
- `scripts/skill_manager.py`: CLI implementation
