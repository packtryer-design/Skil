# Third-party notices

This repository MAINLY adapts material from the following open-source projects. The adapted material lives in the files named below; the original projects are not redistributed here (they are kept locally under `references/` for study and ignored by git).

## ai-business-skills

- Upstream: https://github.com/minhnv0807/ai-business-skills
- License: MIT (Copyright (c) 2025 Over Powers Agency)
- Adapted in: `skills/prompt-architect/templates/marketing-plan.md`, `campaign-brief.md`, `ad-copy.md`, `competitor-research.md`, `customer-insight.md`, `content-calendar.md` (condensed and restructured; each file names its source in frontmatter), and the structure of `skill-domain-expert.md`.

## i-have-adhd

- Upstream: https://github.com/ayghri/i-have-adhd
- License: MIT (Copyright (c) 2026 Ayoub Ghriss)
- Adapted in: the packaging layout of this repository (plugin manifests, `AGENTS.md`, `INSTALL.md`), the structure of `skills/prompt-architect/templates/skill-output-style.md` and `skill-plugin-scaffold.md`, and the hook and evaluation guidance in `skills/prompt-architect/references/skill-authoring.md`. No text from the skill itself is reproduced.

## SkillSpector

- Upstream: https://github.com/NVIDIA/SkillSpector
- License: Apache License 2.0 (Copyright NVIDIA Corporation)
- Adapted in: the vulnerability categories, rule identifiers, and explanations summarized in `skills/prompt-architect/references/skill-security.md` and implemented as independent regular-expression checks in `skills/prompt-architect/scripts/pa_skill.py`; the review procedure of its `skill-inspector` skill informs `skills/prompt-architect/templates/skill-tool-wrapper.md`. No SkillSpector source code is included.

MIT License text (applies to the ai-business-skills and i-have-adhd adaptations):

```text
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

Apache License 2.0 (applies to the SkillSpector adaptation): https://www.apache.org/licenses/LICENSE-2.0
