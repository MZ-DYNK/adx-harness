# ADX Harness

Claude Code를 개발 도구에 한정하지 않고 기획·마케팅·문서·프론트 디자인까지
같은 기억과 판단 기준으로 함께 일하게 만드는 개인용 하네스입니다.

핵심은 `.md`를 무작정 누적하는 것이 아닙니다. 사람이 검토하고 수정할 수 있는
Markdown을 정본으로 두고, 매 턴 질문에 맞는 지식과 실행 스킬만 자동으로
찾아주는 파생 인덱스를 결합합니다.

## 지금 포함된 것

- 한국 시장의 전략·브랜드·광고·디지털·CRM을 연결하는 마케팅 스킬
- 리포트 감사, 마케팅 실험, CRM 라이프사이클, 이해관계자 의사결정을 위한
  네 개의 실행형 방법론 스킬
- 사용자의 혼합형 실무 수준에 맞춘 한국어 설명과 Markdown 규칙
- 디자인 방향과 컴포넌트 아이디어를 누적하는 프론트 아이데이션 스킬
- 프로젝트별 정본, 상세 위키 페이지, 일일 턴 기록, 제한 원본을 분리한 지식 구조
- Markdown 전체를 검색하되 언제든 다시 만들 수 있는 로컬 SQLite FTS 인덱스
- 사용자 발화의 `행동 + 대상`을 함께 확인하는 precision-first 스킬 라우터
- 로컬 중복을 먼저 확인하고 외부 스킬의 출처·권한·스크립트를 검토하는
  `find-skills`
- 반복 조사와 대량 분류를 맡는 읽기 전용 리서치 서브에이전트

ECC의 대규모 카탈로그를 복제하지 않습니다. 항상 켜지는 플러그인 하나와
작은 표준 라이브러리 런타임을 두고, 필요한 스킬과 지식만 조건부로 불러옵니다.

## 설치

### 팀에 배포할 때 (권장)

Claude Team·Enterprise 플랜은 조직 설정에서 플러그인을 배포합니다. 도메인,
npm, 공개 저장소가 모두 필요하지 않고 이 저장소 구조가 그대로 맞습니다.

- 마켓플레이스 매니페스트: `.claude-plugin/marketplace.json`
- 플러그인 소스: `"./plugin"` 상대 경로
- 조직 sync가 배포 시 각 플러그인을 패키징하므로 팀원은 저장소 접근 권한이
  필요 없습니다

