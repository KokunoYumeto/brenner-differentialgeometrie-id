[CmdletBinding()]
param(
    [switch]$PrepareOnly
)

$ErrorActionPreference = 'Stop'
$laneRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$buildDir = Join-Path $laneRoot 'build'
$generatedDir = Join-Path $buildDir 'generated'
$workDir = Join-Path $buildDir 'complete-work'
$qaDir = Join-Path $laneRoot 'qa\complete'
$prepareQaDir = Join-Path $qaDir 'preparation'
$outputDir = Join-Path $laneRoot 'output\pdf'
$outputPdf = Join-Path $outputDir 'geometri-diferensial-manifold-mulus-edisi-lengkap-id.pdf'
$driverPath = Join-Path $generatedDir 'complete-reader-driver.tex'
$prefixDriverPath = Join-Path $generatedDir 'through-unit-22-driver.tex'
$prefixPdfPath = Join-Path $outputDir 'geometri-diferensial-manifold-mulus-hingga-unit-22-id.pdf'
$macroPath = Join-Path $buildDir 'complete-exam-macros.id.tex'
$python = (Get-Command python -ErrorAction Stop).Source
$pdfLatex = (Get-Command pdflatex -ErrorAction Stop).Source
$utf8NoBom = [Text.UTF8Encoding]::new($false)

$prefixFrozen = [ordered]@{
    driver = [ordered]@{
        path = 'build/generated/through-unit-22-driver.tex'
        bytes = 17431
        sha256 = '7d04f2c5906c1ddf5e82a0e80dcaafa7a7d62f99f915f3b8643e5be1d8181716'
    }
    pdf = [ordered]@{
        path = 'output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-22-id.pdf'
        bytes = 9046717
        sha256 = '4e6c03dc8388a4c10c464d939d5a416ab035c52e3bd233212c78a40617e02cf7'
    }
    build_receipt = [ordered]@{
        path = 'qa/unit-22/build.json'
        bytes = 233556
        sha256 = '68aacdf979f81c432a62dd9cebf2d4bab8e017cc03cde60d60532aaa99e6312d'
    }
    structural_qa = [ordered]@{
        path = 'qa/unit-22/pdf_structural_qa.json'
        bytes = 478620
        sha256 = 'f5e9ae47e09bd6759b32b5ae14d623f25c0fbb5feb51f1d21d42559291915159'
    }
}

function Get-Identity {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $null
    }
    return [ordered]@{
        bytes = (Get-Item -LiteralPath $Path).Length
        sha256 = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}

function Get-RelativeProjectPath {
    param([Parameter(Mandatory)][string]$Path)
    $candidate = [IO.Path]::GetFullPath($Path)
    $prefix = $laneRoot.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
    if (-not $candidate.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside the project root: $Path"
    }
    return [IO.Path]::GetRelativePath($laneRoot, $candidate).Replace('\', '/')
}

function Resolve-ProjectLeaf {
    param([Parameter(Mandatory)][string]$RelativePath)
    if ([IO.Path]::IsPathRooted($RelativePath)) {
        throw "Project-relative path must not be rooted: $RelativePath"
    }
    $candidate = [IO.Path]::GetFullPath((Join-Path $laneRoot $RelativePath))
    $prefix = $laneRoot.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
    if (-not $candidate.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes the project root: $RelativePath"
    }
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        throw "Required file is missing: $RelativePath"
    }
    return $candidate
}

function Assert-Identity {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][long]$Bytes,
        [Parameter(Mandatory)][string]$Sha256,
        [Parameter(Mandatory)][string]$Label
    )
    $actual = Get-Identity -Path $Path
    if (
        $null -eq $actual -or
        [long]$actual.bytes -ne $Bytes -or
        $actual.sha256 -ne $Sha256.ToLowerInvariant()
    ) {
        throw ($Label + ' identity mismatch: ' + (ConvertTo-Json -InputObject $actual -Compress))
    }
}

function Read-JsonFile {
    param([Parameter(Mandatory)][string]$Path)
    try {
        return Get-Content -LiteralPath $Path -Raw -Encoding utf8 | ConvertFrom-Json
    }
    catch {
        throw "Invalid JSON at ${Path}: $($_.Exception.Message)"
    }
}

function Write-JsonFile {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][object]$Value
    )
    $parent = Split-Path -Parent $Path
    [IO.Directory]::CreateDirectory($parent) | Out-Null
    [IO.File]::WriteAllBytes(
        $Path,
        $utf8NoBom.GetBytes((ConvertTo-Json -InputObject $Value -Depth 16) + "`n")
    )
}

function Test-PassStatus {
    param([Parameter(Mandatory)][object]$Receipt)
    return ($Receipt.status -eq 'pass' -or $Receipt.passed -eq $true)
}

function Get-BoundedTargetHash {
    param([Parameter(Mandatory)][object]$Receipt)
    if ($null -ne $Receipt.target_sha256 -and [string]$Receipt.target_sha256 -ne '') {
        return ([string]$Receipt.target_sha256).ToLowerInvariant()
    }
    if ($null -ne $Receipt.target -and $null -ne $Receipt.target.sha256) {
        return ([string]$Receipt.target.sha256).ToLowerInvariant()
    }
    return $null
}

