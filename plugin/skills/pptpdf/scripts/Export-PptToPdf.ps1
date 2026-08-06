<#
.SYNOPSIS
    ppt/pptx를 PowerPoint 자체 엔진(COM 자동화)으로 PDF로 내보낸다.
    "다른 이름으로 저장 > PDF"와 동일한 결과물(고화질/Print 품질, 폰트 임베딩)을 생성한다.

.PARAMETER Path
    변환할 .ppt/.pptx 파일 경로, 또는 폴더 경로(폴더면 안의 ppt/pptx를 모두 변환).

.PARAMETER OutDir
    결과 PDF를 저장할 폴더. 지정하지 않으면 원본 파일과 같은 폴더에 저장한다.

.PARAMETER Recurse
    Path가 폴더일 때 하위 폴더까지 재귀적으로 찾는다.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Path,

    [string]$OutDir,

    [switch]$Recurse
)

$ErrorActionPreference = 'Stop'

function Get-TargetFiles {
    param([string]$InputPath, [bool]$DoRecurse)

    if (Test-Path -LiteralPath $InputPath -PathType Leaf) {
        return @(Get-Item -LiteralPath $InputPath)
    }

    if (Test-Path -LiteralPath $InputPath -PathType Container) {
        # -Include는 -Recurse가 없으면 -Path에 와일드카드가 있어야 동작한다.
        $gciParams = @{
            Path    = if ($DoRecurse) { $InputPath } else { Join-Path $InputPath '*' }
            Include = @('*.ppt', '*.pptx', '*.pptm')
            File    = $true
        }
        if ($DoRecurse) { $gciParams.Recurse = $true }
        return @(Get-ChildItem @gciParams | Where-Object { $_.Name -notlike '~$*' })
    }

    throw "경로를 찾을 수 없습니다: $InputPath"
}

function Get-PptxFontAudit {
    param([string]$PptxPath)

    $referenced = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    $embedded = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)

    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue
        $zip = [System.IO.Compression.ZipFile]::OpenRead($PptxPath)
        try {
            foreach ($entry in $zip.Entries) {
                $isSlideLike = $entry.FullName -match '^ppt/(slides|slideLayouts|slideMasters)/.*\.xml$'
                $isTheme = $entry.FullName -match '^ppt/theme/.*\.xml$'
                $isPresentationXml = $entry.FullName -eq 'ppt/presentation.xml'
                if (-not ($isSlideLike -or $isTheme -or $isPresentationXml)) { continue }

                $stream = $entry.Open()
                $reader = New-Object System.IO.StreamReader($stream)
                $xml = $reader.ReadToEnd()
                $reader.Close()
                $stream.Close()

                if ($isSlideLike) {
                    # 실제 텍스트 서식에 지정된 라틴/한중일/기타 폰트만 본다.
                    # (a:font script="..")로 표기되는 테마의 다국어 대체 폰트 표까지 잡으면
                    # 실제로는 안 쓰이는 폰트가 대량으로 "위험 폰트"에 끼어드는 오탐이 생긴다.
                    foreach ($m in [regex]::Matches($xml, '<a:(?:latin|ea|cs)\s+typeface="([^"]+)"')) {
                        $name = $m.Groups[1].Value
                        if ($name -and $name -notlike '+*') { [void]$referenced.Add($name) }
                    }
                } elseif ($isTheme) {
                    # 테마에서는 majorFont/minorFont의 latin(기본 서체)만 실제 사용 폰트로 취급한다.
                    foreach ($blockMatch in [regex]::Matches($xml, '<a:(?:major|minor)Font>(.*?)</a:(?:major|minor)Font>', 'Singleline')) {
                        $latin = [regex]::Match($blockMatch.Groups[1].Value, '<a:latin\s+typeface="([^"]+)"')
                        if ($latin.Success -and $latin.Groups[1].Value -and $latin.Groups[1].Value -notlike '+*') {
                            [void]$referenced.Add($latin.Groups[1].Value)
                        }
                    }
                } elseif ($isPresentationXml) {
                    $embedLst = [regex]::Match($xml, '<p:embeddedFontLst>(.*?)</p:embeddedFontLst>', 'Singleline')
                    if ($embedLst.Success) {
                        foreach ($m in [regex]::Matches($embedLst.Groups[1].Value, 'typeface="([^"]+)"')) {
                            [void]$embedded.Add($m.Groups[1].Value)
                        }
                    }
                }
            }
        } finally {
            $zip.Dispose()
        }
    } catch {
        # 손상되었거나 zip으로 열 수 없는 파일(레거시 .ppt 등)은 오디트를 건너뛴다.
        return $null
    }

    Add-Type -AssemblyName System.Drawing -ErrorAction SilentlyContinue
    $installedFonts = (New-Object System.Drawing.Text.InstalledFontCollection).Families.Name
    $installed = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    foreach ($f in $installedFonts) { [void]$installed.Add($f) }

    $risky = @($referenced | Where-Object { -not $embedded.Contains($_) -and -not $installed.Contains($_) })

    [PSCustomObject]@{
        Referenced = @($referenced)
        Embedded   = @($embedded)
        Risky      = $risky
    }
}

