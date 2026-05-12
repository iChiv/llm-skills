#!/usr/bin/env python3
"""Skill manager for ~/.claude/skills.

Supports:
- list installed skills
- show status vs upstream GitHub repo commit
- install/update skills from GitHub (commit SHA based)
- remove skills (move to trash)

This script intentionally avoids third-party dependencies.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
import urllib.error


DEFAULT_UPSTREAM_REPO = "anthropics/skills"


def _utc_now_iso() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat()


def _skills_root() -> Path:
    override = os.environ.get("SKILLS_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return (Path.home() / ".claude" / "skills").resolve()


def _state_dir(root: Path) -> Path:
    return root / ".skill-manager"


def _registry_path(root: Path) -> Path:
    return _state_dir(root) / "registry.json"


def _ensure_state_dirs(root: Path) -> None:
    (_state_dir(root) / "backups").mkdir(parents=True, exist_ok=True)
    (_state_dir(root) / "trash").mkdir(parents=True, exist_ok=True)


def _load_registry(root: Path) -> dict:
    _ensure_state_dirs(root)
    p = _registry_path(root)
    if not p.exists():
        reg = {"skills": {}}
        _bootstrap_self(root, reg)
        return {"skills": {}}
    try:
        reg = json.loads(p.read_text(encoding="utf-8"))
        _bootstrap_self(root, reg)
        return reg
    except Exception:
        return {"skills": {}}


def _save_registry(root: Path, reg: dict) -> None:
    _ensure_state_dirs(root)
    p = _registry_path(root)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(reg, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(p)


def _bootstrap_self(root: Path, reg: dict) -> None:
    """Auto-register skill-manager itself so it can track its own updates."""
    if "skill-manager" not in reg.get("skills", {}):
        try:
            commit = _local_git_commit(root / "skill-manager")
        except Exception:
            commit = None
        reg.setdefault("skills", {})["skill-manager"] = {
            "repo": "Redox-OX/opencode-skill-manager",
            "path": ".",
            "installed_commit": commit,
            "installed_at": _utc_now_iso(),
        }

def _read_skill_frontmatter(skill_md: Path) -> dict:
    """Parse a minimal YAML frontmatter block without a YAML dependency.

