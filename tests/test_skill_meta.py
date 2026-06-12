"""Meta tests for skill bundle integrity.

Locks in three invariants:
- every skills/*/SKILL.md has frontmatter with name (== directory) and description
- every bundle-relative path mentioned in a SKILL.md actually exists in that bundle
- the README skill list matches the skills/ directories exactly
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SKILLS_DIR = ROOT / "skills"
README = ROOT / "README.md"

SKILL_DIRS = sorted(d for d in SKILLS_DIR.iterdir() if d.is_dir())

# bundle-relative paths like scripts/foo.py, reference/bar.md, examples/baz.md
# (negative lookbehind keeps shared-reference/... from matching as reference/...)
_REF_RE = re.compile(r"(?<![\w-])(?:scripts|reference|examples)/[A-Za-z0-9_\-.]+\.(?:py|md)")


def _frontmatter(skill_md: Path) -> dict:
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return {}
    fields = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()
    return fields


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=lambda d: d.name)
class TestSkillMd:
    def test_has_frontmatter_name_and_description(self, skill_dir: Path):
        fm = _frontmatter(skill_dir / "SKILL.md")
        assert fm.get("name"), f"{skill_dir.name}: frontmatter name 누락"
        assert fm.get("description"), f"{skill_dir.name}: frontmatter description 누락"

    def test_frontmatter_name_matches_directory(self, skill_dir: Path):
        fm = _frontmatter(skill_dir / "SKILL.md")
        assert fm.get("name") == skill_dir.name

    def test_referenced_bundle_files_exist(self, skill_dir: Path):
        text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        missing = sorted({ref for ref in _REF_RE.findall(text)
                          if not (skill_dir / ref).exists()})
        assert missing == [], f"{skill_dir.name}: SKILL.md가 참조하는 파일 없음: {missing}"


class TestReadmeSkillList:
    def test_readme_list_matches_skill_directories(self):
        readme_skills = set(re.findall(r"^#### `([a-z0-9-]+)`", README.read_text(encoding="utf-8"), re.MULTILINE))
        dir_skills = {d.name for d in SKILL_DIRS}
        assert readme_skills == dir_skills
