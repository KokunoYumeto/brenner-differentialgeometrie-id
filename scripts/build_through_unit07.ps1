[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$laneRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$buildDir = Join-Path $laneRoot 'build'
$generatedDir = Join-Path $buildDir 'generated'
$mediaDir = Join-Path $generatedDir 'media'
$qaDir = Join-Path $laneRoot 'qa\unit-07'
$workDir = Join-Path $laneRoot 'tmp\pdfs\through-unit07-build'
$outputDir = Join-Path $laneRoot 'output\pdf'
$outputPdf = Join-Path $outputDir 'geometri-diferensial-manifold-mulus-hingga-unit-07-id.pdf'

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

# Rebuild and verify the complete admitted Unit 1--6 prefix first. Its build
# receipt becomes a transitive, hash-bound input to this cumulative extension.
& (Join-Path $laneRoot 'scripts\build_through_unit06.ps1') | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Cumulative Unit 1--6 prefix build failed"
}

$translationPairs = @(
    @{ source = 'lecture06_source.de.tex'; target = 'unit-06\lecture06.id.tex'; receipt = 'unit-06\lecture06_translation.json'; corrections = 'LECTURE06_PROTECTED_CORRECTIONS.json' },
    @{ source = 'worksheet06_source.de.tex'; target = 'unit-06\worksheet06.id.tex'; receipt = 'unit-06\worksheet06_translation.json'; corrections = 'WORKSHEET06_PROTECTED_CORRECTIONS.json' },
    @{ source = 'worksheet06_exercise02_solution_source.de.tex'; target = 'unit-06\worksheet06_exercise02_solution.id.tex'; receipt = 'unit-06\worksheet06_exercise02_solution_translation.json'; corrections = 'SOLUTION06_02_PROTECTED_CORRECTIONS.json' },
    @{ source = 'worksheet06_exercise06_solution_source.de.tex'; target = 'unit-06\worksheet06_exercise06_solution.id.tex'; receipt = 'unit-06\worksheet06_exercise06_solution_translation.json' },
    @{ source = 'worksheet06_exercise09_solution_source.de.tex'; target = 'unit-06\worksheet06_exercise09_solution.id.tex'; receipt = 'unit-06\worksheet06_exercise09_solution_translation.json' },
    @{ source = 'lecture07_source.de.tex'; target = 'unit-07\lecture07.id.tex'; receipt = 'unit-07\lecture07_translation.json'; corrections = 'LECTURE07_PROTECTED_CORRECTIONS.json' },
    @{ source = 'worksheet07_source.de.tex'; target = 'unit-07\worksheet07.id.tex'; receipt = 'unit-07\worksheet07_translation.json'; corrections = 'WORKSHEET07_PROTECTED_CORRECTIONS.json' },
    @{ source = 'worksheet07_exercise04_solution_source.de.tex'; target = 'unit-07\worksheet07_exercise04_solution.id.tex'; receipt = 'unit-07\worksheet07_exercise04_solution_translation.json' },
    @{ source = 'worksheet07_exercise07_solution_source.de.tex'; target = 'unit-07\worksheet07_exercise07_solution.id.tex'; receipt = 'unit-07\worksheet07_exercise07_solution_translation.json' },
    @{ source = 'worksheet07_exercise13_solution_source.de.tex'; target = 'unit-07\worksheet07_exercise13_solution.id.tex'; receipt = 'unit-07\worksheet07_exercise13_solution_translation.json' }
)
foreach ($pair in $translationPairs) {
    $verificationArguments = @(
        (Join-Path $laneRoot 'scripts\verify_unit_translation.py'),
        (Join-Path $laneRoot ('authority\expanded\' + $pair.source)),
        (Join-Path $laneRoot ('source\units\' + $pair.target)),
        '--project-root', $laneRoot,
        '--receipt', (Join-Path $laneRoot ('qa\' + $pair.receipt))
    )
    if ($pair.ContainsKey('corrections')) {
        $verificationArguments += @(
            '--corrections', (Join-Path $laneRoot ('00_control\' + $pair.corrections))
        )
    }
    Invoke-CheckedPython $verificationArguments
}

$preparations = @(
    @('unit-06\lecture06.id.tex', 'lecture06.id.build.tex', 'unit-06\lecture06_prepare.json'),
    @('unit-06\worksheet06.id.tex', 'worksheet06.id.build.tex', 'unit-06\worksheet06_prepare.json'),
    @('unit-06\worksheet06_exercise02_solution.id.tex', 'worksheet06_exercise02_solution.id.build.tex', 'unit-06\worksheet06_exercise02_solution_prepare.json'),
    @('unit-06\worksheet06_exercise06_solution.id.tex', 'worksheet06_exercise06_solution.id.build.tex', 'unit-06\worksheet06_exercise06_solution_prepare.json'),
    @('unit-06\worksheet06_exercise09_solution.id.tex', 'worksheet06_exercise09_solution.id.build.tex', 'unit-06\worksheet06_exercise09_solution_prepare.json'),
    @('unit-07\lecture07.id.tex', 'lecture07.id.build.tex', 'unit-07\lecture07_prepare.json'),
    @('unit-07\worksheet07.id.tex', 'worksheet07.id.build.tex', 'unit-07\worksheet07_prepare.json'),
    @('unit-07\worksheet07_exercise04_solution.id.tex', 'worksheet07_exercise04_solution.id.build.tex', 'unit-07\worksheet07_exercise04_solution_prepare.json'),
    @('unit-07\worksheet07_exercise07_solution.id.tex', 'worksheet07_exercise07_solution.id.build.tex', 'unit-07\worksheet07_exercise07_solution_prepare.json'),
    @('unit-07\worksheet07_exercise13_solution.id.tex', 'worksheet07_exercise13_solution.id.build.tex', 'unit-07\worksheet07_exercise13_solution_prepare.json')
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

Invoke-CheckedPython @(
    (Join-Path $laneRoot 'scripts\prepare_unit_media.py'),
    '--manifest', (Join-Path $laneRoot 'authority\brenner_media_rights_manifest.csv'),
    '--project-root', $laneRoot,
    '--source-dir', (Join-Path $laneRoot 'authority\media'),
    '--output-dir', $mediaDir,
    '--media-config', (Join-Path $laneRoot 'source\unit_media.json'),
    '--unit-number', '7',
    '--heading-level', 'section',
    '--attribution-tex', (Join-Path $generatedDir 'unit07-media-attribution-cumulative.tex'),
    '--receipt', (Join-Path $laneRoot 'qa\unit-07_media.json')
)

# The frozen Unit 7 TeX names two PNGs and one SVG through MediaWiki's
# underscore-normalized file names. Keep canonical Commons files with their
# exact space-bearing names, but create deterministic generated aliases for
# the wrapper's Unit 7-only lookup surface.
$unit7MediaAliases = @(
    @{ source = 'authority/media/Hyperboloid1.png'; target = 'build/generated/media/Hyperboloid1.png' },
    @{ source = 'authority/media/Stereographic projection in 3D.png'; target = 'build/generated/media/Stereographic_projection_in_3D.png' },
    @{ source = 'authority/media/Manifold zahyou3.png'; target = 'build/generated/media/Manifold_zahyou3.png' },
    @{ source = 'build/generated/media/Circle - black simple.png'; target = 'build/generated/media/Circle_-_black_simple.png' }
)
$aliasRows = foreach ($alias in $unit7MediaAliases) {
    $sourcePath = Join-Path $laneRoot $alias.source
    $targetPath = Join-Path $laneRoot $alias.target
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
        throw "Unit 7 media alias source missing: $sourcePath"
    }
    Copy-Item -LiteralPath $sourcePath -Destination $targetPath -Force
    [pscustomobject]@{
        source = $alias.source
        target = $alias.target
        bytes = (Get-Item -LiteralPath $targetPath).Length
        sha256 = (Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}
$aliasReceipt = [ordered]@{
    schema_version = 1
    workflow = 'o011-unit07-media-aliases-v1'
    aliases = @($aliasRows)
    wrapper_macro_surface = '\bildeinlesungpng,\bildeinlesungPNG,\bildeinlesungsvg'
}
$aliasReceiptPath = Join-Path $laneRoot 'qa\unit-07\MEDIA_ALIAS_RECEIPT.json'
$aliasReceiptBytes = [Text.UTF8Encoding]::new($false).GetBytes(($aliasReceipt | ConvertTo-Json -Depth 6) + "`n")
[IO.File]::WriteAllBytes($aliasReceiptPath, $aliasReceiptBytes)

$auxiliaryNames = @(
    'through-unit-07.aux', 'through-unit-07.log', 'through-unit-07.out',
    'through-unit-07.pdf', 'through-unit-07.toc', 'through-unit-07.lof',
    'through-unit-07.fls', 'through-unit-07.fdb_latexmk'
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
            & $pdfLatex '-interaction=nonstopmode' '-halt-on-error' '-file-line-error' '-recorder' 'through-unit-07.tex' 2>&1 |
                Out-File -LiteralPath $logPath -Encoding utf8
            if ($LASTEXITCODE -ne 0) {
                throw "pdflatex failed in cycle $Cycle pass $pass; see $logPath"
            }
            $cycleLogs += $logPath
        }
    }
    finally {
        Pop-Location
    }
    $built = Join-Path $buildDir 'through-unit-07.pdf'
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
    'qa/unit-06/build.json',
    'build/through-unit-07.tex',
    'build/brenner-compat.tex',
    'build/generated/lecture06.id.build.tex',
    'build/generated/worksheet06.id.build.tex',
    'build/generated/worksheet06_exercise02_solution.id.build.tex',
    'build/generated/worksheet06_exercise06_solution.id.build.tex',
    'build/generated/worksheet06_exercise09_solution.id.build.tex',
    'build/generated/unit06-media-attribution-cumulative.tex',
    'build/generated/lecture07.id.build.tex',
    'build/generated/worksheet07.id.build.tex',
    'build/generated/worksheet07_exercise04_solution.id.build.tex',
    'build/generated/worksheet07_exercise07_solution.id.build.tex',
    'build/generated/worksheet07_exercise13_solution.id.build.tex',
    'build/generated/unit07-media-attribution-cumulative.tex',
    'source/unit07_interactive_media.json',
    '00_control/LECTURE07_PROTECTED_CORRECTIONS.json',
    '00_control/WORKSHEET07_PROTECTED_CORRECTIONS.json',
    'qa/unit-07/INTERACTIVE_MEDIA_QA.json',
    'qa/unit-07/MEDIA_ALIAS_RECEIPT.json',
    'scripts/prepare_unit_tex.py',
    'scripts/prepare_unit_media.py',
    'qa/unit-06/lecture06_translation.json',
    'qa/unit-06/worksheet06_translation.json',
    'qa/unit-06/worksheet06_exercise02_solution_translation.json',
    'qa/unit-06/worksheet06_exercise06_solution_translation.json',
    'qa/unit-06/worksheet06_exercise09_solution_translation.json',
    'qa/unit-07/lecture07_translation.json',
    'qa/unit-07/worksheet07_translation.json',
    'qa/unit-07/worksheet07_exercise04_solution_translation.json',
    'qa/unit-07/worksheet07_exercise07_solution_translation.json',
    'qa/unit-07/worksheet07_exercise13_solution_translation.json',
    'qa/unit-07/lecture07_prepare.json',
    'qa/unit-07/worksheet07_prepare.json',
    'qa/unit-07/worksheet07_exercise04_solution_prepare.json',
    'qa/unit-07/worksheet07_exercise07_solution_prepare.json',
    'qa/unit-07/worksheet07_exercise13_solution_prepare.json',
    'qa/unit-07_media.json'
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
    workflow = 'o011-through-unit07-pdf-build-v1'
    engine = $engineVersion
    command = 'pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -recorder through-unit-07.tex (three passes per clean cycle; two cycles)'
    deterministic_clean_cycles = $true
    cumulative_prefix_receipt = 'qa/unit-06/build.json'
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