We only support:
- top-level `key: value` scalars
- `metadata:` map with `  k: v` lines
"""

    try:
        text = skill_md.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = skill_md.read_text(encoding="utf-8", errors="replace")

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}

    block = lines[1:end]
    out: dict = {}
    i = 0
    while i < len(block):
        line = block[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if line.startswith("metadata:"):
            md = {}
            i += 1
            while i < len(block) and (block[i].startswith("  ") or block[i].startswith("\t")):
                raw = block[i].strip()
                if not raw or raw.startswith("#"):
                    i += 1
                    continue
                if ":" in raw:
                    k, v = raw.split(":", 1)
                    md[k.strip()] = v.strip().strip('"').strip("'")
                i += 1
            out["metadata"] = md
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
        i += 1

    return out


def _iter_installed_skills(root: Path):
    if not root.exists():
        return
    for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir():
            continue
        if child.name.startswith("."):
            continue
        skill_md = child / "SKILL.md"
        if skill_md.exists():
            yield child


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _dir_digest(dir_path: Path) -> str:
    """Stable digest of all files in a directory."""
    h = hashlib.sha256()
    for p in sorted(dir_path.rglob("*"), key=lambda x: str(x).lower()):
        if p.is_dir():
            continue
        rel = str(p.relative_to(dir_path)).replace("\\", "/")
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(_sha256_file(p).encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


def _http_get_json(url: str) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "skill-manager/1.0",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        return json.loads(data.decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = b""
        try:
            body = e.read() or b""
        except Exception:
            body = b""
        body_text = ""
        try:
            body_text = body.decode("utf-8", errors="replace")
        except Exception:
            body_text = ""
        if e.code == 403 and "rate limit" in body_text.lower():
            raise RuntimeError(
                "GitHub API rate limit exceeded. Set GITHUB_TOKEN (or GH_TOKEN) and retry."
            ) from e
        raise


def _github_head_commit(repo: str) -> dict:
    q = urllib.parse.urlencode({"per_page": 1})
    url = f"https://api.github.com/repos/{repo}/commits?{q}"
    data = _http_get_json(url)
    if not isinstance(data, list) or not data:
        raise RuntimeError(f"No commits found for {repo}")
    c = data[0]
    return {
        "sha": c.get("sha"),
        "date": c.get("commit", {}).get("author", {}).get("date"),
        "message": (c.get("commit", {}).get("message") or "").splitlines()[0],
    }


def _github_latest_release_tag(repo: str) -> str:
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    data = _http_get_json(url)
    if not isinstance(data, dict):
        raise RuntimeError(f"Unexpected latest release response for {repo}")
    tag = data.get("tag_name")
    if not isinstance(tag, str) or not tag.strip():
        raise RuntimeError(f"No tag_name in latest release for {repo}")
    return tag.strip()


def _run_version_command(cmd: list[str]) -> str:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError as e:
        raise RuntimeError(f"Command not found: {cmd[0]}") from e
    out = (p.stdout or "").strip()
    if not out:
        out = (p.stderr or "").strip()
    out = out.splitlines()[0].strip() if out else ""
    if not out:
        raise RuntimeError(f"No version output from: {' '.join(cmd)}")
    return out


def _github_tree(repo: str, commit_sha: str) -> list[dict]:
    url = f"https://api.github.com/repos/{repo}/git/trees/{commit_sha}?recursive=1"
    data = _http_get_json(url)
    tree = data.get("tree") if isinstance(data, dict) else None
    if not isinstance(tree, list):
        raise RuntimeError(f"Unexpected tree response for {repo}@{commit_sha}")
    return tree


def _github_raw_url(repo: str, commit_sha: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{repo}/{commit_sha}/{path}"


def _download_bytes(url: str) -> bytes:
    headers = {"User-Agent": "skill-manager/1.0"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def _backup_dir(root: Path, skill_name: str, src_dir: Path) -> Path:
    ts = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    dst = _state_dir(root) / "backups" / skill_name / ts
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src_dir, dst)
    return dst


def _trash_dir(root: Path, skill_name: str, src_dir: Path) -> Path:
    ts = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    dst = _state_dir(root) / "trash" / skill_name / ts
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src_dir), str(dst))
    return dst


def _default_source_for(name: str) -> tuple[str, str] | None:
    # Default mapping for anthropics/skills.
    # This list is intentionally conservative; set-source overrides it.
    known = {
        "algorithmic-art",
        "brand-guidelines",
        "canvas-design",
        "doc-coauthoring",
        "docx",
        "frontend-design",
        "internal-comms",
        "mcp-builder",
        "pdf",
        "pptx",
        "skill-creator",
        "slack-gif-creator",
        "theme-factory",
        "web-artifacts-builder",
        "webapp-testing",
        "xlsx",
    }
    if name in known:
        return (DEFAULT_UPSTREAM_REPO, f"skills/{name}")
    return None


def cmd_list(args: argparse.Namespace) -> int:
    root = _skills_root()
    reg = _load_registry(root)

    items = []
    for d in _iter_installed_skills(root):
        fm = _read_skill_frontmatter(d / "SKILL.md")
        name = fm.get("name") or d.name
        desc = fm.get("description") or ""
        lic = fm.get("license") or ""
        src = reg.get("skills", {}).get(name, {})
        if not src.get("repo") or not src.get("path"):
            default = _default_source_for(name)
            if default:
                src = {**src, "repo": default[0], "path": default[1]}
        items.append(
            {
                "name": name,
                "description": desc,
                "license": lic,
                "repo": src.get("repo"),
                "path": src.get("path"),
                "installed_commit": src.get("installed_commit"),
            }
        )

    if args.json:
        sys.stdout.write(json.dumps(items, indent=2, ensure_ascii=True) + "\n")
        return 0

    for it in items:
        repo = it.get("repo") or "-"
        path = it.get("path") or "-"
        loc = it.get("installed_commit") or "untracked"
        sys.stdout.write(f"{it['name']}\n")
        if it.get("description"):
            sys.stdout.write(f"  {it['description']}\n")
        if it.get("license"):
            sys.stdout.write(f"  license: {it['license']}\n")
        sys.stdout.write(f"  origin: {repo} {path}\n")
        sys.stdout.write(f"  local:  {loc}\n")
    return 0


def cmd_set_source(args: argparse.Namespace) -> int:
    root = _skills_root()
    reg = _load_registry(root)
    reg.setdefault("skills", {})
    entry = reg["skills"].setdefault(args.name, {})
    entry["repo"] = args.repo
    entry["path"] = args.path
    entry["source_set_at"] = _utc_now_iso()
    _save_registry(root, reg)
    sys.stdout.write(f"OK: set source for {args.name} -> {args.repo}:{args.path}\n")
    return 0


def cmd_set_tool(args: argparse.Namespace) -> int:
    root = _skills_root()
    reg = _load_registry(root)
    reg.setdefault("skills", {})
    entry = reg["skills"].setdefault(args.name, {})
    entry["tool"] = {
        "command": args.command,
        "args": args.args or [],
    }
    entry["tool_set_at"] = _utc_now_iso()
    _save_registry(root, reg)
    sys.stdout.write(
        f"OK: set tool for {args.name} -> {args.command} {' '.join(args.args or [])}\n"
    )
    return 0


def _resolve_source(root: Path, reg: dict, name: str, repo: str | None, path: str | None) -> tuple[str, str]:
    if repo and path:
        return repo, path
    entry = reg.get("skills", {}).get(name, {})
    r = entry.get("repo")
    p = entry.get("path")
    if r and p:
        return r, p
    default = _default_source_for(name)
    if default:
        return default
    raise RuntimeError(
        f"No upstream source for '{name}'. Use set-source or pass --repo/--path."
    )


def _download_skill_tree(repo: str, skill_path: str, commit_sha: str, dest_dir: Path, dry_run: bool) -> list[str]:
    tree = _github_tree(repo, commit_sha)
    prefix = skill_path.rstrip("/") + "/"

    blobs = [x for x in tree if x.get("type") == "blob" and str(x.get("path", "")).startswith(prefix)]
    if not blobs:
        raise RuntimeError(f"No files found under {repo}@{commit_sha}:{skill_path}")

    written: list[str] = []
    for b in blobs:
        rel = str(b["path"])[len(prefix) :]
        out_path = dest_dir / rel
        written.append(str(out_path))
        if dry_run:
            continue
        out_path.parent.mkdir(parents=True, exist_ok=True)
        url = _github_raw_url(repo, commit_sha, b["path"])
        data = _download_bytes(url)
        out_path.write_bytes(data)
    return written


def _install_or_update(
    *,
    action: str,
    name: str,
    repo: str,
    path: str,
    all_flag: bool,
    dry_run: bool,
    force: bool,
) -> int:
    root = _skills_root()
    reg = _load_registry(root)
    reg.setdefault("skills", {})

    targets: list[str]
    if all_flag:
        targets = [
            _read_skill_frontmatter((d / "SKILL.md")).get("name") or d.name
            for d in _iter_installed_skills(root)
        ]
    else:
        targets = [name]

    head_cache: dict[str, dict] = {}

    for t in targets:
        try:
            r, p = _resolve_source(
                root,
                reg,
                t,
                repo if not all_flag else None,
                path if not all_flag else None,
            )
        except Exception as e:
            if all_flag:
                sys.stdout.write(f"skip: {t} (no upstream: {e})\n")
                continue
            raise
        latest = head_cache.get(r)
        if latest is None:
            try:
                latest = _github_head_commit(r)
            except Exception as e:
                # In --all mode, avoid crashing the whole run.
                if all_flag:
                    sys.stdout.write(f"stop: unable to fetch upstream for {r} ({e})\n")
                    break
                raise
            head_cache[r] = latest
        commit_sha = latest["sha"]
        if not commit_sha:
            raise RuntimeError(f"Unable to resolve latest commit for {r}:{p}")

        dest = root / t
        if dest.exists():
            # Backup before overwrite.
            if not dry_run:
                _backup_dir(root, t, dest)
        else:
            if action == "update" and not force:
                # Update implies installed skill; allow force to treat as install.
                raise RuntimeError(f"Skill '{t}' is not installed. Use install, or update --force.")

        if dry_run:
            sys.stdout.write(f"{action}: {t} -> {r}@{commit_sha[:8]}:{p}\n")
        else:
            if dest.exists():
                shutil.rmtree(dest)
            dest.mkdir(parents=True, exist_ok=True)
            _download_skill_tree(r, p, commit_sha, dest, dry_run=False)

            entry = reg["skills"].setdefault(t, {})
            entry["repo"] = r
            entry["path"] = p
            entry["installed_commit"] = commit_sha
            entry["installed_commit_date"] = latest.get("date")
            entry["installed_commit_message"] = latest.get("message")
            entry["installed_at"] = _utc_now_iso()
            entry["installed_digest"] = _dir_digest(dest)

            _save_registry(root, reg)
            sys.stdout.write(f"{action}: OK {t} @ {commit_sha[:8]}\n")

    return 0


def cmd_install(args: argparse.Namespace) -> int:
    repo, path = _resolve_source(_skills_root(), _load_registry(_skills_root()), args.name, args.repo, args.path)
    return _install_or_update(
        action="install",
        name=args.name,
        repo=repo,
        path=path,
        all_flag=False,
        dry_run=args.dry_run,
        force=True,
    )


def cmd_update(args: argparse.Namespace) -> int:
    return _install_or_update(
        action="update",
        name=args.name or "",
        repo=args.repo,
        path=args.path,
        all_flag=bool(args.all),
        dry_run=args.dry_run,
        force=bool(args.force),
    )


def cmd_remove(args: argparse.Namespace) -> int:
    root = _skills_root()
    dest = root / args.name
    if not dest.exists():
        raise RuntimeError(f"Skill not found: {args.name}")
    if args.dry_run:
        sys.stdout.write(f"remove: {args.name} -> trash\n")
        return 0
    _trash_dir(root, args.name, dest)
    sys.stdout.write(f"remove: OK {args.name}\n")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = _skills_root()
    reg = _load_registry(root)
    reg.setdefault("skills", {})

    head_cache: dict[str, dict] = {}

    release_cache: dict[str, str] = {}

    for d in _iter_installed_skills(root):
        fm = _read_skill_frontmatter(d / "SKILL.md")
        name = fm.get("name") or d.name
        entry = reg.get("skills", {}).get(name, {})
        tool = entry.get("tool") if isinstance(entry.get("tool"), dict) else None
        r = entry.get("repo")
        p = entry.get("path")
        if not r or not p:
            default = _default_source_for(name)
            if default:
                r, p = default
        local_commit = entry.get("installed_commit")
        local_state = local_commit[:8] if isinstance(local_commit, str) else "untracked"

        # Tool-mode status (e.g., yt-dlp): compare local tool version vs upstream release.
        if tool and tool.get("command"):
            cmd = [str(tool.get("command"))] + [str(x) for x in (tool.get("args") or [])]
            try:
                local_ver = _run_version_command(cmd)
            except Exception as e:
                sys.stdout.write(f"{name}: tool=error ({e})\n")
                continue
            if r:
                try:
                    remote_ver = release_cache.get(r)
                    if remote_ver is None:
                        remote_ver = _github_latest_release_tag(r)
                        release_cache[r] = remote_ver
                    if local_ver == remote_ver:
                        status = "up-to-date"
                    else:
                        status = "out-of-date"
                    sys.stdout.write(
                        f"{name}: {status} local={local_ver} upstream={remote_ver} ({r}:releases/latest)\n"
                    )
                except Exception as e:
                    sys.stdout.write(f"{name}: local={local_ver} upstream=error ({e})\n")
                continue
            sys.stdout.write(f"{name}: local={local_ver} upstream=unknown\n")
            continue

        if not r or not p:
            sys.stdout.write(f"{name}: local={local_state} upstream=unknown\n")
            continue

        try:
            latest = head_cache.get(r)
            if latest is None:
                latest = _github_head_commit(r)
                head_cache[r] = latest
            remote_sha = latest.get("sha") or ""
            remote_state = remote_sha[:8] if remote_sha else "unknown"
        except Exception as e:
            sys.stdout.write(f"{name}: local={local_state} upstream=error ({e})\n")
            if "rate limit" in str(e).lower():
                break
            continue

        if local_commit and remote_sha and local_commit == remote_sha:
            status = "up-to-date"
        elif local_commit and remote_sha:
            status = "out-of-date"
        else:
            status = "untracked"
        sys.stdout.write(f"{name}: {status} local={local_state} upstream={remote_state} ({r}:{p})\n")

    return 0


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="skill_manager.py")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("list", help="List installed skills")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("status", help="Show local vs upstream status")
    sp.set_defaults(func=cmd_status)

    sp = sub.add_parser("set-source", help="Record upstream repo/path for a skill")
    sp.add_argument("name")
    sp.add_argument("--repo", required=True, help="GitHub repo, e.g. owner/name")
    sp.add_argument("--path", required=True, help="Path inside repo, e.g. skills/pdf")
    sp.set_defaults(func=cmd_set_source)

    sp = sub.add_parser("set-tool", help="Record a local tool version command for a skill")
    sp.add_argument("name")
    sp.add_argument("--command", required=True, help="Executable name, e.g. yt-dlp")
    sp.add_argument(
        "--args",
        nargs=argparse.REMAINDER,
        help="Args to print version, e.g. --version (all remaining tokens are captured)",
    )
    sp.set_defaults(func=cmd_set_tool)

    sp = sub.add_parser("install", help="Install a skill from GitHub")
    sp.add_argument("name")
    sp.add_argument("--repo", help="GitHub repo (defaults to anthropics/skills when known)")
    sp.add_argument("--path", help="Path inside repo (defaults to skills/<name> when known)")
    sp.add_argument("--dry-run", action="store_true")
    sp.set_defaults(func=cmd_install)

    sp = sub.add_parser("update", help="Update skills from GitHub (backup then overwrite)")
    sp.add_argument("name", nargs="?")
    sp.add_argument("--all", action="store_true", help="Update all installed skills with known upstream")
    sp.add_argument("--repo", help="Override repo for single-skill update")
    sp.add_argument("--path", help="Override path for single-skill update")
    sp.add_argument("--force", action="store_true", help="Allow update even if skill is not installed")
    sp.add_argument("--dry-run", action="store_true")
    sp.set_defaults(func=cmd_update)

    sp = sub.add_parser("remove", help="Remove a skill (move to trash)")
    sp.add_argument("name")
    sp.add_argument("--dry-run", action="store_true")
    sp.set_defaults(func=cmd_remove)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        raise SystemExit(130)