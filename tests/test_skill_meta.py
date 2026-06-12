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

# backticked bare filenames like `foo.md` — opening backtick must sit directly
# before the name, so path forms (`reference/foo.md`) stay with _REF_RE
_BARE_REF_RE = re.compile(r"`([A-Za-z0-9_\-.]+\.(?:py|md))`")


def _bare_refs(text: str) -> set[str]:
    return set(_BARE_REF_RE.findall(text))


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

    def test_bare_filename_references_exist_in_bundle(self, skill_dir: Path):
        """경로 없이 백틱으로만 지칭한 파일(`foo.md`)도 번들에 실존해야 한다.

        qa-bug-report가 `risk-taxonomy`를 지칭하면서 번들에 파일이 없던
        자기완결성 위반이 경로 형식이 아니라서 탐지를 빠져나간 갭의 회귀 방지."""
        text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        missing = sorted({name for name in _bare_refs(text)
                          if not any(skill_dir.rglob(name))})
        assert missing == [], (
            f"{skill_dir.name}: SKILL.md가 백틱으로 지칭한 파일이 번들에 없음: {missing} "
            "(reference/<name> 경로 형식으로 쓰거나 번들에 파일을 추가할 것)")


class TestBareRefExtraction:
    def test_extracts_bare_filenames_only(self):
        text = ("`risk-taxonomy.md` 기준으로 판정, `scripts/tool.py` 실행, "
                "`shared-reference/policy.md` 참조, `--patch` 옵션, `uv` 필요")
        assert _bare_refs(text) == {"risk-taxonomy.md"}

    def test_detects_missing_file_candidate(self):
        # 존재 검증은 번들 테스트가 하므로, 추출기는 이름만 정확히 뽑으면 된다
        assert _bare_refs("심각도는 `no-such-doc.md` 기준") == {"no-such-doc.md"}


class TestReadmeSkillList:
    def test_readme_list_matches_skill_directories(self):
        readme_skills = set(re.findall(r"^#### `([a-z0-9-]+)`", README.read_text(encoding="utf-8"), re.MULTILINE))
        dir_skills = {d.name for d in SKILL_DIRS}
        assert readme_skills == dir_skills
