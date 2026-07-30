---
name: adaptive-writing
description: 독자, 톤, 용어, 구조, 정보 밀도를 맞춰야 하는 한국어·영어 텍스트를 쓰거나 고칩니다. 다시 쓰기, 교정, 요약, 번역, README·문서 수정, 대표 보고용 메모, 독자 수준 설명, rewrite, proofread, executive memo. 일상 대화나 다른 스킬이 글을 만든다는 이유로는 쓰지 않습니다.
---

# Adaptive Writing

Write for a reader who can work across product, planning, marketing, frontend,
and development but does not want unexplained low-level jargon or beginner
lectures.

## Calibrate

1. Read the user profile path injected at session start.
2. Identify the document's purpose, reader, and decision or action.
3. Use known product, marketing, and frontend terms normally.
4. Explain unfamiliar infrastructure, architecture, data, or language-runtime
   terms once in plain language, then use the exact term.
5. Match the density of the request. A short question should not trigger a report.

If the user provides writing samples or corrections, treat them as stronger
evidence than this default. Store an explicit durable preference in the global
profile only when the user asks or the evidence is stable.

## Compose

- Lead with the outcome, recommendation, or finding.
- Follow with why it matters, evidence, and the next action.
- Prefer concrete nouns, verbs, numbers, examples, and mechanisms over adjectives.
- Make fact, inference, assumption, and recommendation distinguishable.
- State only assumptions that affect the result.
- Remove repeated conclusions, generic introductions, and ceremonial summaries.
- Keep headings proportional to length. Do not turn every paragraph into a section.

For Markdown creation or substantial editing, read
[references/markdown-rules.md](references/markdown-rules.md).

Strings that live inside a screen (button labels, toasts, error messages, empty
states, form helpers) are interface parts, not prose. Use the ux-writing skill
for those.

## Task formats

### Review

Show findings first, ordered by impact:

1. finding
2. consequence
3. evidence or location
4. concrete correction

Do not hide actionable findings behind a long overview.

### Plan or proposal

Show:

1. recommended direction
2. key assumptions
3. sequence and artifacts
4. success measure
5. risks or unresolved decisions

### Technical explanation

Use this order:

1. what happened or what to choose
2. why it matters to the product or work
3. the simplest accurate mental model
4. implementation detail only as needed

## Quality gate

Before delivering, check:

- The first paragraph answers the actual question.
- The user can identify the next action without rereading.
- No section exists only because a template had one.
- Terms are accurate and explained at the right altitude.
- Claims that can age have a source and verification date.
- An edit preserves the surrounding document's established style.
