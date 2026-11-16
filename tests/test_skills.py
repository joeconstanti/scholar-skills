"""Lint every skill: frontmatter, name, description length and local links."""
import re, unittest
from pathlib import Path

SKILLS = Path(__file__).parents[1] / "skills"
LINK = re.compile(r"\]\(([^)#:]+)\)")

def frontmatter(text):
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not match: return None
    return dict(line.split(":", 1) for line in match.group(1).splitlines() if ":" in line)

class SkillLint(unittest.TestCase):
    def test_every_skill_is_valid(self):
        dirs = [d for d in SKILLS.iterdir() if d.is_dir()]
        self.assertTrue(dirs)
        for skill in dirs:
            with self.subTest(skill=skill.name):
                text = (skill / "SKILL.md").read_text(encoding="utf-8")
                meta = frontmatter(text)
                self.assertIsNotNone(meta, "missing frontmatter")
                self.assertEqual(meta["name"].strip(), skill.name)
                self.assertRegex(skill.name, r"^[a-z0-9-]{1,64}$")
                description = meta["description"].strip()
                self.assertTrue(20 <= len(description) <= 1024)
                self.assertLess(len(text.splitlines()), 500, "keep SKILL.md under 500 lines")
                for md in skill.rglob("*.md"):
                    for target in LINK.findall(md.read_text(encoding="utf-8")):
                        self.assertTrue((md.parent / target).exists(), f"{md.name}: broken link {target}")

if __name__ == "__main__": unittest.main()
