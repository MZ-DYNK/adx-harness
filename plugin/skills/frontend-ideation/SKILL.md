---
name: frontend-ideation
description: 웹사이트, 앱, 랜딩페이지, 대시보드, 화면, 디자인 시스템, UI 컴포넌트의 디자인을 결정합니다. 시각적 방향, 정보 위계, 레이아웃, 상호작용, 상태 처리, 반응형, 접근성, 컴포넌트 구성, 디자인 취향 축적, visual hierarchy, responsive, accessibility. 구현 버그, API·데이터 로직, 컴포넌트 단위 테스트, UI 테스트 실패에는 쓰지 않습니다.
---

# Frontend Ideation

Make the interface appropriate to the product and repeated user task before
making it decorative.

## Gather context

1. Inspect the existing product, frontend stack, design tokens, component library,
   and representative screens.
2. Read `.harness/DESIGN.md` and the global design-taste path injected at session
   start.
3. Define the interface purpose, primary audience, usage frequency, content
   density, desired tone, and technical constraints.
4. Identify one memorable design idea that supports the product rather than
   competing with it.

Read [references/design-lenses.md](references/design-lenses.md) when setting a
new direction. Read [references/archive-format.md](references/archive-format.md)
when capturing references, feedback, patterns, or components.

## Ideate

For open-ended ideation, propose two or three meaningfully different directions,
not cosmetic variants. For each direction show:

- visual thesis
- information hierarchy and layout
- typography and density
- color and material behavior
- interaction and motion
- signature component or moment
- trade-off and best-fit context

Recommend one direction and explain why it fits the product, audience, and
existing system.

## Build or revise

- Put the actual product or primary workflow in the first viewport.
- Reuse current tokens, components, icons, and interaction conventions before
  adding a new system.
- Design all relevant states: loading, empty, error, disabled, hover, focus,
  selected, success, and destructive.
- Define mobile and desktop behavior explicitly.
- Use motion to clarify hierarchy or state, not to decorate latency.
- Check content fit, contrast, keyboard use, focus visibility, and reduced motion.
- Avoid nested cards, generic gradient heroes, decorative blobs, oversized
  headings, and landing-page compositions imposed on operational tools.

## Learn taste

After explicit feedback:

- Record project-specific choices in `.harness/DESIGN.md`.
- Record global preference only when the user states it directly or the pattern
  repeats across projects.
- Mark ideas as `adopted`, `held`, or `rejected` with the reason.
- Preserve the reason and use condition, not only a screenshot or link.

## Quality gate

- The first viewport communicates the product and primary action.
- The hierarchy supports scanning and repeated use.
- The direction is distinct for a reason, not novelty alone.
- Components cover content variability and interaction states.
- The result respects existing product conventions or documents why it departs.
- The archive was updated only with durable learning.
