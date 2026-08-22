[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$laneRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$buildDir = Join-Path $laneRoot 'build'
$generatedDir = Join-Path $buildDir 'generated'
$mediaDir = Join-Path $generatedDir 'media'
$qaDir = Join-Path $laneRoot 'qa\unit-02'
$workDir = Join-Path $laneRoot 'tmp\pdfs\through-unit02-build'
$outputDir = Join-Path $laneRoot 'output\pdf'
$outputPdf = Join-Path $outputDir 'geometri-diferensial-manifold-mulus-hingga-unit-02-id.pdf'

foreach ($directory in @($generatedDir, $mediaDir, $qaDir, $workDir, $outputDir)) {
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
}

$python = (Get-Command python -ErrorAction Stop).Source
$pdfLatex = (Get-Command pdflatex -ErrorAction Stop).Source

function Invoke-CheckedPython {
    param([string[]]$Arguments)
    & $python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code ${LASTEXITCODE}: $($Arguments -join ' ')"
    }
}

$translationPairs = @(
    @('lecture01_source.de.tex', 'unit-01\lecture01.id.tex', 'unit-01\lecture_translation.json'),
    @('worksheet01_source.de.tex', 'unit-01\worksheet01.id.tex', 'unit-01\worksheet_translation.json'),
    @('worksheet01_exercise01_solution_source.de.tex', 'unit-01\worksheet01_exercise01_solution.id.tex', 'unit-01\worksheet_exercise01_solution_translation.json'),
    @('lecture02_source.de.tex', 'unit-02\lecture02.id.tex', 'unit-02\lecture_translation.json'),
    @('worksheet02_source.de.tex', 'unit-02\worksheet02.id.tex', 'unit-02\worksheet_translation.json'),
    @('worksheet02_exercise01_solution_source.de.tex', 'unit-02\worksheet02_exercise01_solution.id.tex', 'unit-02\worksheet02_exercise01_solution_translation.json'),
    @('worksheet02_exercise02_solution_source.de.tex', 'unit-02\worksheet02_exercise02_solution.id.tex', 'unit-02\worksheet02_exercise02_solution_translation.json'),
    @('worksheet02_exercise07_solution_source.de.tex', 'unit-02\worksheet02_exercise07_solution.id.tex', 'unit-02\worksheet02_exercise07_solution_translation.json'),
    @('worksheet02_exercise12_solution_source.de.tex', 'unit-02\worksheet02_exercise12_solution.id.tex', 'unit-02\worksheet02_exercise12_solution_translation.json'),
    @('worksheet02_exercise13_solution_source.de.tex', 'unit-02\worksheet02_exercise13_solution.id.tex', 'unit-02\worksheet02_exercise13_solution_translation.json')
)
foreach ($pair in $translationPairs) {
    $arguments = @(
        (Join-Path $laneRoot 'scripts\verify_unit_translation.py'),
        (Join-Path $laneRoot ('authority\expanded\' + $pair[0])),
        (Join-Path $laneRoot ('source\units\' + $pair[1])),
        '--project-root', $laneRoot,
        '--receipt', (Join-Path $laneRoot ('qa\' + $pair[2]))
    )
    if ($pair[0] -eq 'lecture01_source.de.tex') {
        $arguments += @('--corrections', (Join-Path $laneRoot '00_control\PROTECTED_CORRECTIONS.json'))
    }
    elseif ($pair[0] -eq 'worksheet01_source.de.tex') {
        $arguments += @('--corrections', (Join-Path $laneRoot '00_control\WORKSHEET01_PROTECTED_CORRECTIONS.json'))
    }
    elseif ($pair[0] -eq 'lecture02_source.de.tex') {
        $arguments += @('--corrections', (Join-Path $laneRoot '00_control\LECTURE02_PROTECTED_CORRECTIONS.json'))
    }
    elseif ($pair[0] -eq 'worksheet02_source.de.tex') {
        $arguments += @('--corrections', (Join-Path $laneRoot '00_control\WORKSHEET02_PROTECTED_CORRECTIONS.json'))
    }
    elseif ($pair[0] -eq 'worksheet02_exercise01_solution_source.de.tex') {
        $arguments += @('--corrections', (Join-Path $laneRoot '00_control\SOLUTION01_PROTECTED_CORRECTIONS.json'))
    }
    elseif ($pair[0] -eq 'worksheet02_exercise02_solution_source.de.tex') {
        $arguments += @('--corrections', (Join-Path $laneRoot '00_control\SOLUTION02_PROTECTED_CORRECTIONS.json'))
    }
    elseif ($pair[0] -eq 'worksheet02_exercise07_solution_source.de.tex') {
        $arguments += @('--corrections', (Join-Path $laneRoot '00_control\SOLUTION07_PROTECTED_CORRECTIONS.json'))
    }
    elseif ($pair[0] -eq 'worksheet02_exercise13_solution_source.de.tex') {
        $arguments += @('--corrections', (Join-Path $laneRoot '00_control\SOLUTION13_PROTECTED_CORRECTIONS.json'))
    }
    Invoke-CheckedPython $arguments
}

Invoke-CheckedPython @(
    (Join-Path $laneRoot 'scripts\make_portable_preamble.py'),
    (Join-Path $laneRoot 'authority\expanded\script_preamble_source.de.tex'),
    (Join-Path $buildDir 'brenner-compat.tex'),
    '--project-root', $laneRoot,
    '--receipt', (Join-Path $laneRoot 'qa\portable_preamble.json')
)

$preparations = @(
    @('unit-01\lecture01.id.tex', 'lecture01.id.build.tex', 'unit-01\lecture01_prepare.json'),
    @('unit-01\worksheet01.id.tex', 'worksheet01.id.build.tex', 'unit-01\worksheet01_prepare.json'),
    @('unit-01\worksheet01_exercise01_solution.id.tex', 'worksheet01_exercise01_solution.id.build.tex', 'unit-01\worksheet01_exercise01_solution_prepare.json'),
    @('unit-02\lecture02.id.tex', 'lecture02.id.build.tex', 'unit-02\lecture02_prepare.json'),
    @('unit-02\worksheet02.id.tex', 'worksheet02.id.build.tex', 'unit-02\worksheet02_prepare.json'),
    @('unit-02\worksheet02_exercise01_solution.id.tex', 'worksheet02_exercise01_solution.id.build.tex', 'unit-02\worksheet02_exercise01_solution_prepare.json'),
    @('unit-02\worksheet02_exercise02_solution.id.tex', 'worksheet02_exercise02_solution.id.build.tex', 'unit-02\worksheet02_exercise02_solution_prepare.json'),
    @('unit-02\worksheet02_exercise07_solution.id.tex', 'worksheet02_exercise07_solution.id.build.tex', 'unit-02\worksheet02_exercise07_solution_prepare.json'),
    @('unit-02\worksheet02_exercise12_solution.id.tex', 'worksheet02_exercise12_solution.id.build.tex', 'unit-02\worksheet02_exercise12_solution_prepare.json'),
    @('unit-02\worksheet02_exercise13_solution.id.tex', 'worksheet02_exercise13_solution.id.build.tex', 'unit-02\worksheet02_exercise13_solution_prepare.json')
)
foreach ($item in $preparations) {
    Invoke-CheckedPython @(
        (Join-Path $laneRoot 'scripts\prepare_unit_tex.py'),
        (Join-Path $laneRoot ('source\units\' + $item[0])),
        (Join-Path $generatedDir $item[1]),
        '--project-root', $laneRoot,
        '--receipt', (Join-Path $laneRoot ('qa\' + $item[2]))
    )
}

foreach ($unit in 1..2) {
    $unitPadded = $unit.ToString('00')
    Invoke-CheckedPython @(
        (Join-Path $laneRoot 'scripts\prepare_unit_media.py'),
        '--manifest', (Join-Path $laneRoot 'authority\brenner_media_rights_manifest.csv'),
        '--project-root', $laneRoot,
        '--source-dir', (Join-Path $laneRoot 'authority\media'),
        '--output-dir', $mediaDir,
        '--media-config', (Join-Path $laneRoot 'source\unit_media.json'),
        '--unit-number', $unit.ToString(),
        '--heading-level', 'section',
        '--attribution-tex', (Join-Path $generatedDir ("unit{0}-media-attribution-cumulative.tex" -f $unitPadded)),
        '--receipt', (Join-Path $laneRoot ("qa\unit-{0}_media.json" -f $unitPadded))
    )
}

$auxiliaryNames = @(
    'through-unit-02.aux', 'through-unit-02.log', 'through-unit-02.out',
    'through-unit-02.pdf', 'through-unit-02.toc', 'through-unit-02.lof',
    'through-unit-02.fls', 'through-unit-02.fdb_latexmk'
)

function Clear-ExactAuxiliaryFiles {
    foreach ($name in $auxiliaryNames) {
        $path = Join-Path $buildDir $name
        if (Test-Path -LiteralPath $path) {
            Remove-Item -LiteralPath $path -Force
        }
    }
}

function Invoke-BuildCycle {
    param([int]$Cycle)
    Clear-ExactAuxiliaryFiles
    $cycleLogs = @()
    Push-Location $buildDir
    try {
        foreach ($pass in 1..3) {
            $logPath = Join-Path $workDir ("cycle-{0}-pass-{1}.console.txt" -f $Cycle, $pass)
            $arguments = @(
                '-interaction=nonstopmode', '-halt-on-error', '-file-line-error',
                '-recorder', 'through-unit-02.tex'
            )
            & $pdfLatex @arguments 2>&1 | Out-File -LiteralPath $logPath -Encoding utf8
            if ($LASTEXITCODE -ne 0) {
                throw "pdflatex failed in cycle $Cycle pass $pass; see $logPath"
            }
            $cycleLogs += $logPath
        }
    }
    finally {
        Pop-Location
    }
    $built = Join-Path $buildDir 'through-unit-02.pdf'
    if (-not (Test-Path -LiteralPath $built)) {
        throw "pdflatex did not create $built"
    }
    $cyclePdf = Join-Path $workDir ("cycle-{0}.pdf" -f $Cycle)
    Copy-Item -LiteralPath $built -Destination $cyclePdf -Force
    return [pscustomobject]@{
        cycle = $Cycle
        pdf = [IO.Path]::GetRelativePath($laneRoot, $cyclePdf).Replace('\', '/')
        bytes = (Get-Item -LiteralPath $cyclePdf).Length
        sha256 = (Get-FileHash -LiteralPath $cyclePdf -Algorithm SHA256).Hash.ToLowerInvariant()
        logs = @($cycleLogs | ForEach-Object {
            [pscustomobject]@{
                path = [IO.Path]::GetRelativePath($laneRoot, $_).Replace('\', '/')
                bytes = (Get-Item -LiteralPath $_).Length
                sha256 = (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash.ToLowerInvariant()
            }
        })
    }
}

$cycle1 = Invoke-BuildCycle -Cycle 1
$cycle2 = Invoke-BuildCycle -Cycle 2
if ($cycle1.bytes -ne $cycle2.bytes -or $cycle1.sha256 -ne $cycle2.sha256) {
    throw "clean-cycle PDF mismatch: $($cycle1.sha256) != $($cycle2.sha256)"
}
Copy-Item -LiteralPath (Join-Path $workDir 'cycle-2.pdf') -Destination $outputPdf -Force

$inputPaths = @(
    'build/through-unit-02.tex',
    'build/brenner-compat.tex',
    'build/generated/lecture01.id.build.tex',
    'build/generated/worksheet01.id.build.tex',
    'build/generated/worksheet01_exercise01_solution.id.build.tex',
    'build/generated/lecture02.id.build.tex',
    'build/generated/worksheet02.id.build.tex',
    'build/generated/worksheet02_exercise01_solution.id.build.tex',
    'build/generated/worksheet02_exercise02_solution.id.build.tex',
    'build/generated/worksheet02_exercise07_solution.id.build.tex',
    'build/generated/worksheet02_exercise12_solution.id.build.tex',
    'build/generated/worksheet02_exercise13_solution.id.build.tex',
    'build/generated/unit01-media-attribution-cumulative.tex',
    'build/generated/unit02-media-attribution-cumulative.tex',
    'qa/unit-01_media.json',
    'qa/unit-02_media.json'
)
$inputs = @($inputPaths | ForEach-Object {
    $path = Join-Path $laneRoot $_
    [pscustomobject]@{
        path = $_
        bytes = (Get-Item -LiteralPath $path).Length
        sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    }
})
$engineVersion = (& $pdfLatex --version | Select-Object -First 1)
$receipt = [ordered]@{
    schema_version = 1
    workflow = 'o011-through-unit02-pdf-build-v1'
    engine = $engineVersion
    command = 'pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -recorder through-unit-02.tex (three passes per clean cycle; two cycles)'
    deterministic_clean_cycles = $true
    cycles = @($cycle1, $cycle2)
    inputs = $inputs
    output = [ordered]@{
        path = [IO.Path]::GetRelativePath($laneRoot, $outputPdf).Replace('\', '/')
        bytes = (Get-Item -LiteralPath $outputPdf).Length
        sha256 = (Get-FileHash -LiteralPath $outputPdf -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}
$receiptPath = Join-Path $qaDir 'build.json'
$receiptBytes = [Text.UTF8Encoding]::new($false).GetBytes(($receipt | ConvertTo-Json -Depth 8) + "`n")
[IO.File]::WriteAllBytes($receiptPath, $receiptBytes)
Clear-ExactAuxiliaryFiles
Write-Output ($receipt | ConvertTo-Json -Depth 8)
