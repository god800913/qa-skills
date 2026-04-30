"""Sync shared/ and shared-reference/ files into each skill bundle.

Treats shared/ and shared-reference/ as the source of truth. For each
skills/<skill>/scripts/ file that has a same-name counterpart in shared/, this
script overwrites the bundled copy. Same for skills/<skill>/reference/ vs
shared-reference/.

Only overwrites files that ALREADY EXIST in the skill bundle. New files in
shared/ do NOT get auto-added to bundles that haven't opted in (avoids
polluting unrelated skills). To opt a bundle in to a new shared file, create
an empty placeholder of the same name first.

Idempotent. Run before committing, or via pre-commit hook.

Usage:
    python scripts/sync_shared.py               # apply sync, write changes
    python scripts/sync_shared.py --check       # report what would change, exit 1 if drift
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent
SHARED_SCRIPTS = ROOT / "shared"
SHARED_REFERENCE = ROOT / "shared-reference"
SKILLS_DIR = ROOT / "skills"


def _sync_dir(source: Path, target: Path, *, check_only: bool) -> list[str]:
    """Copy each source file into target IF target has a same-name file.

    If check_only is True, no files are mutated; would-be changes are reported
    with a "would-update:" prefix.
    """
    actions: list[str] = []
    if not target.exists() or not source.exists():
        return actions
    for src_file in sorted(source.iterdir()):
        if not src_file.is_file() or src_file.name == "__init__.py":
            continue
        dst_file = target / src_file.name
        if not dst_file.exists():
            continue
        if dst_file.read_bytes() == src_file.read_bytes():
            actions.append(f"unchanged: {dst_file.relative_to(ROOT)}")
            continue
        if check_only:
            actions.append(f"would-update: {dst_file.relative_to(ROOT)}")
        else:
            shutil.copy2(src_file, dst_file)
            actions.append(f"updated: {dst_file.relative_to(ROOT)}")
    return actions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true",
        help="Report what would change without writing. Exit 1 if any drift.",
    )
    args = parser.parse_args()

    if not SKILLS_DIR.exists():
        raise SystemExit(f"No skills dir: {SKILLS_DIR}")

    actions: list[str] = []
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        actions.extend(_sync_dir(SHARED_SCRIPTS, skill_dir / "scripts", check_only=args.check))
        actions.extend(_sync_dir(SHARED_REFERENCE, skill_dir / "reference", check_only=args.check))

    if not actions:
        print("Nothing to sync.")
        return

    for line in actions:
        print(line)

    if args.check and any(a.startswith("would-update:") for a in actions):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