foreach ($row in $prefixFrozen.Values) {
    $path = Resolve-ProjectLeaf -RelativePath $row.path
    Assert-Identity -Path $path -Bytes $row.bytes -Sha256 $row.sha256 -Label ('Frozen Unit 22 ' + $row.path)
}

[IO.Directory]::CreateDirectory($generatedDir) | Out-Null
[IO.Directory]::CreateDirectory($workDir) | Out-Null
[IO.Directory]::CreateDirectory($qaDir) | Out-Null
[IO.Directory]::CreateDirectory($prepareQaDir) | Out-Null
[IO.Directory]::CreateDirectory($outputDir) | Out-Null

$preflightBlockers = [Collections.Generic.List[string]]::new()
$examGates = [Collections.Generic.List[object]]::new()
foreach ($exam in 1..10) {
    $digits = '{0:d2}' -f $exam
    $sourceRel = "source/exams/exam-$digits/exam${digits}_solutions.id.tex"
    $translationRel = "qa/exams/EXAM${digits}_SOLUTIONS_TRANSLATION_QA.json"
    $boundedRel = "qa/exams/EXAM${digits}_SOLUTIONS_BOUNDED_QA.json"
    $sourcePath = Join-Path $laneRoot $sourceRel
    $translationPath = Join-Path $laneRoot $translationRel
    $boundedPath = Join-Path $laneRoot $boundedRel
    $sourceIdentity = Get-Identity -Path $sourcePath
    $translation = $null
    $bounded = $null
    if ($null -eq $sourceIdentity) {
        $preflightBlockers.Add("missing official Exam $exam solution form: $sourceRel")
    }
    if (-not (Test-Path -LiteralPath $translationPath -PathType Leaf)) {
        $preflightBlockers.Add("missing Exam $exam exact translation receipt: $translationRel")
    }
    else {
        $translation = Read-JsonFile -Path $translationPath
        if (-not (Test-PassStatus -Receipt $translation)) {
            $preflightBlockers.Add("Exam $exam exact translation receipt does not pass")
        }
        elseif ($null -ne $sourceIdentity -and ([string]$translation.target_sha256).ToLowerInvariant() -ne $sourceIdentity.sha256) {
            $preflightBlockers.Add("Exam $exam exact translation receipt is not bound to the live solution form")
        }
    }
    if (-not (Test-Path -LiteralPath $boundedPath -PathType Leaf)) {
        $preflightBlockers.Add("missing Exam $exam bounded QA receipt: $boundedRel")
    }
    else {
        $bounded = Read-JsonFile -Path $boundedPath
        if (-not (Test-PassStatus -Receipt $bounded)) {
            $preflightBlockers.Add("Exam $exam bounded QA receipt does not pass")
        }
        $boundedHash = Get-BoundedTargetHash -Receipt $bounded
        if ($null -ne $boundedHash -and $null -ne $sourceIdentity -and $boundedHash -ne $sourceIdentity.sha256) {
            $preflightBlockers.Add("Exam $exam bounded QA receipt is not bound to the live solution form")
        }
    }
    $examGates.Add([ordered]@{
        exam = $exam
        source = [ordered]@{ path = $sourceRel; identity = $sourceIdentity }
        exact_translation_qa = [ordered]@{ path = $translationRel; status = if ($null -eq $translation) { 'missing' } else { $translation.status } }
        bounded_qa = [ordered]@{ path = $boundedRel; status = if ($null -eq $bounded) { 'missing' } else { $bounded.status } }
    })
}

$preflightReceipt = [ordered]@{
    schema_version = 1
    workflow = 'o011-complete-reader-preflight-v1'
    status = if ($preflightBlockers.Count -eq 0) { 'ready' } else { 'blocked' }
    exact_unit22_public_prefix = $prefixFrozen
    official_exam_solution_gates = @($examGates)
    blockers = @($preflightBlockers)
}
Write-JsonFile -Path (Join-Path $qaDir 'preflight.json') -Value $preflightReceipt
if ($preflightBlockers.Count -ne 0) {
    if ($PrepareOnly) {
        Write-Output (ConvertTo-Json -InputObject $preflightReceipt -Depth 16)
        return
    }
    throw ('Complete-reader preflight blocked: ' + ($preflightBlockers -join '; '))
}