function Invoke-RasterFallback {
    param($SourcePres, $App, [string]$TargetPath)

    # ExportAsFixedFormat과 SaveAs 둘 다 "패키지 전체를 다시 쓰는" 단계에서 실패하는 파일이 실제로 있다
    # (예: 특이한 이미지 포맷 하나가 내부 저장 파이프라인을 막는 경우). 반면 슬라이드 단위 렌더링(Export)은
    # 대부분 살아있으므로, 각 슬라이드를 고해상도 PNG로 뽑아 새 프레젠테이션에 이미지로 붙이고 그 새
    # 프레젠테이션을 PDF로 저장하는 방식으로 우회한다. 텍스트가 이미지로 바뀌어 선택/검색은 안 되지만,
    # 화면에 보이는 모양은 원본과 동일하게 보존된다. 아예 실패하는 것보다는 이게 훨씬 낫다.
    $slideWidth = $SourcePres.PageSetup.SlideWidth
    $slideHeight = $SourcePres.PageSetup.SlideHeight
    $count = $SourcePres.Slides.Count
    $dpi = 200
    $pxWidth = [int]([Math]::Round($slideWidth / 72 * $dpi))
    $pxHeight = [int]([Math]::Round($slideHeight / 72 * $dpi))

    $pngDir = Join-Path ([System.IO.Path]::GetTempPath()) ('pptpdf_raster_' + [System.Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $pngDir | Out-Null

    try {
        $pngPaths = New-Object System.Collections.Generic.List[string]
        for ($i = 1; $i -le $count; $i++) {
            $pngPath = Join-Path $pngDir ("slide{0:D4}.png" -f $i)
            $SourcePres.Slides.Item($i).Export($pngPath, "PNG", $pxWidth, $pxHeight)
            $pngPaths.Add($pngPath)
        }

        $newPres = $App.Presentations.Add(1)
        try {
            $newPres.PageSetup.SlideWidth = $slideWidth
            $newPres.PageSetup.SlideHeight = $slideHeight
            for ($i = 0; $i -lt $pngPaths.Count; $i++) {
                $slide = $newPres.Slides.Add($i + 1, 12)  # ppLayoutBlank
                [void]$slide.Shapes.AddPicture($pngPaths[$i], 0, -1, 0, 0, $slideWidth, $slideHeight)
            }
            $newPres.SaveAs($TargetPath, 32)  # ppSaveAsPDF
        } finally {
            try { $newPres.Close() } catch {}
            [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($newPres)
        }
    } finally {
        Remove-Item -Recurse -Force $pngDir -ErrorAction SilentlyContinue
    }
}

function Invoke-SinglePptToPdf {
    param([string]$SourcePath, [string]$TargetPath)

    # PowerPoint는 Application.Visible을 강제로 끌 수 없는 버전이 있다.
    # 대신 Presentations.Open의 WithWindow:=msoFalse(0)로 창 표시를 최소화한다.
    $app = New-Object -ComObject PowerPoint.Application
    try {
        try { $app.DisplayAlerts = 1 } catch {}          # ppAlertsNone
        try { $app.AutomationSecurity = 3 } catch {}      # msoAutomationSecurityForceDisable (매크로 경고 억제)

        $pres = $app.Presentations.Open($SourcePath, -1, 0, 0)  # ReadOnly, !Untitled, !WithWindow
        $method = 'vector'
        try {
            try {
                # FixedFormatType=PDF(2), Intent=Print(2, 고화질 - PowerPoint "Save As PDF"의 Standard 품질과 동일)
                # BitmapMissingFonts=msoTrue(-1): 임베딩 불가 폰트는 비트맵으로 떠서 화면과 다르게 보이는 것을 방지
                # DocStructureTags=msoTrue(-1): 텍스트 선택/검색 가능하도록 접근성 태그 유지
                $pres.ExportAsFixedFormat($TargetPath, 2, 2, 0, 1, 1, 0, $null, 1, "", -1, -1, -1, -1, 0, $null)
            } catch {
                try {
                    # 일부 Office 빌드는 COM 자동화로 ExportAsFixedFormat을 호출하면
                    # 인자 개수와 무관하게 NullReferenceException을 던진다(수동 UI 실행은 정상).
                    # 이 경우 "다른 이름으로 저장 > PDF"와 완전히 동일한 SaveAs 경로로 대체한다.
                    $pres.SaveAs($TargetPath, 32)  # ppSaveAsPDF
                } catch {
                    # 둘 다 실패하면 해당 파일 자체의 패키지에 문제가 있는 것이다(실제 사례로 확인됨:
                    # 흔치 않은 이미지 포맷 하나가 전체 저장을 막았음). 슬라이드 래스터화로 우회한다.
                    $method = 'raster'
                    Invoke-RasterFallback -SourcePres $pres -App $app -TargetPath $TargetPath
                }
            }
        } finally {
            try { $pres.Close() } catch {}
            [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($pres)
        }
        return $method
    } finally {
        $app.Quit()
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app)
    }
}

function Clear-OrphanPowerPoint {
    param([int[]]$PidsBefore)

    # Quit()이 실제로 프로세스를 내리기까지 약간의 지연이 있다.
    # 너무 빨리 검사하면 정상 종료 중인 프로세스를 "고아"로 오판해 불필요하게 강제 종료하게 된다.
    $deadline = (Get-Date).AddSeconds(6)
    $orphans = @()
    do {
        Start-Sleep -Milliseconds 500
        [GC]::Collect()
        [GC]::WaitForPendingFinalizers()
        $after = @(Get-Process POWERPNT -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
        $orphans = @($after | Where-Object { $PidsBefore -notcontains $_ })
    } while ($orphans.Count -gt 0 -and (Get-Date) -lt $deadline)

    foreach ($orphanPid in $orphans) {
        Write-Warning "종료되지 않은 PowerPoint 프로세스(PID $orphanPid)를 강제 종료합니다."
        Stop-Process -Id $orphanPid -Force -ErrorAction SilentlyContinue
    }
}

# ---- 메인 ----

$files = Get-TargetFiles -InputPath $Path -DoRecurse:$Recurse.IsPresent
if (-not $files -or $files.Count -eq 0) {
    Write-Output "변환할 ppt/pptx 파일을 찾지 못했습니다: $Path"
    return
}

if ($OutDir) {
    New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
}

$results = @()

foreach ($file in $files) {
    $targetDir = if ($OutDir) { $OutDir } else { $file.DirectoryName }
    $targetPath = Join-Path $targetDir ([System.IO.Path]::GetFileNameWithoutExtension($file.Name) + '.pdf')

    $audit = $null
    if ($file.Extension -ieq '.pptx' -or $file.Extension -ieq '.pptm') {
        $audit = Get-PptxFontAudit -PptxPath $file.FullName
    }

    $pidsBefore = @(Get-Process POWERPNT -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)

    $status = 'Success'
    $errorMessage = $null
    $method = 'vector'
    try {
        $method = Invoke-SinglePptToPdf -SourcePath $file.FullName -TargetPath $targetPath
    } catch {
        $status = 'Failed'
        $errorMessage = $_.Exception.Message
    }

    Clear-OrphanPowerPoint -PidsBefore $pidsBefore

    if ($status -eq 'Success' -and -not (Test-Path -LiteralPath $targetPath)) {
        $status = 'Failed'
        $errorMessage = 'PDF 파일이 생성되지 않았습니다.'
    }

    $results += [PSCustomObject]@{
        Source = $file.FullName
        Target = $targetPath
        Status = $status
        Error  = $errorMessage
        Method = $method   # vector: 텍스트/폰트가 살아있는 정상 PDF. raster: 우회 생성(이미지화, 검색/선택 불가)
        Risky  = if ($audit) { $audit.Risky } else { @() }
    }
}

$results | ConvertTo-Json -Depth 4
