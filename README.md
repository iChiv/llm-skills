# skills

My personal collection of Agent Skills, compatible with OpenCode, Claude Code, and DeepSeek TUI.

All skills live under `skills/` and follow the Agent Skills format.

## Installation

Clone into `~/.claude/skills/`:

```bash
git clone https://github.com/iChiv/llm-skills.git ~/.claude/skills/
```

To manage installed skills (list, install, update, remove), use the included skill-manager:

```bash
python ~/.claude/skills/skills/skill-manager/scripts/skill_manager.py list
python ~/.claude/skills/skills/skill-manager/scripts/skill_manager.py status
python ~/.claude/skills/skills/skill-manager/scripts/skill_manager.py update --all
```

## Available skills

| Skill | Description |
|-------|-------------|
| [skill-manager](skills/skill-manager/SKILL.md) | Manage installed Agent Skills: list, install, update, remove |
| [video-downloader](skills/video-downloader/SKILL.md) | Download videos from YouTube, Bilibili, Vimeo, and 1000+ sites |
| [media-converter](skills/media-converter/SKILL.md) | Convert video/audio/image formats via ffmpeg |

## Adding a new skill

1. Create a folder: `skills/<skill-name>/`
2. Add `SKILL.md` with YAML frontmatter
3. Optionally add `scripts/`, `references/`, or `assets/`
4. Commit and push

## Compatibility

- **OpenCode** (via oh-my-opencode) — auto-discovers from `~/.claude/skills/`
- **Claude Code** — uses the same Agent Skills format
- **DeepSeek TUI** — auto-discovers from `~/.claude/skills/`; use `load_skill <name>` to activate