$prepareBindings = [Collections.Generic.List[object]]::new()
function Invoke-PrepareFragment {
    param(
        [Parameter(Mandatory)][string]$InputRel,
        [Parameter(Mandatory)][string]$OutputRel,
        [Parameter(Mandatory)][string]$ReceiptRel
    )
    $inputPath = Resolve-ProjectLeaf -RelativePath $InputRel
    $outputPath = Join-Path $laneRoot $OutputRel
    $receiptPath = Join-Path $laneRoot $ReceiptRel
    $inputIdentity = Get-Identity -Path $inputPath
    $reuse = $false
    if (
        (Test-Path -LiteralPath $outputPath -PathType Leaf) -and
        (Test-Path -LiteralPath $receiptPath -PathType Leaf)
    ) {
        $existingReceipt = Read-JsonFile -Path $receiptPath
        $existingOutputIdentity = Get-Identity -Path $outputPath
        $reuse = (
            $existingReceipt.input -eq $InputRel -and
            $existingReceipt.output -eq $OutputRel -and
            $existingReceipt.input_sha256 -eq $inputIdentity.sha256 -and
            $existingReceipt.output_sha256 -eq $existingOutputIdentity.sha256
        )
    }
    if (-not $reuse) {
        & $python (Join-Path $laneRoot 'scripts\prepare_unit_tex.py') $inputPath $outputPath '--project-root' $laneRoot '--receipt' $receiptPath
        if ($LASTEXITCODE -ne 0) {
            throw "prepare_unit_tex.py failed for $InputRel"
        }
    }
    $receipt = Read-JsonFile -Path $receiptPath
    $outputIdentity = Get-Identity -Path $outputPath
    if (
        $receipt.input -ne $InputRel -or
        $receipt.output -ne $OutputRel -or
        $receipt.input_sha256 -ne $inputIdentity.sha256 -or
        $receipt.output_sha256 -ne $outputIdentity.sha256
    ) {
        throw "Preparation receipt is not bound to live input/output for $InputRel"
    }
    $script:prepareBindings.Add([ordered]@{
        input = [ordered]@{ path = $InputRel; identity = $inputIdentity }
        output = [ordered]@{ path = $OutputRel; identity = $outputIdentity }
        receipt = [ordered]@{ path = $ReceiptRel; identity = (Get-Identity -Path $receiptPath) }
        reused_without_rewrite = $reuse
    })
}

Invoke-PrepareFragment -InputRel 'source/bridges/lie-groups/bridge-lie-theory.id.tex' -OutputRel 'build/generated/bridges/bridge-lie-theory.build.tex' -ReceiptRel 'qa/complete/preparation/bridge-lie-theory_prepare.json'
Invoke-PrepareFragment -InputRel 'source/bridges/lie-groups/bridge-lie-assessment.id.tex' -OutputRel 'build/generated/bridges/bridge-lie-assessment.build.tex' -ReceiptRel 'qa/complete/preparation/bridge-lie-assessment_prepare.json'
Invoke-PrepareFragment -InputRel 'source/bridges/de-rham/bridge-de-rham-theory.id.tex' -OutputRel 'build/generated/bridges/bridge-de-rham-theory.build.tex' -ReceiptRel 'qa/complete/preparation/bridge-de-rham-theory_prepare.json'
Invoke-PrepareFragment -InputRel 'source/bridges/de-rham/bridge-de-rham-assessment.id.tex' -OutputRel 'build/generated/bridges/bridge-de-rham-assessment.build.tex' -ReceiptRel 'qa/complete/preparation/bridge-de-rham-assessment_prepare.json'

foreach ($exam in 1..10) {
    $digits = '{0:d2}' -f $exam
    Invoke-PrepareFragment -InputRel "source/exams/exam-$digits/exam${digits}_learner.id.tex" -OutputRel "build/generated/exams/exam${digits}_learner.id.build.tex" -ReceiptRel "qa/complete/preparation/exam${digits}_learner_prepare.json"
    Invoke-PrepareFragment -InputRel "source/exams/exam-$digits/exam${digits}_solutions.id.tex" -OutputRel "build/generated/exams/exam${digits}_solutions.id.build.tex" -ReceiptRel "qa/complete/preparation/exam${digits}_solutions_prepare.json"
}
Invoke-PrepareFragment -InputRel 'source/exams/original-repairs/missing-exam-solutions.id.tex' -OutputRel 'build/generated/bridges/missing-exam-solutions.build.tex' -ReceiptRel 'qa/complete/preparation/missing-exam-solutions_prepare.json'

$solutionNumbers = [ordered]@{
    '23' = @(6, 13, 16, 17)
    '24' = @()
    '25' = @(1, 7, 8, 11, 12, 14)
    '26' = @(3, 6, 9)
    '27' = @(4, 5, 9, 13)
    '28' = @(2, 5)
    '29' = @(2)
}
$lectureTitles = [ordered]@{
    '23' = 'Teorema Stokes dan Teorema Titik Tetap Brouwer'
    '24' = 'Koneksi dan Turunan Vertikal'
    '25' = 'Penampang Horizontal dan Koneksi Linear'
    '26' = 'Koneksi Levi--Civita'
    '27' = 'Turunan Vertikal, Percepatan Tangensial, dan Geodesik'
    '28' = 'Kelengkungan dan Teorema Frobenius'
    '29' = 'Kelengkungan Riemann dan Kelengkungan Seksional'
}