관리자 절차는 [Organization settings > Plugins](https://claude.ai/admin-settings/plugins)
에서 두 가지 중 하나입니다.

1. **ZIP 업로드** — 즉시 배포. 플러그인당 50 MB, 마켓플레이스당 100개까지
2. **GitHub 동기화** — private 또는 internal 저장소에 Claude GitHub App을 설치하고
   `owner/repo` 를 입력. push하면 자동 반영되고 500개까지 지원

전제 조건은 세 가지입니다. 조직 Owner 또는 Primary Owner 권한, Cowork와 Skills
활성화, 그리고 **저장소가 private 또는 internal** 이어야 합니다. 공개 저장소는
지원되지 않습니다.

배포 후 플러그인별로 `기본 설치 / 설치 가능 / 숨김 / 필수` 를 지정할 수 있고,
팀원의 다음 세션에 반영됩니다.

ZIP은 아래처럼 만듭니다.

```bash
cd plugin && zip -rq ../adx-harness.zip . -x "*__pycache__*" && cd ..
```

### 팀에서 쓸 때 필요한 것

**1. 관리자 조건**

- 조직 **Owner 또는 Primary Owner** 권한 (Admin은 플러그인 관리 불가)
- **Cowork와 Skills 활성화** — 마켓플레이스의 선행 조건
- GitHub 동기화를 쓸 경우 저장소가 **private 또는 internal**

**2. 배포 설정은 `설치 가능`으로**

상시 비용이 세션당 약 2,100 토큰입니다. 마케팅·기획 업무를 하지 않는 멤버에게는
값을 못 하므로 `기본 설치`나 `필수`가 아니라 **자기 선택으로 설치**하게 둡니다.

**3. 팀원은 설치 후 할 일이 없습니다**

프로필과 디자인 취향은 `~/.claude/personal-harness-data/` 아래 **사람마다 따로**
생성됩니다. 템플릿에는 역할·업무 범위가 `미확인`으로 비어 있고, 각자의 실제 작업에서
채워집니다. 다른 사람의 프로필이 섞이지 않습니다.

**4. 무엇을 공유하고 무엇을 개인으로 둘지 합의**

같은 저장소에서 일한다면 `.harness/` 안에서 공유 대상과 개인 대상이 갈립니다.

| 파일 | 성격 | Git |
|---|---|---|
| `PROJECT.md` `WIKI.md` `DESIGN.md` `MARKETING.md` `wiki/` | 팀 공유 정본 | 커밋 |
| `NOW.md` | 개인의 현재 작업 상태 | 제외 |
| `logs/` | 개인의 턴 기록과 하루 정리 | 제외 |
| `imports/` | 제한 원본과 조사 요약 | 제외 |

기본값이 이미 이렇게 설정돼 있습니다. 팀에서 현재 상태까지 공유하려면 `NOW.md`를
`.gitignore`에서 빼면 되지만, 서로의 작업 중 상태가 충돌하므로 권장하지 않습니다.

**5. imports 규칙을 팀 규칙으로 올리기**

`imports/`는 사람마다 로컬에만 존재하고 소유자 전용 권한으로 유지됩니다. 클라이언트
원본을 넣는 멤버가 생기면 보존 정책(`RETENTION.md`)을 각자 만들어야 합니다.
새 원본은 이메일·전화·주민번호·카드번호 패턴을 먼저 검사해 계층을 정합니다.

**6. 스킬이 팀 업무에 맞는지 확인**

한국 마케팅·CRM·리포트 감사 방법론이 중심입니다. 개발 전용 팀이라면 스킬을 덜어낸
변형을 따로 만드는 편이 낫습니다.

### 내 기기에 직접 설치할 때

```bash
claude plugin marketplace add ./
```

```bash
claude plugin install adx-harness@adx
```

이후에는 아무 명령도 필요하지 않습니다. 훅이 세션 시작, 질문, 도구 사용, 턴
종료, 세션 종료에 붙어 기억과 라우팅과 정리를 알아서 처리합니다.

상태를 보고 싶을 때만 아래를 씁니다.

```bash
./harness status
```

Claude Code 안에서는 `status`, `summary`, `check` 명령으로 같은 일을 할 수
있습니다. 다른 플러그인과 이름이 겹치면 `/adx-harness:status`처럼
접두사를 붙입니다. 세 명령은 저장소 밖 프로젝트에서도 동작합니다.

### 하네스를 직접 고치며 쓸 때

설치는 플러그인 소스를 캐시로 **복사**합니다. 그래서 `plugin/` 을 고치면 설치본이
오래됩니다. 외울 필요는 없습니다 — `./harness status` 가 소스와 설치본의 수정
시각을 비교해 `소스보다 오래됨` 을 표시하고, 설치 경로가 사라졌으면 문제로
올립니다. 그때만 아래 두 줄을 실행하면 됩니다.

```bash
claude plugin marketplace update adx
```

```bash
claude plugin install adx-harness@adx
```

### 플러그인 경계

플러그인을 설치하면 **소스 디렉터리가 그대로 복사됩니다. 제외 규칙은 없습니다.**
그래서 배포되는 것은 `plugin/` 아래에만 두고, 이 저장소의 프로젝트 상태
(`.harness/`), 제한 원본, 평가 세트, 테스트는 `plugin/` 밖에 둡니다.
`tests/test_packaging.py`가 이 경계를 검사하고, `./harness status`는 플러그인
캐시에 제한 데이터가 복사됐는지 감시합니다.

## 지식 위키 구조

첫 세션에 프로젝트 루트 아래 `.harness/`가 생성됩니다.

```text
.harness/
├── PROJECT.md
├── NOW.md
├── WIKI.md
├── DESIGN.md
├── MARKETING.md
├── wiki/
│   ├── decisions/      # 필요할 때만 분리
│   ├── playbooks/
│   └── concepts/
├── logs/YYYY/MM/DD.md          # 턴 기록
├── logs/YYYY/MM/summary-DD.md  # 하루 정리 서머리
├── imports/            # 메일·Slack·첨부와 조사 요약, 로컬 전용
└── .index/
    └── knowledge.sqlite3
```

- `PROJECT.md`: 변하지 않는 프로젝트 배경, 목표, 범위
- `NOW.md`: 다음 턴에 이어갈 현재 목표, 상태, blocker, 다음 행동
- `WIKI.md`: 검증된 지식의 홈이자 상세 페이지의 Map of Content
- `DESIGN.md`: 프로젝트 디자인 방향, 선택 이력, 재사용할 UI 패턴
- `MARKETING.md`: 고객, 포지셔닝, 채널, CRM, 측정 계약과 검증된 학습
- `wiki/`: 독립적으로 반복 참조할 결정·방법론·개념의 상세 페이지
- `logs/`: 자동 생성되는 `질문 → 답변 → 라우팅 → 진행`의 시간순 증거
- `imports/`: 메일·Slack·첨부 원본과 출처별 조사 요약
- `.index/knowledge.sqlite3`: 위 파일을 검색하기 위한 삭제 가능한 파생 인덱스

프로젝트를 넘는 사용자 프로필과 디자인 취향은
`~/.claude/personal-harness-data/global/` 한 곳에만 저장합니다. 플러그인 설치
위치가 바뀌어도 같은 전역 지식을 사용하며 디렉터리는 `0700`, 파일은 `0600`으로
제한합니다.

Markdown이 유일한 정본입니다. SQLite에는 새 지식을 직접 쓰지 않으며, 파일이
바뀌면 자동 재생성합니다. 기본 검색은 정본과 전역 선호만 대상으로 하고,
“어제 작업 이어서”처럼 연속성이 필요한 발화에서만 로그를, Slack·메일·원본·근거를
명시한 발화에서만 제한 조사 요약을 후보에 넣습니다. 프로젝트별 근거 어휘는
`imports/` 하위 폴더 이름에서 자동으로 만들어지므로 코드에 클라이언트명이 없습니다.
첨부 원본 자체는 인덱싱하지 않습니다.

`NOW.md`, `logs/`, `imports/`, `.index/`는 기본적으로 Git에서 제외합니다.
인덱스 디렉터리는 `0700`, DB는 `0600`으로 제한합니다. 공유가 필요한 결론만
정본으로 승격합니다.

### 보존 정책

`imports`는 요약과 원본의 위험·가치가 달라 4계층으로 보존합니다. 계층 표는
`.harness/imports/RETENTION.md` 한 곳에만 두고, 런타임이 재검토 기한을 읽어
`./harness status` 의 `보존` 줄과 `doctor` 오류로 알립니다.

| 계층 | 보존 |
|---|---|
| 조사 요약 | 영구 |
| 집계 리포트 원본 | 프로젝트 종료 + 월간 마감 1회 |
| 첨부 원본 | 프로젝트 종료 + 월간 마감 1회 |
| 개인 단위 데이터 | 집계로 대체하는 즉시 삭제 |

새 원본을 들여올 때는 이메일·전화·주민번호·카드번호 패턴과 개인정보 의심 열
이름을 먼저 검사해 계층을 정합니다. 삭제는 계층 단위가 아니라 파일 단위로
확인한 뒤 수행하고, 해시는 남겨 같은 파일을 다시 받았을 때 대조합니다.

## 턴별 스킬 라우팅

`UserPromptSubmit` 훅은 질문을 보자마자 다음을 수행합니다.

1. 명시적 `$skill-name` 호출을 최우선으로 확인
2. 일반 키워드 하나가 아니라 `행동 + 대상`, 강한 구문, 고유 신호를 조합해 채점
3. 고신뢰 후보를 최대 두 개만 Claude 문맥에 추가
4. 같은 질문으로 관련 정본·로그·조사 요약을 범위 제한 검색
5. Claude가 실제 의도와 맞는 최소 스킬을 선택해 실행

훅은 Skill을 강제로 호출할 수 없으므로 후보는 힌트입니다. 실제 호출 여부와
관련 지식 위치는 당일 로그의 `### 라우팅`에 남아 오탐·누락을 나중에 조정할
수 있습니다. `routing-report`는 프롬프트 본문 없이 추천 스킬과 훅에서 관측된
Skill 호출 이름만 집계합니다.

현재 라우팅하는 스킬은 다음과 같습니다.

- `find-skills`: 로컬 확인, 외부 탐색, 안전 검토, 범위별 설치 제안
- `audit-marketing-report`: 리포트 QA부터 Scale/Hold/Stop 판단까지
- `plan-marketing-experiment`: 소재·메시지 신호를 검증 가능한 실험으로 변환
- `design-crm-lifecycle`: 동의·제외·빈도·증분효과를 포함한 CRM 설계
- `reconcile-marketing-decision`: 광고주·인하우스·대행사 의견을 결정과 책임으로 정리
- `korea-marketing`: 한국 시장 STP, GTM, 포지셔닝, 채널·캠페인 전략
- `frontend-ideation`: 화면·레이아웃·컴포넌트·상태의 디자인 방향
- `adaptive-writing`: 명시적인 문서 작성·교정·요약·번역
- `project-knowledge`: 이전 결정 회수, 위키 승격, 지식 구조 정리

라우터는 다음처럼 단독 점검할 수 있습니다.

```bash
./harness route \
  --query "CPA와 소재 기준으로 데일리 리포트 분석해줘"
```

## 기록과 검색

- `SessionStart`: 사용자 프로필, 현재 상태, 위키의 제한된 문맥만 주입
- `UserPromptSubmit`: 질문 기록, 스킬 추천, 관련 지식 후보 검색
- `PostToolUse`: 파일 변경·명령·검색·서브에이전트 등 주요 활동을 요약하되,
  Read·Glob·Grep은 경로 중심으로, Gmail·Slack 같은 MCP는 도구 이름만 기록
- `Stop`: 질문·최종 답변·라우팅·진행을 당일 로그에 추가하고 인덱스 갱신
- `SessionEnd`: 하루 기록을 `summary-DD.md` 정리 서머리로 자동 생성

정리 서머리는 턴 수와 도구 실행 횟수, 호출한 스킬과 추천된 스킬, 주요 활동,
질문 흐름, 그리고 추천과 실제 호출이 어긋난 턴의 `확인할 것` 목록을 담습니다.
직접 보고 싶을 때는 `./harness digest` 또는 `/summary`를 씁니다.

최근 로그 본문이나 전체 `imports`는 자동 주입하지 않습니다. 하루 로그가
96 KiB를 넘으면 `DD.part-02.md`처럼 나누고, 긴 질문·답변은 companion 파일로
분리합니다. API 키, 토큰, 쿠키, 이메일, 한국 전화번호, 서명 URL의 민감
쿼리는 기록과 인덱싱 전에 마스킹합니다.

```bash
# 인덱스 상태와 범위
./harness index --project .

# 질문과 같은 범위 규칙으로 검색
./harness search --project . \
  --query "지난번에 확정한 KPI"

# 추천 후보와 관측된 Skill 호출 비교
./harness routing-report --project .
```

`find-skills`는 먼저 `./harness skills`로 번들 스킬을
확인합니다. 외부 탐색이 필요하면 비식별 검색어로 `npx skills find`를 사용하되,
정확한 스킬 원문·스크립트·훅·권한·라이선스와 현재 공식 문서 호환성을 검토하고,
사용자가 범위를 승인한 뒤에만 설치합니다. 세부 기준은
[외부 스킬 도입 정책](.harness/wiki/decisions/external-skill-policy.md)에 있습니다.

## 병렬 처리

반복 조사, 대량 분류, 서로 독립적인 비교는 읽기 전용 서브에이전트에 나눠
동시에 돌립니다. 기본 상한은 세 개이고, 각 에이전트에 서로 다른 범위와
`findings / evidence / recommendation / uncertainty` 형식을 줍니다. 최종 종합과
사용자 취향 판단은 메인 스레드에 남깁니다.

실제로 이 방식으로 리포트 감사, 소재 실험 설계, CRM 라이프사이클, 결정 정리를
병렬 집행하고 각각 루브릭으로 채점했습니다. 기준과 누적 점수는
[집행 평가 기준](evals/real-usage/EXECUTION-RUBRIC.md)에 있습니다.

## 검증

```bash
python3 -m unittest discover -s tests -v
python3 plugin/scripts/eval_routing.py
./harness status
claude plugin validate plugin/.claude-plugin/plugin.json --strict
claude plugin validate . --strict
```

`./harness status` 한 줄이 구조 점검, 라우팅 평가, 지식 인덱스, 오늘 기록,
플러그인 설치 상태와 캐시 유출 감시를 함께 보여줍니다.

## 참고한 원칙

- [ECC](https://github.com/affaan-m/ecc): 선택적 스킬 로딩, 훅 기반 지속성,
  bounded context, 검토된 지식 승격
- [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills):
  가정 표면화, 단순성, 국소 변경, 검증 가능한 완료
- [Vercel Skills](https://github.com/vercel-labs/skills): 스킬 검색·설치와
  점진적 공개 방식
- [Claude Code 공식 훅 문서](https://code.claude.com/docs/en/hooks)
- [Claude Code 공식 스킬 문서](https://code.claude.com/docs/en/slash-commands)

Karpathy 저장소는 Markdown 문체 규격 그 자체가 아니라 에이전트 행동 원칙을
제공합니다. 이 하네스는 그 원칙을 문서·마케팅·디자인 업무에도 적용하도록
재서술했습니다.
