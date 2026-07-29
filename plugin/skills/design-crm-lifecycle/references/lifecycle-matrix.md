# CRM 라이프사이클 설계

## 실행 상태

`Ready / Design-only / Launch blocked`

- 발송 전 확인할 동의 증거: 출처 / 목적 / 채널 / 시각 / 철회

## 상태 지도

| 상태 | 진입 이벤트 | 목표 행동 | 이탈·다음 상태 | 기준 기간 |
|---|---|---|---|---|
|  |  |  |  |  |

## 시나리오

| 항목 | 내용 |
|---|---|
| Trigger |  |
| Audience |  |
| Suppression |  |
| Promise |  |
| Action |  |
| Channel |  |
| Timing / Frequency |  |
| Exit / Re-entry |  |
| Measure / Holdout |  |
| Owner / SLA |  |

## 데이터·운영 QA

- 필요한 이벤트와 ID:
- 동의·수신 자격:
- 중복·충돌:
- 리워드·할인 비용:
- Primary KPI:
- Guardrail:
- 실패·Rollback 조건:
- 다음 검증일:

## 발송 차단 조건

아래가 확인되지 않으면 설계까지만 진행하고 `Design-only / Launch blocked`를
명시합니다. 차단 사유, 해소 조건, 확인 주체를 함께 남깁니다.

- 동의 원장: 출처, 목적, 채널, 시각, 철회 경로
- 규제 업종 문안의 승인번호와 유효기간
- 미귀속·잔여 버킷의 크기와 분해 가능성
- 홀드아웃 명단이 콜센터 아웃바운드에서도 제외되는지
- 이벤트 시각과 배치 갱신 시각의 구분 여부