$extension = [Collections.Generic.List[string]]::new()
$extension.Add('% O011-COMPLETE-EXTENSION-BEGIN')
$extension.Add('\part{Kelanjutan Edisi Lengkap}')
$extension.Add('\chapter*{Catatan provenans bagian tambahan}')
$extension.Add('\addcontentsline{toc}{chapter}{Catatan provenans bagian tambahan}')
$extension.Add('Unit 23--29 melanjutkan sumber Holger Brenner dari Wikiversity berbahasa Jerman. Hanya solusi inti yang benar-benar disediakan oleh sumber yang dimuat pada bagian unit. Jembatan Grup Lie dan de Rham serta enam perbaikan kekosongan ujian merupakan materi asli edisi ini dan tidak dinisbahkan kepada Brenner atau Wikiversity. Formulir solusi resmi mempertahankan kekosongan solusi sumber; perbaikan asli disajikan kemudian sebagai bagian yang terpisah dan berlabel jelas.')
$extension.Add('\newtheorem{Korolari}[fakt]{Korolari}')
$extension.Add('\newtheorem{Akibat}[fakt]{Akibat}')
$extension.Add('')
foreach ($unit in 23..29) {
    $digits = '{0:d2}' -f $unit
    $unitKey = [string]$unit
    $extension.Add('\part{Unit ' + $unit + '}')
    $extension.Add('\chapter[Kuliah ' + $unit + ']{Kuliah ' + $unit + ': ' + $lectureTitles[$unitKey] + '}')
    $extension.Add('\input{generated/lecture' + $digits + '.id.build.tex}')
    $extension.Add('')
    $extension.Add('\chapter{Lembar Kerja ' + $unit + '}')
    $extension.Add('\input{generated/worksheet' + $digits + '.id.build.tex}')
    if (@($solutionNumbers[$unitKey]).Count -gt 0) {
        $extension.Add('')
        $extension.Add('\section*{Solusi yang disediakan oleh sumber}')
        $extension.Add('\addcontentsline{toc}{section}{Solusi yang disediakan oleh sumber}')
        foreach ($exercise in @($solutionNumbers[$unitKey])) {
            $exerciseDigits = '{0:d2}' -f $exercise
            $extension.Add('\subsection*{Solusi Soal ' + $unit + '.' + $exercise + '}')
            $extension.Add('\input{generated/worksheet' + $digits + '_exercise' + $exerciseDigits + '_solution.id.build.tex}')
        }
    }
    $extension.Add('')
}

$extension.Add('\part{Jembatan Asli}')
$extension.Add('\chapter{Jembatan Grup Lie dan Aljabar Lie}')
$extension.Add('\noindent\textit{Materi asli edisi ini; bukan solusi atau teks yang disediakan oleh sumber Brenner/Wikiversity.}')
$extension.Add('\input{generated/bridges/bridge-lie-theory.build.tex}')
$extension.Add('\input{generated/bridges/bridge-lie-assessment.build.tex}')
$extension.Add('')
$extension.Add('\chapter{Jembatan Kohomologi de Rham dan Topologi Diferensial}')
$extension.Add('\noindent\textit{Materi asli edisi ini; bukan solusi atau teks yang disediakan oleh sumber Brenner/Wikiversity.}')
$extension.Add('\input{generated/bridges/bridge-de-rham-theory.build.tex}')
$extension.Add('\input{generated/bridges/bridge-de-rham-assessment.build.tex}')
$extension.Add('')

$extension.Add('\part{Formulir Ujian}')
$extension.Add('\chapter*{Provenans formulir ujian}')
$extension.Add('\addcontentsline{toc}{chapter}{Provenans formulir ujian}')
$extension.Add('Sepuluh formulir peserta berikut mempertahankan teks peserta resmi. Sepuluh formulir solusi resmi sesudahnya hanya memuat solusi yang tersedia pada sumber resmi yang dibekukan. Kekosongan sumber tetap kosong dan tidak diisi pada permukaan resmi ini.')
$extension.Add('\input{complete-exam-macros.id.tex}')
$extension.Add('\providecommand{\theHfakt}{}')
$extension.Add('')
foreach ($exam in 1..10) {
    $digits = '{0:d2}' -f $exam
    $extension.Add('\chapter{Formulir Peserta Ujian ' + $exam + '}')
    $extension.Add('\noindent\textit{Formulir peserta dari sumber resmi; teks soal dipertahankan sesuai terjemahan yang telah diverifikasi.}')
    $extension.Add('\begingroup')
    $extension.Add('\renewcommand{\theHfakt}{o011.exam.learner.' + $digits + '.\arabic{fakt}}')
    $extension.Add('\input{generated/exams/exam' + $digits + '_learner.id.build.tex}')
    $extension.Add('\endgroup')
    $extension.Add('')
}

$extension.Add('\part{Formulir Solusi Resmi}')
$extension.Add('\chapter*{Batas solusi resmi}')
$extension.Add('\addcontentsline{toc}{chapter}{Batas solusi resmi}')
$extension.Add('Setiap formulir pada bagian ini berasal dari permukaan solusi resmi yang dibekukan. Solusi yang tidak tersedia pada sumber tetap tidak tersedia di sini; tidak ada materi asli yang dimasukkan ke dalam formulir resmi.')
foreach ($exam in 1..10) {
    $digits = '{0:d2}' -f $exam
    $extension.Add('\chapter{Formulir Solusi Resmi Ujian ' + $exam + '}')
    $extension.Add('\noindent\textit{Solusi yang disediakan oleh sumber resmi; kekosongan sumber dipertahankan.}')
    $extension.Add('\begingroup')
    $extension.Add('\renewcommand{\theHfakt}{o011.exam.official.' + $digits + '.\arabic{fakt}}')
    $extension.Add('\input{generated/exams/exam' + $digits + '_solutions.id.build.tex}')
    $extension.Add('\endgroup')
    $extension.Add('')
}

$extension.Add('\part{Perbaikan Asli yang Terpisah}')
$extension.Add('\chapter{Enam solusi asli untuk kekosongan sumber}')
$extension.Add('\noindent\textit{Bagian ini berisi tepat enam solusi asli edisi, berlabel terpisah, dan bukan bagian dari sumber Brenner/Wikiversity maupun formulir solusi resmi.}')
$extension.Add('\input{generated/bridges/missing-exam-solutions.build.tex}')
$extension.Add('% O011-COMPLETE-EXTENSION-END')
$extensionText = (($extension -join "`n") + "`n`n")

