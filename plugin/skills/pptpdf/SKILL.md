---
name: pptpdf
description: ppt/pptx/pptm 파일을 PowerPoint 자체 렌더링 엔진(COM 자동화)으로 고화질 PDF로 변환합니다. PPT를 PDF로 바꿔달라는 요청, 발표자료·제안서·리포트 파일을 PDF로 내보내거나 뽑아달라는 요청, 폴더 안의 여러 ppt/pptx를 한 번에 PDF로 변환해달라는 요청, 고용량 ppt 변환에 씁니다. 폰트가 임베딩되지 않고 이 PC에도 없어 대체 렌더링될 위험을 사전 점검해 경고하고, 일반 저장/내보내기 경로가 실패하는 파일은 슬라이드를 고해상도로 래스터화해 우회합니다. 이미 만들어진 PDF를 읽거나 요약하거나 텍스트를 추출하는 작업, PDF 파일명·메타데이터만 바꾸는 작업에는 쓰지 않습니다.
---

# ppt/pptx → PDF 고화질 변환

사람이 PowerPoint에서 "다른 이름으로 저장 > PDF"를 눌렀을 때와 같은 결과물을 만든다.
LibreOffice 같은 외부 렌더러는 폰트 메트릭·그림자·그라디언트·SmartArt 렌더링이 PowerPoint와
미묘하게 달라질 수 있어서 이 보증을 못 한다. 그래서 설치된 PowerPoint 자체를 COM으로
조작해 PowerPoint의 렌더링 엔진을 직접 쓴다. Windows에 Microsoft PowerPoint가 설치되어
있어야 한다.

## 사용법

```
powershell.exe -ExecutionPolicy Bypass -File "${CLAUDE_SKILL_DIR}/scripts/Export-PptToPdf.ps1" -Path "<파일 또는 폴더 경로>" [-OutDir "<출력 폴더>"] [-Recurse]
```

- `-Path` (필수): 변환할 `.ppt`/`.pptx`/`.pptm` 파일 하나, 또는 폴더. 폴더면 안의 ppt/pptx를 모두 변환한다(배치 변환).
- `-OutDir` (선택): 결과 PDF를 저장할 폴더. 생략하면 원본과 같은 폴더에 같은 이름으로 저장한다.
  실제 "저장"과 같은 감각을 유지하는 기본값이다.
- `-Recurse` (선택): `-Path`가 폴더일 때 하위 폴더까지 찾는다.

경로는 공백·한글·괄호가 있어도 그대로 전달하면 된다. 스크립트는 각 파일의 처리 결과를 JSON
배열로 표준출력에 낸다.

```json
[
  { "Source": "...", "Target": "...", "Status": "Success", "Error": null, "Method": "vector", "Risky": ["폰트명", ...] }
]
```

## 실행 후 반드시 할 일

1. **Status**: `Failed`인 파일이 있으면 `Error` 메시지를 그대로 전달하고, 나머지 파일은 정상
   처리됐다는 것도 함께 알린다(배치 중 한 파일이 깨져도 나머지는 계속 진행된다).
2. **Method**: `raster`면 원본 저장 단계에 문제가 있어 슬라이드를 고해상도 이미지로 변환해
   PDF를 만든 것이다. 화면 모양은 같지만 텍스트 검색·선택·복사는 안 된다는 것을 알린다.
   `vector`면 텍스트가 살아있는 일반 PDF다.
3. **Risky(폰트 경고)**: 비어 있지 않으면(원소가 하나면 배열이 아니라 문자열 하나로 나올 수
   있다. PowerShell `ConvertTo-Json`이 원소 1개짜리 배열을 풀어버리는 특성 때문이니 둘 다
   "위험 폰트 목록"으로 취급한다) 다음 취지로 경고한다. **Method가 raster인 파일에는 이 경고를
   하지 않는다**: 이미 이미지로 그려졌으므로 폰트 대체가 의미 없다.
   > 이 파일에 쓰인 "○○" 폰트가 PDF에 임베딩돼 있지 않고 이 PC에도 설치돼 있지 않습니다.
   > PowerPoint가 비슷한 폰트로 대체해서 만들었을 수 있어 원본과 모양이 다를 수 있습니다.
   > 정확한 모양이 필요하면 (a) 그 폰트를 설치한 뒤 다시 변환하거나, (b) 원본을 만든 PC에서
   > PowerPoint 옵션 > 저장 > "파일의 글꼴 포함"을 켜고 다시 저장해달라고 요청하세요.
