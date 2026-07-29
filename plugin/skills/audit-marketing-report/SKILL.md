---
name: audit-marketing-report
description: 유료 매체·커머스·CRM 성과 리포트를 감사해 근거 있는 예산·운영 결정으로 바꿉니다. 데일리·주간·월간 성과 리포트, XLSX·CSV 대시보드, CPA, ROAS, 예산 소진 페이스, 채널·소재 성과, 어트리뷰션 불일치, 1st-party 결과, 증액·유지·재구조화·감액·중단, audit, performance report, budget pacing, attribution. 다음 실험 설계가 주 산출물이면 plan-marketing-experiment.
---

# Audit Marketing Report

Turn a report into a decision without treating unstable or incomparable numbers
as fact.

## Prepare

1. Read `.harness/MARKETING.md` when present.
2. Read
   [performance-decisions.md](../korea-marketing/references/performance-decisions.md).
3. Inspect the original report when available. Record the file, sheet or range,
   actual included period, and verification date.
4. Ask only for a missing input that would materially change the decision.
   Otherwise mark it `확인 필요` and continue with a bounded conclusion.

## Execute

1. Fix the data contract: objective, actual period and `as_of_date`, cost basis,
   conversion definition, source, attribution, freshness, and business KPI.
2. Run QA before ranking performance:
   - empty used ranges, duplicate sheets, stale pivots, formula errors
   - dynamic dates, restatement, zero-cost conversions, unattributed rows
   - mismatched currencies, VAT, fees, markup, new/existing customer definitions
3. Separate scorecards for reach or video, traffic, conversion, and downstream
   value. Never combine them into one efficiency rank.
4. Compare:
   - budget pacing versus calendar progress
   - efficiency and absolute volume
   - recent and cumulative performance
   - platform or MMP events and first-party results
   - acquisition and downstream quality
5. Diagnose the smallest defensible unit: channel, campaign, creative hypothesis,
   offer, landing, cohort, or data issue.
6. Choose one status:
   `Scale / Hold / Test / Restructure / Reduce-Stop / Investigate`.
7. Attach the action, owner, execution time, downside case, and next check date.
8. Match the decision horizon to the reporting cadence:
   - daily: freshness, anomalies, pacing, and safety-line intervention;
   - weekly: comparable operating and budget decisions;
   - monthly: first-party reconciliation, restatement, and structural learning.

Do not calculate a sequential funnel from independent event totals. Do not call
CTR or CPC improvement a sales result when orders or revenue are missing. Treat
a small efficient sample as a test candidate, not a scalable winner.

## Deliver

Use [report-audit-template.md](references/report-audit-template.md). Lead with
the decision, then confidence and evidence. Keep observations, interpretation,
unknowns, and recommendations distinct.

Update `.harness/MARKETING.md` only when a result is validated or a measurement
contract is accepted. Leave date-bound channel and creative numbers in the
local evidence layer.

## Quality gate

- Every decision traces to a source and metric definition.
- Broken comparability changes the status to `Investigate`, not a confident
  budget action.
- The recommendation includes counter-evidence and a next verification point.
- Advertiser, in-house, agency, and customer consequences are visible when
  materially different.