$prefixBytes = [IO.File]::ReadAllBytes($prefixDriverPath)
$prefixText = $utf8NoBom.GetString($prefixBytes)
$backmatterMarker = '\backmatter'
$markerIndex = $prefixText.IndexOf($backmatterMarker, [StringComparison]::Ordinal)
if ($markerIndex -lt 0 -or $prefixText.IndexOf($backmatterMarker, $markerIndex + 1, [StringComparison]::Ordinal) -ge 0) {
    throw 'Frozen Unit 22 driver must contain exactly one backmatter marker'
}
$prefixHeadText = $prefixText.Substring(0, $markerIndex)
$suffixText = $prefixText.Substring($markerIndex)
$attributionMarker = '\input{generated/unit22-media-attribution-cumulative.tex}'
if (($suffixText.Split($attributionMarker).Count - 1) -ne 1) {
    throw 'Frozen Unit 22 suffix must contain exactly one Unit 22 attribution marker'
}
$additionalAttribution = [Collections.Generic.List[string]]::new()
foreach ($unit in 23..29) {
    $additionalAttribution.Add('\input{generated/unit' + $unit + '-media-attribution-complete.tex}')
}
$suffixText = $suffixText.Replace($attributionMarker, $attributionMarker + "`n" + ($additionalAttribution -join "`n"))
$driverText = $prefixHeadText + $extensionText + $suffixText
[IO.File]::WriteAllBytes($driverPath, $utf8NoBom.GetBytes($driverText))

$prefixHeadBytes = $utf8NoBom.GetBytes($prefixHeadText)
$driverBytes = [IO.File]::ReadAllBytes($driverPath)
if ($driverBytes.Length -lt $prefixHeadBytes.Length) {
    throw 'Derived complete driver is shorter than the frozen Unit 22 prefix head'
}
for ($index = 0; $index -lt $prefixHeadBytes.Length; $index++) {
    if ($driverBytes[$index] -ne $prefixHeadBytes[$index]) {
        throw "Derived complete driver changed the frozen Unit 22 prefix at byte $index"
    }
}
if ($driverText.IndexOf('\usepackage[a4paper,margin=22mm,headheight=15pt]{geometry}', [StringComparison]::Ordinal) -lt 0) {
    throw 'Derived complete driver lost the centered A4/22mm geometry contract'
}

$prefixHeadTemp = Join-Path $workDir 'unit22-prefix-head.bin'
[IO.File]::WriteAllBytes($prefixHeadTemp, $prefixHeadBytes)
$driverReceipt = [ordered]@{
    schema_version = 1
    workflow = 'o011-complete-reader-driver-derivation-v1'
    frozen_input = $prefixFrozen.driver
    preserved_prefix = [ordered]@{
        boundary = 'all frozen driver bytes before the unique backmatter command'
        bytes = $prefixHeadBytes.Length
        sha256 = (Get-FileHash -LiteralPath $prefixHeadTemp -Algorithm SHA256).Hash.ToLowerInvariant()
        byte_identical = $true
    }
    output = [ordered]@{ path = 'build/generated/complete-reader-driver.tex'; identity = (Get-Identity -Path $driverPath) }
    geometry = [ordered]@{ paper = 'A4'; margin = '22mm'; centered = $true; class_option = 'oneside' }
    unit_extension = @(23, 24, 25, 26, 27, 28, 29)
    source_supplied_core_solutions = $solutionNumbers
    ordered_surfaces = @('units-23-through-29', 'original-lie-bridge', 'original-de-rham-bridge', 'ten-learner-exam-forms', 'ten-official-solution-forms', 'six-separately-labelled-original-repairs')
}
Write-JsonFile -Path (Join-Path $qaDir 'driver_derivation.json') -Value $driverReceipt

if ($PrepareOnly) {
    $result = [ordered]@{
        status = 'prepared'
        preflight = 'qa/complete/preflight.json'
        driver = $driverReceipt.output
        preparation_count = $prepareBindings.Count
        final_pdf_built = $false
    }
    Write-Output (ConvertTo-Json -InputObject $result -Depth 8)
    return
}

