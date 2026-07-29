---
name: reconcile-marketing-decision
description: 광고주·인하우스·대행사·운영자의 발언을 추적 가능한 결정, 승인, 담당, 후속으로 정리합니다. Slack·메일·회의록, 액션 아이템, 광고주 피드백, 인수인계, 의견 충돌, 승인 사항, 결정 로그, 누가 언제까지 무엇을, decision log, owner, approval. 책임 정리가 필요 없는 단순 요약에는 쓰지 않습니다.
---

# Reconcile Marketing Decision

Convert fragmented communication into an accountable decision without turning
another person's statement into the user's belief.

## Prepare

1. Read `.harness/NOW.md` and the relevant canonical project file.
2. Follow `.harness/imports/INDEX.md` only to the minimum relevant summary or
   source. Never bulk-load mail, chat, or attachments.
3. Capture source, date, speaker, role, request or constraint, related KPI,
   decision status, and deadline.
4. If the project, channel or thread, or time range is absent, state those as
   source-discovery inputs. Do not use a broad communication summary as evidence
   for a specific decision.

## Execute

1. Classify each item as fact, request, proposal, feedback, decision, action, or
   unresolved question.
2. Preserve the speaker and perspective:
   advertiser, in-house, agency strategy, agency operation, customer, or other.
3. Identify conflicts in success definition, metric source, cost basis, timing,
   approval, capacity, compliance, or ownership.
4. Resolve only what the evidence supports. Mark `미합의`, `미확인`, and
   `승인 대기` explicitly.
5. Close each accepted decision with rationale, owner, approver, execution time,
   next check, and rollback or escalation condition.
6. If no owner exists, keep the action open. You may propose a role-based owner,
   approver, and escalation path, but label the assignment `제안` until accepted.
7. Hand only accepted, durable knowledge to the project knowledge layer.

## Deliver

Use [decision-record.md](references/decision-record.md). Lead with the resolved
decision or blocker, then show perspective evidence and missing information.

Do not infer intent or personal traits from a one-to-one message. Do not label
something agreed without explicit evidence. An action without an owner and
follow-up time remains open.

## Quality gate

- Every material statement retains a speaker and source.
- Fact, interpretation, request, and decision remain distinct.
- Conflicting KPI definitions are surfaced before execution.
- Every closed action has owner, approver when needed, due time, and next check.
- Private conversation detail is minimized and secrets or personal identifiers
  are never promoted.
