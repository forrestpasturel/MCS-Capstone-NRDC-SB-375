from __future__ import annotations

from pathlib import Path
import shutil

import yaml

from src.pipeline.utils import abs_path, load_config


def find_matches(search_roots: list[str], patterns: list[str]) -> list[Path]:
    matches: list[Path] = []
    for root in search_roots:
        root_path = Path(root)
        if not root_path.exists():
            continue
        for pattern in patterns:
            matches.extend(root_path.glob(pattern))
    # De-duplicate while preserving order
    seen: set[Path] = set()
    uniq: list[Path] = []
    for m in matches:
        if m.is_file() and m not in seen:
            seen.add(m)
            uniq.append(m)
    return uniq


def looks_like_placeholder(path: Path) -> bool:
    # Simple heuristic: tiny files are usually placeholders.
    try:
        return path.stat().st_size < 200
    except OSError:
        return True


def main() -> None:
    cfg = load_config()
    staging_cfg_path = abs_path("config/data_staging.yaml")

    with open(staging_cfg_path, "r", encoding="utf-8") as f:
        staging_cfg = yaml.safe_load(f)

    search_roots = staging_cfg.get("search_roots", [])
    pattern_map = staging_cfg.get("patterns", {})

    required_targets = [Path(p).name for p in cfg["paths"].values()]

    raw_dir = abs_path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    staged = 0
    unresolved: list[str] = []

    for target_name in required_targets:
        target_path = raw_dir / target_name

        candidate_patterns = pattern_map.get(target_name, [])
        matches = find_matches(search_roots, candidate_patterns)

        # Filter out already-staged target itself and obvious placeholders.
        matches = [m for m in matches if m.resolve() != target_path.resolve() and not looks_like_placeholder(m)]

        if not matches:
            unresolved.append(target_name)
            continue

        # Choose newest modified file among candidates.
        source = sorted(matches, key=lambda p: p.stat().st_mtime, reverse=True)[0]
        shutil.copy2(source, target_path)
        staged += 1
        print(f"Staged {target_name} <- {source}")

    print(f"Staged {staged} dataset(s).")
    if unresolved:
        print("Unresolved targets:")
        for name in unresolved:
            print(f"- {name}")


if __name__ == "__main__":
    main()