# The frozen Unit 22 build needed two transient underscore-normalized JPEG
# aliases.  The complete build must not write into authority/, so reproduce the
# compilation tree under build/complete-stage and place the aliases only there.
$stageRoot = Join-Path $buildDir 'complete-stage'
$stageBuildDir = Join-Path $stageRoot 'build'
$stageAuthorityMediaDir = Join-Path $stageRoot 'authority\media'
if (Test-Path -LiteralPath $stageRoot) {
    $resolvedStage = (Resolve-Path -LiteralPath $stageRoot).Path
    $expectedStage = [IO.Path]::GetFullPath($stageRoot)
    $allowedPrefix = [IO.Path]::GetFullPath($buildDir).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
    if ($resolvedStage -ne $expectedStage -or -not $resolvedStage.StartsWith($allowedPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to replace unsafe complete-build staging path: $resolvedStage"
    }
    Remove-Item -LiteralPath $resolvedStage -Recurse -Force
}
[IO.Directory]::CreateDirectory($stageBuildDir) | Out-Null
[IO.Directory]::CreateDirectory($stageAuthorityMediaDir) | Out-Null

# Stage only the generated files that participate in the complete reader.  The
# persistent generated tree also contains historical milestone and bounded-QA
# drivers; copying that whole tree made the clean source-package rebuild depend
# on stale files that were intentionally absent from the release package.
$driverInputs = [regex]::Matches($driverText, '\\input\{([^}]+)\}')
$generatedStageRelativePaths = [Collections.Generic.List[string]]::new()
$generatedStageRelativePaths.Add('generated/complete-reader-driver.tex')
foreach ($match in $driverInputs) {
    $buildRelative = $match.Groups[1].Value.Replace('\', '/')
    if ($buildRelative.StartsWith('generated/', [StringComparison]::OrdinalIgnoreCase)) {
        $generatedStageRelativePaths.Add($buildRelative)
    }
}
$generatedMediaFiles = @(Get-ChildItem -LiteralPath (Join-Path $generatedDir 'media') -File | Sort-Object -Property Name)
foreach ($mediaFile in $generatedMediaFiles) {
    $generatedStageRelativePaths.Add('generated/media/' + $mediaFile.Name)
}
$generatedStageRelativePaths = @($generatedStageRelativePaths | Sort-Object -Unique)
foreach ($stageRelative in $generatedStageRelativePaths) {
    $sourcePath = Resolve-ProjectLeaf -RelativePath ('build/' + $stageRelative)
    $targetPath = Join-Path $stageBuildDir $stageRelative
    [IO.Directory]::CreateDirectory((Split-Path -Parent $targetPath)) | Out-Null
    Copy-Item -LiteralPath $sourcePath -Destination $targetPath
}
Copy-Item -LiteralPath (Join-Path $buildDir 'brenner-compat.tex') -Destination (Join-Path $stageBuildDir 'brenner-compat.tex')
Copy-Item -LiteralPath $macroPath -Destination (Join-Path $stageBuildDir 'complete-exam-macros.id.tex')
$authorityMediaFiles = @(
    Get-ChildItem -LiteralPath (Join-Path $laneRoot 'authority\media') -File |
        Where-Object { $_.Name -notlike '*.download.json' } |
        Sort-Object -Property Name
)
foreach ($mediaFile in $authorityMediaFiles) {
    Copy-Item -LiteralPath $mediaFile.FullName -Destination (Join-Path $stageAuthorityMediaDir $mediaFile.Name)
}

$stageAliases = @(
    [ordered]@{
        source = 'build/complete-stage/authority/media/Torus vectors oblique.jpg'
        target = 'build/complete-stage/authority/media/Torus_vectors_oblique.jpg'
        role = 'task-local Unit 10 underscore-normalized JPEG loader alias'
    },
    [ordered]@{
        source = 'build/complete-stage/authority/media/Georg Friedrich Bernhard Riemann.jpeg'
        target = 'build/complete-stage/authority/media/Georg_Friedrich_Bernhard_Riemann.jpg'
        role = 'task-local Unit 16 underscore-normalized JPEG loader alias'
    }
)
$stageAliasRows = [Collections.Generic.List[object]]::new()
foreach ($alias in $stageAliases) {
    $sourcePath = Resolve-ProjectLeaf -RelativePath $alias.source
    $targetPath = Join-Path $laneRoot $alias.target
    Copy-Item -LiteralPath $sourcePath -Destination $targetPath -Force
    $sourceIdentity = Get-Identity -Path $sourcePath
    $targetIdentity = Get-Identity -Path $targetPath
    if ($sourceIdentity.bytes -ne $targetIdentity.bytes -or $sourceIdentity.sha256 -ne $targetIdentity.sha256) {
        throw "Task-local staging alias identity mismatch: $($alias.target)"
    }
    $stageAliasRows.Add([ordered]@{
        source = [ordered]@{ path = $alias.source; identity = $sourceIdentity }
        target = [ordered]@{ path = $alias.target; identity = $targetIdentity }
        role = $alias.role
    })
}
$stagingReceipt = [ordered]@{
    schema_version = 1
    workflow = 'o011-complete-reader-task-local-staging-v1'
    root = 'build/complete-stage'
    authority_tree_untouched = $true
    generated_tree_source = [ordered]@{ path = 'build/generated'; selected_file_count = $generatedStageRelativePaths.Count; selection = 'complete driver, its generated inputs, and complete generated media only' }
    staged_generated_tree = [ordered]@{ path = 'build/complete-stage/build/generated'; file_count = @(Get-ChildItem -LiteralPath (Join-Path $stageBuildDir 'generated') -Recurse -File).Count }
    staged_authority_media = [ordered]@{ path = 'build/complete-stage/authority/media'; selected_source_file_count = $authorityMediaFiles.Count; excluded_sidecars = '*.download.json'; staged_file_count = @(Get-ChildItem -LiteralPath $stageAuthorityMediaDir -File).Count }
    aliases = @($stageAliasRows)
}
Write-JsonFile -Path (Join-Path $qaDir 'staging.json') -Value $stagingReceipt

$inputPaths = [Collections.Generic.Dictionary[string, object]]::new([StringComparer]::OrdinalIgnoreCase)
function Add-InputIdentity {
    param([Parameter(Mandatory)][string]$RelativePath)
    $normalized = $RelativePath.Replace('\', '/')
    if ($script:inputPaths.ContainsKey($normalized)) {
        return
    }
    $path = Resolve-ProjectLeaf -RelativePath $normalized
    $script:inputPaths.Add($normalized, (Get-Identity -Path $path))
}

foreach ($row in $prefixFrozen.Values) { Add-InputIdentity -RelativePath $row.path }
foreach ($rel in @(
    'scripts/build_complete_reader.ps1',
    'scripts/verify_complete_reader.py',
    'scripts/prepare_unit_tex.py',
    'build/brenner-compat.tex',
    'build/complete-exam-macros.id.tex',
    'build/generated/complete-reader-driver.tex',
    'qa/complete/preflight.json',
    'qa/complete/driver_derivation.json',
    'qa/complete/staging.json'
)) { Add-InputIdentity -RelativePath $rel }

foreach ($binding in $prepareBindings) {
    Add-InputIdentity -RelativePath $binding.input.path
    Add-InputIdentity -RelativePath $binding.output.path
    Add-InputIdentity -RelativePath $binding.receipt.path
}

foreach ($unit in 23..29) {
    $digits = '{0:d2}' -f $unit
    $unitKey = [string]$unit
    foreach ($rel in @(
        "source/units/unit-$digits/lecture${digits}.id.tex",
        "source/units/unit-$digits/worksheet${digits}.id.tex",
        "build/generated/lecture${digits}.id.build.tex",
        "build/generated/worksheet${digits}.id.build.tex",
        "build/generated/unit${digits}-media-attribution-complete.tex",
        "qa/complete/cumulative-media/unit-${digits}_media.json"
    )) { Add-InputIdentity -RelativePath $rel }
    foreach ($exercise in @($solutionNumbers[$unitKey])) {
        $exerciseDigits = '{0:d2}' -f $exercise
        Add-InputIdentity -RelativePath "source/units/unit-$digits/worksheet${digits}_exercise${exerciseDigits}_solution.id.tex"
        Add-InputIdentity -RelativePath "build/generated/worksheet${digits}_exercise${exerciseDigits}_solution.id.build.tex"
    }
}

foreach ($exam in 1..10) {
    $digits = '{0:d2}' -f $exam
    Add-InputIdentity -RelativePath "qa/exams/EXAM${digits}_SOLUTIONS_TRANSLATION_QA.json"
    Add-InputIdentity -RelativePath "qa/exams/EXAM${digits}_SOLUTIONS_BOUNDED_QA.json"
}

foreach ($match in $driverInputs) {
    $buildRelative = $match.Groups[1].Value
    Add-InputIdentity -RelativePath ('build/' + $buildRelative)
}
$mediaFiles = Get-ChildItem -LiteralPath (Join-Path $generatedDir 'media') -File
foreach ($mediaFile in $mediaFiles) {
    Add-InputIdentity -RelativePath (Get-RelativeProjectPath -Path $mediaFile.FullName)
}
$stageFiles = Get-ChildItem -LiteralPath $stageRoot -Recurse -File
foreach ($stageFile in $stageFiles) {
    Add-InputIdentity -RelativePath (Get-RelativeProjectPath -Path $stageFile.FullName)
}

function Assert-InputsUnchanged {
    param([Parameter(Mandatory)][string]$Stage)
    foreach ($entry in $script:inputPaths.GetEnumerator()) {
        $path = Resolve-ProjectLeaf -RelativePath $entry.Key
        $actual = Get-Identity -Path $path
        if ($actual.bytes -ne $entry.Value.bytes -or $actual.sha256 -ne $entry.Value.sha256) {
            throw "Build input changed ${Stage}: $($entry.Key)"
        }
    }
}

$jobArtifacts = @(
    'complete-reader.aux', 'complete-reader.log', 'complete-reader.out',
    'complete-reader.toc', 'complete-reader.lof', 'complete-reader.fls',
    'complete-reader.pdf'
)
function Clear-JobArtifacts {
    foreach ($name in $jobArtifacts) {
        $path = Join-Path $workDir $name
        if (Test-Path -LiteralPath $path -PathType Leaf) {
            Remove-Item -LiteralPath $path -Force
        }
    }
}

foreach ($name in @(
    'cycle-1.pdf', 'cycle-2.pdf',
    'cycle-1-pass-1.console.txt', 'cycle-1-pass-2.console.txt', 'cycle-1-pass-3.console.txt',
    'cycle-2-pass-1.console.txt', 'cycle-2-pass-2.console.txt', 'cycle-2-pass-3.console.txt'
)) {
    $path = Join-Path $workDir $name
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        Remove-Item -LiteralPath $path -Force
    }
}

function Invoke-BuildCycle {
    param([Parameter(Mandatory)][int]$Cycle)
    Assert-InputsUnchanged -Stage "before clean cycle $Cycle"
    foreach ($row in $prefixFrozen.Values) {
        Assert-Identity -Path (Join-Path $laneRoot $row.path) -Bytes $row.bytes -Sha256 $row.sha256 -Label "Frozen Unit 22 prefix before cycle $Cycle"
    }
    Clear-JobArtifacts
    $logs = [Collections.Generic.List[object]]::new()
    Push-Location $stageBuildDir
    try {
        foreach ($pass in 1..3) {
            $consolePath = Join-Path $workDir ("cycle-{0}-pass-{1}.console.txt" -f $Cycle, $pass)
            & $pdfLatex '-interaction=nonstopmode' '-halt-on-error' '-file-line-error' '-recorder' ("-output-directory=$workDir") '-jobname=complete-reader' 'generated/complete-reader-driver.tex' 2>&1 |
                Out-File -LiteralPath $consolePath -Encoding utf8
            if ($LASTEXITCODE -ne 0) {
                throw "pdflatex failed in cycle $Cycle pass $pass; see $consolePath"
            }
            $logs.Add([ordered]@{
                pass = $pass
                path = Get-RelativeProjectPath -Path $consolePath
                exit_code = 0
            })
        }
    }
    finally {
        Pop-Location
    }
    $builtPdf = Join-Path $workDir 'complete-reader.pdf'
    if (-not (Test-Path -LiteralPath $builtPdf -PathType Leaf)) {
        throw "pdflatex did not create $builtPdf"
    }
    Assert-InputsUnchanged -Stage "after clean cycle $Cycle"
    $cyclePdf = Join-Path $workDir ("cycle-{0}.pdf" -f $Cycle)
    Copy-Item -LiteralPath $builtPdf -Destination $cyclePdf -Force
    return [ordered]@{
        cycle = $Cycle
        pdf = Get-RelativeProjectPath -Path $cyclePdf
        identity = Get-Identity -Path $cyclePdf
        logs = @($logs)
    }
}

$priorSourceDateEpoch = $env:SOURCE_DATE_EPOCH
$priorForceSourceDate = $env:FORCE_SOURCE_DATE
$env:SOURCE_DATE_EPOCH = '0'
$env:FORCE_SOURCE_DATE = '1'
try {
    $cycle1 = Invoke-BuildCycle -Cycle 1
    $cycle2 = Invoke-BuildCycle -Cycle 2
}
finally {
    if ($null -eq $priorSourceDateEpoch) { Remove-Item Env:SOURCE_DATE_EPOCH -ErrorAction SilentlyContinue } else { $env:SOURCE_DATE_EPOCH = $priorSourceDateEpoch }
    if ($null -eq $priorForceSourceDate) { Remove-Item Env:FORCE_SOURCE_DATE -ErrorAction SilentlyContinue } else { $env:FORCE_SOURCE_DATE = $priorForceSourceDate }
}

if ($cycle1.identity.bytes -ne $cycle2.identity.bytes -or $cycle1.identity.sha256 -ne $cycle2.identity.sha256) {
    throw "Clean-cycle PDF mismatch: $($cycle1.identity.sha256) != $($cycle2.identity.sha256)"
}
Assert-InputsUnchanged -Stage 'before final PDF installation'
Copy-Item -LiteralPath (Join-Path $workDir 'cycle-2.pdf') -Destination $outputPdf -Force
$outputIdentity = Get-Identity -Path $outputPdf

$declaredInputs = @($inputPaths.GetEnumerator() | Sort-Object Key | ForEach-Object {
    [ordered]@{ path = $_.Key; bytes = $_.Value.bytes; sha256 = $_.Value.sha256 }
})
$buildReceipt = [ordered]@{
    schema_version = 1
    workflow = 'o011-complete-reader-pdf-build-v1'
    engine = (& $pdfLatex --version | Select-Object -First 1)
    command = 'pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -recorder -output-directory=<task-local build/complete-work> -jobname=complete-reader generated/complete-reader-driver.tex from build/complete-stage/build (three passes per clean cycle; two clean cycles)'
    deterministic_clean_cycles = $true
    exact_unit22_public_prefix = $prefixFrozen
    driver_derivation = $driverReceipt
    official_exam_solution_gates = @($examGates)
    preparation = @($prepareBindings)
    core_units = @(
        foreach ($unit in 23..29) {
            $unitKey = [string]$unit
            [ordered]@{
                unit = $unit
                source_supplied_solution_numbers = @($solutionNumbers[$unitKey])
            }
        }
    )
    original_bridges = @('Lie groups and Lie algebras', 'de Rham cohomology and differential topology')
    exam_surfaces = [ordered]@{ learner_forms = 10; official_solution_forms = 10; original_repairs = 6 }
    geometry = [ordered]@{ paper = 'A4'; margin = '22mm'; centered = $true; class_option = 'oneside' }
    cycles = @($cycle1, $cycle2)
    inputs = $declaredInputs
    output = [ordered]@{ path = 'output/pdf/geometri-diferensial-manifold-mulus-edisi-lengkap-id.pdf'; bytes = $outputIdentity.bytes; sha256 = $outputIdentity.sha256 }
    structural_verifier = [ordered]@{ path = 'scripts/verify_complete_reader.py'; output = 'qa/complete/pdf_structural_qa.json' }
}
$buildReceiptPath = Join-Path $qaDir 'build.json'
Write-JsonFile -Path $buildReceiptPath -Value $buildReceipt

& $python (Join-Path $laneRoot 'scripts\verify_complete_reader.py')
if ($LASTEXITCODE -ne 0) {
    throw 'Complete-reader structural verifier did not pass'
}

$structural = Read-JsonFile -Path (Join-Path $qaDir 'pdf_structural_qa.json')
if ($structural.status -ne 'pass') {
    throw 'Complete-reader structural QA receipt does not report pass'
}

Write-Output (ConvertTo-Json -InputObject $buildReceipt -Depth 16)
