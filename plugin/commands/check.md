---
description: 하네스 전체 검증을 한 번에 실행한다 (테스트, 라우팅 평가, 점검, 매니페스트)
allowed-tools: Bash(./harness:*), Bash(python3:*), Bash(claude plugin:*), Read
---

아래를 순서대로 실행하고, **실패가 있을 때만** 원인을 설명해라.

```
python3 -m unittest discover -s tests
python3 plugin/scripts/eval_routing.py
./harness status
claude plugin validate plugin/.claude-plugin/plugin.json --strict
claude plugin validate . --strict
```

- 전부 통과하면 한 줄로 통과 사실과 라우팅 점수만 보고한다.
- 라우팅 평가가 만점 미달이면 실패 시나리오의 `expect`와 실제 `selected`를 비교해
  누락인지 오탐인지 먼저 구분한다. 규칙을 바로 고치지 말고, 같은 실패 유형이
  세 번 이상 반복되는지 확인한 뒤 시나리오를 추가하고 최소 범위로 수정한다.
- 제한 데이터가 플러그인 캐시로 복사됐다는 오류가 나오면 그 경로를 지우고
  원인(플러그인 소스에 프로젝트 상태가 섞였는지)을 먼저 확인한다.

하네스 실행 경로는 아래 순서로 찾는다.

1. 현재 디렉터리에 `./harness` 가 있으면 그것을 쓴다.
2. 없으면 `python3 "$CLAUDE_PLUGIN_ROOT/scripts/harness.py"` 를 쓴다.
3. 둘 다 없으면 `claude plugin list` 로 설치 경로를 확인해 알려주고 멈춘다.
