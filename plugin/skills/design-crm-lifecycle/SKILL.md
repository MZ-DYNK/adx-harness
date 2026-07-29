---
name: design-crm-lifecycle
description: 활성화·리텐션·재구매·윈백을 위한 CRM 라이프사이클 상태, 세그먼트, 메시지 프로그램을 설계하고 진단합니다. CRM 시나리오, 온보딩, 가입 후 전환, 리텐션 저하, 카카오·LMS·푸시·인앱 메시지, suppression, 빈도 상한, 휴면 고객, 윈백, lifecycle, retention, holdout.
---

# Design CRM Lifecycle

Design CRM from identifiable customer state and consent through incremental
business value.

## Prepare

1. Read `.harness/MARKETING.md` when present.
2. Read
   [crm-and-measurement.md](../korea-marketing/references/crm-and-measurement.md).
3. Confirm the lifecycle event, eligible identity, consent state and evidence
   (`source / purpose / channel / timestamp / withdrawal`), target behavior,
   time window, channel, exclusions, incentive cost, and available baseline.
4. Verify current Korean consent and messaging requirements from primary sources
   when the recommendation depends on them. Do not present this as legal advice.

## Execute

1. Define lifecycle states using observable events, not vague personas.
2. Confirm that IDs and cohorts can connect stages. Do not divide independent
   event totals into a sequential funnel.
3. Prioritize the bottleneck segment by reachable volume, expected value, urgency,
   and risk.
4. Specify every program with:
   `Trigger / Audience / Suppression / Promise / Action / Channel / Timing /
   Frequency / Exit / Measure`.
5. Check collisions across campaigns and channels, duplicate rewards,
   re-enrollment, customer support, and operational ownership.
6. Define a holdout or credible comparison, downstream KPI, incentive cost,
   and guardrails for fatigue, complaints, churn, and margin.
7. Connect acquisition and CRM through a shared outcome and feedback SLA.

## Deliver

Use [lifecycle-matrix.md](references/lifecycle-matrix.md). Show the lifecycle
map, prioritized scenario matrix, event and data requirements, measurement
design, and operating QA. Recommend a smallest viable first program.
When consent, eligibility, or suppression is unresolved, lead with
`Design-only / Launch blocked` and list exactly what must be verified before send.

Update `.harness/MARKETING.md` only with accepted lifecycle definitions,
measurement contracts, or validated learning.

## Quality gate

- Do not finalize a send without consent and eligibility.
- Do not omit suppression, frequency, or exit logic.
- Channel clicks are not the final KPI when activation, purchase, appointment,
  operation, or repeat purchase is available.
- Incrementality accounts for natural conversion and incentive cost.
- Each program has an owner and a failure or rollback condition.
