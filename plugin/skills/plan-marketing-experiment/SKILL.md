---
name: plan-marketing-experiment
description: 소재·메시지·오퍼·랜딩 신호를 통제된 마케팅 실험으로 바꿉니다. 위닝·고효율 소재, 소재 피로도, A/B 테스트, 메시지 가설, 어떤 소재를 만들거나 확장할지, 성과가 왜 변했는지, 다음 광고 테스트, creative fatigue. 데이터 QA·예산 배분·운영 판정이 주 산출물이면 audit-marketing-report.
---

# Plan Marketing Experiment

Turn a performance observation into a falsifiable learning plan instead of
declaring a winner from a label, CTR, or short period.

## Prepare

1. Read `.harness/MARKETING.md` when present. Read `.harness/DESIGN.md` only
   when landing, UI, visual system, or component choice is an experiment axis.
2. Read
   [performance-decisions.md](../korea-marketing/references/performance-decisions.md)
   and the campaign section of
   [integrated-playbook.md](../korea-marketing/references/integrated-playbook.md).
3. Collect the objective, audience situation, message, proof or offer, format,
   channel, landing, spend, conversions, recent and cumulative results, and
   downstream quality.

## Execute

1. Separate observed data, interpretation, alternative explanations, and unknowns.
2. Rewrite the learning unit as:

   `customer situation × message hypothesis × proof/offer × format × channel × landing × downstream quality`

3. Compare like with like. Separate objective, period, placement, format, new
   version versus accumulated creative, and efficiency versus volume.
4. Identify whether the likely bottleneck is attention, traffic quality, landing,
   offer, conversion friction, attribution, or downstream customer quality.
5. Change one causal axis per primary test. If operational reality requires
   multiple changes, label the result non-identifiable.
6. Define control, treatment, eligible audience, duration, minimum evidence,
   primary metric, guardrails, and scale or stop rule before launch.
7. Include production, approval, legal copy, usage rights, and landing or CRM
   dependencies.
8. For creator-led assets, preserve the creator's native tone and production
   style. Fix only the required claim, offer, rights, timing, and measurement
   constraints unless the hypothesis explicitly tests style.

## Deliver

Use [experiment-cards.md](references/experiment-cards.md). Return one learning
card and one to three prioritized test cards. Recommend the first test and say
what decision its result will unlock.

Store a result as a hypothesis until repeated, experimentally supported, or
accepted by the user. Archive project-specific learning in
`.harness/MARKETING.md`; archive reusable UI patterns in `.harness/DESIGN.md`.

## Quality gate

- High CTR alone is not a winning creative.
- A small efficient sample is not evidence of scale.
- A simple before-and-after comparison is not stated as causality.
- The test isolates a useful decision and has a predeclared failure condition.
- Compliance, approval, and asset rights are part of the test plan.
