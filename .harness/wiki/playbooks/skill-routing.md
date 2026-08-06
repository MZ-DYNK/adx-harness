# 턴별 스킬 라우팅

- 상태: 적용 중
- 마지막 갱신: 2026-08-06
- 정본 구현: `config/skill-routing.json`, `scripts/skill_router.py`

## 목적

사용자가 스킬 이름을 기억하거나 매번 고르지 않아도, 발화에 맞는 최소 실행
방법론을 Claude가 발견하도록 합니다. 스킬 후보는 강제 명령이 아니라
정확도 우선 힌트입니다.

## 매 턴 흐름

1. `$skill-name` 또는 `/skill-name` 명시 호출을 우선합니다.
2. 발화를 NFKC 정규화하고 영어는 단어 경계를 지켜 부분문자열 오탐을 막습니다.
3. 각 스킬의 `행동 + 대상`, 강한 구문, 고유 신호, 지정 조합을 채점합니다.
4. 코드·테스트·건축처럼 헷갈리는 맥락은 negative signal로 감점합니다.
5. `0.82` 이상만 고신뢰 후보로 제시하고 기본 최대 두 개로 제한합니다.
6. Claude가 실제 의도를 확인해 가장 작은 스킬 집합을 호출합니다.
7. 추천 후보, 관련 지식, 실제 Skill 호출을 당일 로그에 남겨 조정 근거로 씁니다.

## 현재 역할 분리

| 요청 | 기본 스킬 |
|---|---|
| 스킬 탐색·검토·추가 | `find-skills` |
| 성과 리포트 QA와 예산 판단 | `audit-marketing-report` |
| 소재·메시지·랜딩 실험 | `plan-marketing-experiment` |
| CRM 상태·세그먼트·시나리오 | `design-crm-lifecycle` |
| 광고주·인하우스·대행사 의견 조율 | `reconcile-marketing-decision` |
| STP·GTM·포지셔닝·채널 전략 | `korea-marketing` |
| UI 방향·레이아웃·컴포넌트 | `frontend-ideation` |
| 명시적인 문서 작성·교정 | `adaptive-writing` |
| 이전 결정 회수·위키 관리 | `project-knowledge` |
| ppt/pptx를 PDF로 변환 | `pptpdf` |

## 오탐 방지 원칙

- `report`, `customer`, `retention`, `material`, `component`, `review` 같은
  일반 단어 하나로 도메인을 결정하지 않습니다.
- 다른 스킬이 글을 출력한다는 이유로 `adaptive-writing`을 함께 호출하지 않습니다.
- Stop 훅이 로그를 쓴다는 이유로 `project-knowledge`를 매 턴 호출하지 않습니다.
- UI 테스트, React 단위 테스트, data retention, 고객 API, 건축 소재는
  마케팅·디자인 스킬로 보내지 않습니다.

## 조정 방법

오탐·누락을 발견하면 당일 로그의 `### 라우팅`과 실제 결과를 함께 확인합니다.
`python3 scripts/harness.py routing-report --project .`로 추천 후보와 훅에서
관측된 Skill 호출을 집계합니다. 이 값은 slash 확장처럼 훅에 잡히지 않는 호출이
있을 수 있으므로 정확도 점수가 아니라 조정용 관측 지표입니다.

- `candidate_adoption`: 추천 후보 중 실제로 관측된 비율
- `routable_call_capture`: 번들 스킬 호출 중 추천에도 포함된 비율
- `exact_set_match`: 추천 집합과 관측 집합이 정확히 같은 턴의 비율
- `review_promotion`: 낮은 신뢰의 검토 후보가 실제로 호출된 비율

명시적 `$skill-name` 호출은 자동 라우팅 지표에서 제외하고, 외부 스킬은 별도
집계합니다. 보고서에는 프롬프트·답변·검색어를 넣지 않습니다. 같은 유형의
불일치가 세 번 이상 반복될 때 원문을 사람이 확인하고, 호출 관측치만으로
라우팅 규칙을 자동 수정하지 않습니다.

새 키워드를 계속 추가하기보다 실패 프롬프트를 테스트에 먼저 고정하고,
행동·대상·negative 조합을 최소 범위로 수정합니다.