4. **Target**: 완성된 PDF 경로를 알린다.

경고가 있어도 변환은 항상 진행한다(중단하지 않음).

## 내부 동작 (재구현할 필요 없음, 참고용)

- **폰트 오디트**: pptx는 zip이므로 슬라이드/레이아웃/마스터 XML에서 실제 서식에 지정된
  라틴/한중일 폰트(`<a:latin>`, `<a:ea>`, `<a:cs>`)만 골라내고, 테마의 다국어 대체 폰트 표
  (`<a:font script="...">`, 실제로는 거의 안 쓰임)는 제외한다. 포함하면 거의 모든 파일에
  수십 개의 오탐 경고가 뜬다(실측으로 확인). `presentation.xml`의 `embeddedFontLst`로 이미
  임베딩된 폰트를 뺀 뒤, 시스템 설치 폰트와 대조해 둘 다 아닌 것만 경고한다. 레거시 `.ppt`는
  오디트를 건너뛴다.
- **3단계 변환**: 1차 `ExportAsFixedFormat`(Intent=Print, BitmapMissingFonts=True로 고화질·
  폰트 대체 최소화)을 시도하고, 일부 Office 빌드에서 COM 자동화 호출 시
  `NullReferenceException`을 던지는 게 실측으로 확인돼(수동 UI는 정상) 실패하면
  `Presentation.SaveAs(path, PDF)`로 대체한다. 이 둘까지 실패하면(실측 사례: 흔치 않은
  임베딩 이미지 포맷 하나가 패키지 전체 재작성을 막았음) 슬라이드를 200DPI PNG로 렌더링해
  새 프레젠테이션에 붙이고 그걸 PDF로 저장하는 방식(`Invoke-RasterFallback`)으로 우회한다.
  개별 슬라이드 렌더링은 대부분 살아있어서 이 방법은 거의 항상 성공한다.
- **프로세스 정리**: 파일마다 PowerPoint를 새로 열고 끝나면 반드시 종료한다. 종료가 지연되면
  최대 6초까지 기다렸다가 남은 프로세스만 강제 종료한다. 이미 사용자가 열어둔 다른
  PowerPoint 창은 건드리지 않는다. 이게 없으면 배치 변환 중 숨은 프로세스가 쌓여 메모리를
  잠식한다.

## 세 방법 모두 Failed일 때 (드문 경우, 진단 순서)

raster 우회까지 실패했다는 건 개별 슬라이드 렌더링(`Slide.Export`) 자체가 막혔다는 뜻이라
원인이 더 근본적이다.

1. Mark of the Web(`Get-Item -Stream Zone.Identifier`), Mark as Final(`Presentation.Final`),
   편집 제한 비밀번호(`presentation.xml`의 `modifyVerifier`), IRM(`Presentation.Permission.Enabled`)을
   확인한다. 같은 출처(Slack·이메일 등)에서 받은 파일은 전부 Zone.Identifier가 있는 게 흔한
   정상 상황이니 그것만으로는 원인이 아니다. 실패하는 파일에서만 나타나는 차이인지 다른
   정상 파일과 비교해서 확인한다.
2. pptx를 zip으로 열어 `ppt/media/`에 TIFF나 WDP(HD Photo) 같은 비주류 이미지 포맷이 있는지
   확인한다. `ppt/slides/_rels/slideN.xml.rels`에서 참조 슬라이드를 찾고,
   `presentation.xml`의 `<p:sldIdLst>` 순서로 실제 화면상 슬라이드 번호를 계산해 알린다.
3. 원인이 안 잡히면 더 파지 말고 "이 파일만 PowerPoint에서 직접 열어보면 어떤 문제가
   있는지" 확인해달라고 요청한다. 자동화로 복구할 수 없는 손상일 수 있다.

## 주의사항

- 변환 중 PowerPoint 창이 짧게 나타날 수 있다(자동화로 완전히 숨길 수 없는 버전이 있음). 정상이다.
- 매크로 포함 파일(.pptm)은 자동화 중 매크로 보안 경고만 강제로 끄고 여는 것이며 매크로를
  실행하지는 않는다.
- 파일이 다른 프로그램에서 열려 있거나 손상된 경우 해당 파일만 `Failed`로 표시된다.
