[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$laneRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$buildDir = Join-Path $laneRoot 'build'
$generatedDir = Join-Path $buildDir 'generated'
$mediaDir = Join-Path $generatedDir 'media'
$qaDir = Join-Path $laneRoot 'qa\unit-10'
$workDir = Join-Path $laneRoot 'tmp\pdfs\through-unit10-build'
$outputDir = Join-Path $laneRoot 'output\pdf'
$outputPdf = Join-Path $outputDir 'geometri-diferensial-manifold-mulus-hingga-unit-10-id.pdf'

foreach ($directory in @($generatedDir, $mediaDir, $qaDir, $workDir, $outputDir)) {
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
}

$python = (Get-Command python -ErrorAction Stop).Source
$pdfLatex = (Get-Command pdflatex -ErrorAction Stop).Source

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

function Assert-Identity {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][long]$Bytes,
        [Parameter(Mandatory)][string]$Sha256,
        [Parameter(Mandatory)][string]$Label
    )
    $actual = Get-Identity -Path $Path
    if ($null -eq $actual -or $actual.bytes -ne $Bytes -or $actual.sha256 -ne $Sha256.ToLowerInvariant()) {
        throw ($Label + ' identity mismatch at ' + $Path + ': ' + ($actual | ConvertTo-Json -Compress))
    }
}

function Invoke-CheckedPython {
    param([string[]]$Arguments)
    & $python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw ('Python command failed with exit code ' + $LASTEXITCODE + ': ' + ($Arguments -join ' '))
    }
}

# Rebuild the complete admitted Unit 1--7 prefix. Its deterministic receipt is
# a transitive, hash-bound input to this cumulative Unit 10 extension.
& (Join-Path $laneRoot 'scripts\build_through_unit07.ps1') | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw 'Cumulative Unit 1--7 prefix build failed'
}

$translationPairs = @(
    [ordered]@{
        source = 'lecture08_source.de.tex'; sourceBytes = 17329; sourceSha256 = '91fef67aac0b5f0f539f73a672d3bb1c79b277986cc5561c0e27801a9973129a'
        target = 'unit-08\lecture08.id.tex'; targetBytes = 18099; targetSha256 = '90574f5e2879e7bc07ee20e5a335d78bd1b84f5f94b52f257dcdd0f3abf6f8bf'
        receipt = 'unit-08\lecture08_translation.json'
        corrections = 'LECTURE08_PROTECTED_CORRECTIONS.json'; correctionsBytes = 3606; correctionsSha256 = '3e146bfa313157a80407fec4bc5bad54fada2db9d2c7d49677740b8bcc7371a2'
    },
    [ordered]@{
        source = 'worksheet08_source.de.tex'; sourceBytes = 12693; sourceSha256 = '1313fbf0d8d068f5089ee8381dafc811079a404dc0d7c847c3b3bab85afceb9a'
        target = 'unit-08\worksheet08.id.tex'; targetBytes = 13094; targetSha256 = '8cd886c6c2f9a7019f5e2319d9930a729572e016ee823346200228e3265b40bf'
        receipt = 'unit-08\worksheet08_translation.json'
        corrections = 'WORKSHEET08_PROTECTED_CORRECTIONS.json'; correctionsBytes = 813; correctionsSha256 = '17a1df1e6b8066dce199b797227ffd33af6ba8a8add8ea8b13ec044478a6ccdf'
    },
    [ordered]@{
        source = 'worksheet08_exercise11_solution_source.de.tex'; sourceBytes = 1175; sourceSha256 = '6ae059c8bfa3ea5d0eb6ee3766647fa5b9a85a5592bff3597d3df185e04622a1'
        target = 'unit-08\worksheet08_exercise11_solution.id.tex'; targetBytes = 1204; targetSha256 = '1a55e39744d436cf93afd514a638197019f2e9e139279abbb3576a1704757a2b'
        receipt = 'unit-08\worksheet08_exercise11_solution_translation.json'
    },
    [ordered]@{
        source = 'worksheet08_exercise13_solution_source.de.tex'; sourceBytes = 2405; sourceSha256 = '31f2e73e81a59c36f23a4f2b35fb1a56399a77d7df3cc2d5b5f43babbc4f7b7d'
        target = 'unit-08\worksheet08_exercise13_solution.id.tex'; targetBytes = 3088; targetSha256 = '73ee95e00976b81b69b5bee684d2f941c39ca413e4dd0f2696f29081456215ed'
        receipt = 'unit-08\worksheet08_exercise13_solution_translation.json'
        corrections = 'SOLUTION13_08_PROTECTED_CORRECTIONS.json'; correctionsBytes = 1463; correctionsSha256 = '89413b8115a9670c00ae4c0a674773162fbe64194020254a3027fc5e7607ecd1'
    },
    [ordered]@{
        source = 'lecture09_source.de.tex'; sourceBytes = 25318; sourceSha256 = '88993b430407a58ad8db4b8006320a3b8ca190fbb02a04d52f3fc8731b55526a'
        target = 'unit-09\lecture09.id.tex'; targetBytes = 26132; targetSha256 = '9e3b12f4168c4f7a8c246c4c9106d1154be237e9080e12e0a21bcd8942d61bba'
        receipt = 'unit-09\lecture09_translation.json'
        corrections = 'LECTURE09_PROTECTED_CORRECTIONS.json'; correctionsBytes = 3567; correctionsSha256 = '6138e9ad10c2911a0041f863f7657471735351b794dc7247f20cccab27e0b048'
    },
    [ordered]@{
        source = 'worksheet09_source.de.tex'; sourceBytes = 9211; sourceSha256 = 'a852a6a793f860d387075bb38be9606cb2c3b26b4558e15323ba61bb127aaa3f'
        target = 'unit-09\worksheet09.id.tex'; targetBytes = 10331; targetSha256 = '4079437947ab31c9216e3ee6059badc8cf7d780ead1df93cd5cfb6f1cd7d3e9d'
        receipt = 'unit-09\worksheet09_translation.json'
        corrections = 'WORKSHEET09_PROTECTED_CORRECTIONS.json'; correctionsBytes = 2815; correctionsSha256 = 'fdb33b4fd49cbcc77b63c64b91cf54a74264f6670528d3a06775bdb6715f9e76'
    },
    [ordered]@{
        source = 'lecture10_source.de.tex'; sourceBytes = 22299; sourceSha256 = 'd9958463f904b6d4118203fc759307b1e97d758296ec1aec4b1e6747309bfa07'
        target = 'unit-10\lecture10.id.tex'; targetBytes = 23152; targetSha256 = 'bafd2d5f8d1307438c42f2b20a1914f143f097ddc7f37c2e1e9b99dccb340044'
        receipt = 'unit-10\lecture10_translation.json'
        corrections = 'LECTURE10_PROTECTED_CORRECTIONS.json'; correctionsBytes = 5654; correctionsSha256 = '017d0be88ec8335dcfdc91e264cef50b7162a562c82ffdee2283a380c4a4a8e6'
    },
    [ordered]@{
        source = 'worksheet10_source.de.tex'; sourceBytes = 16246; sourceSha256 = '0bb2340e60fd19551d420565bd9296e259eacf786a4262dc892395c1f2cbb786'
        target = 'unit-10\worksheet10.id.tex'; targetBytes = 16155; targetSha256 = '3a386ddb1a7e29475d54ca052c518b9b7c7447cefb2c6158f1a288c9b816ac4a'
        receipt = 'unit-10\worksheet10_translation.json'
        corrections = 'WORKSHEET10_PROTECTED_CORRECTIONS.json'; correctionsBytes = 3580; correctionsSha256 = '1adff375a3d5c86c6a9dcaeaa526a849b5de77e7ee8fc3ccd301be982df238d2'
    },
    [ordered]@{
        source = 'worksheet10_exercise09_solution_source.de.tex'; sourceBytes = 2372; sourceSha256 = '834634b11a1139ad6766043844108f945466cf4ebb45a23b3838fac32814c784'
        target = 'unit-10\worksheet10_exercise09_solution.id.tex'; targetBytes = 2822; targetSha256 = 'f4d86590a7244ce6006f2d7812700e4038391fe9808bf733b3c731e1d1cfe088'
        receipt = 'unit-10\worksheet10_exercise09_solution_translation.json'
        corrections = 'SOLUTION09_10_PROTECTED_CORRECTIONS.json'; correctionsBytes = 1114; correctionsSha256 = 'df17028c1dba9ae38239ef1b2cdea8d80e0030ef23f24bb9822b594c84f8d832'
    },
    [ordered]@{
        source = 'worksheet10_exercise10_solution_source.de.tex'; sourceBytes = 5002; sourceSha256 = '7d5ddb258d592ae0efcf699c4c2bfee47fb0bf4a92554b616cdf27cca9481a78'
        target = 'unit-10\worksheet10_exercise10_solution.id.tex'; targetBytes = 5275; targetSha256 = '4af0e5d19acc8555b0deb5fd7503008b86bb740f76ef8ce1482ff95d09cc7b22'
        receipt = 'unit-10\worksheet10_exercise10_solution_translation.json'
        corrections = 'SOLUTION10_10_PROTECTED_CORRECTIONS.json'; correctionsBytes = 1366; correctionsSha256 = '04c04b845d9190f7b659475207007cd292c95c73940e66ad0d473b3e82495da4'
    },
    [ordered]@{
        source = 'worksheet10_exercise15_solution_source.de.tex'; sourceBytes = 2266; sourceSha256 = 'd4eec7ea3336812723021e08c9efe24592b99a7ce21f8ad5e74a6ba8d0dbc143'
        target = 'unit-10\worksheet10_exercise15_solution.id.tex'; targetBytes = 2544; targetSha256 = 'df54358b3ac368df7d552f21a38f09fbceb0c90055066e25944a11359c5ab2d1'
        receipt = 'unit-10\worksheet10_exercise15_solution_translation.json'
        corrections = 'SOLUTION15_10_PROTECTED_CORRECTIONS.json'; correctionsBytes = 1921; correctionsSha256 = 'dca94c71fdb1e461e87ffdd35bc96b0b5d51507f528dd67793760c2204450ce3'
    },
    [ordered]@{
        source = 'worksheet10_exercise25_solution_source.de.tex'; sourceBytes = 1317; sourceSha256 = '3d4501800dc153183f9dbd86269956dc73a1787e5961b56004dc383dc3cc1617'
        target = 'unit-10\worksheet10_exercise25_solution.id.tex'; targetBytes = 1568; targetSha256 = '18c69f5473ffea083ed655dd8542e2e466a0fee07175e355f3125447b26d21d5'
        receipt = 'unit-10\worksheet10_exercise25_solution_translation.json'
        corrections = 'SOLUTION25_10_PROTECTED_CORRECTIONS.json'; correctionsBytes = 1615; correctionsSha256 = '9fcb39e581ff87a5475194ed6eeca994bcbda36260a3e4e4b6e6f91d70768f3d'
    }
)

foreach ($pair in $translationPairs) {
    $sourcePath = Join-Path $laneRoot ('authority\expanded\' + $pair.source)
    $targetPath = Join-Path $laneRoot ('source\units\' + $pair.target)
    Assert-Identity -Path $sourcePath -Bytes $pair.sourceBytes -Sha256 $pair.sourceSha256 -Label 'frozen authority'
    Assert-Identity -Path $targetPath -Bytes $pair.targetBytes -Sha256 $pair.targetSha256 -Label 'frozen Indonesian target'
    $verificationArguments = @(
        (Join-Path $laneRoot 'scripts\verify_unit_translation.py'),
        $sourcePath,
        $targetPath,
        '--project-root', $laneRoot,
        '--receipt', (Join-Path $laneRoot ('qa\' + $pair.receipt))
    )
    if ($pair.Contains('corrections')) {
        $correctionPath = Join-Path $laneRoot ('00_control\' + $pair.corrections)
        Assert-Identity -Path $correctionPath -Bytes $pair.correctionsBytes -Sha256 $pair.correctionsSha256 -Label 'protected correction manifest'
        $verificationArguments += @('--corrections', $correctionPath)
    }
    Invoke-CheckedPython $verificationArguments
    $receiptPath = Join-Path $laneRoot ('qa\' + $pair.receipt)
    $translationReceipt = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
    if (
        $translationReceipt.status -ne 'pass' -or
        $translationReceipt.source -ne ('authority/expanded/' + $pair.source) -or
        $translationReceipt.target -ne ('source/units/' + $pair.target.Replace('\', '/')) -or
        $translationReceipt.source_bytes -ne $pair.sourceBytes -or
        $translationReceipt.source_sha256 -ne $pair.sourceSha256 -or
        $translationReceipt.target_bytes -ne $pair.targetBytes -or
        $translationReceipt.target_sha256 -ne $pair.targetSha256
    ) {
        throw "Translation receipt closure failure: $receiptPath"
    }
}

$mathQa = @(
    @{ path = 'qa\unit-08\POST_CORRECTION_MATH_QA.json'; bytes = 5279; sha256 = 'd09f92ff5de7cbacb37c5bd3a0ec61516877d473c3362cd0cdeeb18410af8974' },
    @{ path = 'qa\unit-09\POST_CORRECTION_MATH_QA.json'; bytes = 4390; sha256 = '57e90ee6c04fcecd5fbc31b23e25d8d3f30f7efaf322101a30ab8f9c867a27be' },
    @{ path = 'qa\unit-10\POST_CORRECTION_MATH_QA.json'; bytes = 8872; sha256 = 'c81d9c1459af5b32ca7b3e1af89c573c4f5881eec81dab2340d9a4ae39c497a6' }
)
foreach ($item in $mathQa) {
    $path = Join-Path $laneRoot $item.path
    Assert-Identity -Path $path -Bytes $item.bytes -Sha256 $item.sha256 -Label 'post-correction mathematics QA'
    if ((Get-Content -LiteralPath $path -Raw | ConvertFrom-Json).status -ne 'pass') {
        throw "Post-correction mathematics QA does not pass: $path"
    }
}

$preparations = @(
    @('unit-08\lecture08.id.tex', 'lecture08.id.build.tex', 'unit-08\lecture08_prepare.json'),
    @('unit-08\worksheet08.id.tex', 'worksheet08.id.build.tex', 'unit-08\worksheet08_prepare.json'),
    @('unit-08\worksheet08_exercise11_solution.id.tex', 'worksheet08_exercise11_solution.id.build.tex', 'unit-08\worksheet08_exercise11_solution_prepare.json'),
    @('unit-08\worksheet08_exercise13_solution.id.tex', 'worksheet08_exercise13_solution.id.build.tex', 'unit-08\worksheet08_exercise13_solution_prepare.json'),
    @('unit-09\lecture09.id.tex', 'lecture09.id.build.tex', 'unit-09\lecture09_prepare.json'),
    @('unit-09\worksheet09.id.tex', 'worksheet09.id.build.tex', 'unit-09\worksheet09_prepare.json'),
    @('unit-10\lecture10.id.tex', 'lecture10.id.build.tex', 'unit-10\lecture10_prepare.json'),
    @('unit-10\worksheet10.id.tex', 'worksheet10.id.build.tex', 'unit-10\worksheet10_prepare.json'),
    @('unit-10\worksheet10_exercise09_solution.id.tex', 'worksheet10_exercise09_solution.id.build.tex', 'unit-10\worksheet10_exercise09_solution_prepare.json'),
    @('unit-10\worksheet10_exercise10_solution.id.tex', 'worksheet10_exercise10_solution.id.build.tex', 'unit-10\worksheet10_exercise10_solution_prepare.json'),
    @('unit-10\worksheet10_exercise15_solution.id.tex', 'worksheet10_exercise15_solution.id.build.tex', 'unit-10\worksheet10_exercise15_solution_prepare.json'),
    @('unit-10\worksheet10_exercise25_solution.id.tex', 'worksheet10_exercise25_solution.id.build.tex', 'unit-10\worksheet10_exercise25_solution_prepare.json')
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

# The translated fact-type labels are reader text, while \inputfaktbeweis also
# treats that argument as a LaTeX environment name. The inherited compatibility
# layer defines the German environment names but not these two Indonesian
# aliases. Generate a deterministic wrapper derivative rather than mutating the
# frozen reader fragments or any published-prefix compatibility file.
$wrapperPath = Join-Path $buildDir 'through-unit-10.tex'
$driverPath = Join-Path $generatedDir 'through-unit-10-driver.tex'
$wrapperText = [IO.File]::ReadAllText($wrapperPath, [Text.Encoding]::UTF8)
$compatMarker = '\input{brenner-compat.tex}'
if (($wrapperText.Split($compatMarker).Count - 1) -ne 1) {
    throw 'Unit 10 wrapper must contain exactly one compatibility-layer input'
}
$environmentAliases = @'
\newtheorem{Proposisi}[fakt]{Proposisi}
\newtheorem{Lema}[fakt]{Lema}
% The inherited loose image macro can strand a caption on the next page.
% Keep each image and the caption inside its source argument as one block in
% this cumulative reader wrapper, without mutating the published prefix layer.
\renewcommand{\bild}[1]{%
\par\vspace{4mm}%
\noindent\begin{minipage}{\linewidth}#1\end{minipage}%
\par}
'@
$driverText = $wrapperText.Replace($compatMarker, $compatMarker + [Environment]::NewLine + $environmentAliases.TrimEnd())
[IO.File]::WriteAllText($driverPath, $driverText, [Text.UTF8Encoding]::new($false))
$driverReceipt = [ordered]@{
    schema_version = 1
    workflow = 'o011-unit10-wrapper-compatibility-v1'
    input = [ordered]@{
        path = 'build/through-unit-10.tex'
        bytes = (Get-Item -LiteralPath $wrapperPath).Length
        sha256 = (Get-FileHash -LiteralPath $wrapperPath -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    output = [ordered]@{
        path = 'build/generated/through-unit-10-driver.tex'
        bytes = (Get-Item -LiteralPath $driverPath).Length
        sha256 = (Get-FileHash -LiteralPath $driverPath -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    added_environment_aliases = @('Proposisi', 'Lema')
}
$driverReceiptPath = Join-Path $qaDir 'WRAPPER_COMPATIBILITY_RECEIPT.json'
$driverReceiptBytes = [Text.UTF8Encoding]::new($false).GetBytes(($driverReceipt | ConvertTo-Json -Depth 6) + [Environment]::NewLine)
[IO.File]::WriteAllBytes($driverReceiptPath, $driverReceiptBytes)

foreach ($unit in 8..10) {
    Invoke-CheckedPython @(
        (Join-Path $laneRoot 'scripts\prepare_unit_media.py'),
        '--manifest', (Join-Path $laneRoot 'authority\brenner_media_rights_manifest.csv'),
        '--project-root', $laneRoot,
        '--source-dir', (Join-Path $laneRoot 'authority\media'),
        '--output-dir', $mediaDir,
        '--media-config', (Join-Path $laneRoot 'source\unit_media.json'),
        '--unit-number', $unit.ToString(),
        '--heading-level', 'section',
        '--attribution-tex', (Join-Path $generatedDir ('unit{0:D2}-media-attribution-cumulative.tex' -f $unit)),
        '--receipt', (Join-Path $laneRoot ('qa\unit-{0:D2}_media.json' -f $unit))
    )
}

# The source uses MediaWiki underscore-normalized loader arguments. Preserve
# canonical filenames and make only exact, hash-receipted aliases.
$persistentAliases = @(
    @{ source = 'build/generated/media/Tangent bundle.png'; target = 'build/generated/media/Tangent_bundle.png'; role = 'SVG print derivative alias' }
)
$aliasRows = @(foreach ($alias in $persistentAliases) {
    $sourcePath = Join-Path $laneRoot $alias.source
    $targetPath = Join-Path $laneRoot $alias.target
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
        throw "Media alias source missing: $sourcePath"
    }
    Copy-Item -LiteralPath $sourcePath -Destination $targetPath -Force
    [ordered]@{
        source = $alias.source
        target = $alias.target
        role = $alias.role
        transient = $false
        bytes = (Get-Item -LiteralPath $targetPath).Length
        sha256 = (Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash.ToLowerInvariant()
    }
})

$jpegSource = Join-Path $laneRoot 'authority\media\Torus vectors oblique.jpg'
$temporaryJpegAlias = Join-Path $laneRoot 'authority\media\Torus_vectors_oblique.jpg'
if (Test-Path -LiteralPath $temporaryJpegAlias -PathType Leaf) {
    $existing = Get-Identity -Path $temporaryJpegAlias
    $canonical = Get-Identity -Path $jpegSource
    if ($existing.bytes -ne $canonical.bytes -or $existing.sha256 -ne $canonical.sha256) {
        throw "Refusing to replace non-identical pre-existing JPEG alias: $temporaryJpegAlias"
    }
    Remove-Item -LiteralPath $temporaryJpegAlias -Force
}
Copy-Item -LiteralPath $jpegSource -Destination $temporaryJpegAlias
$aliasRows += [ordered]@{
    source = 'authority/media/Torus vectors oblique.jpg'
    target = 'authority/media/Torus_vectors_oblique.jpg'
    role = 'temporary MediaWiki JPEG loader alias'
    transient = $true
    bytes = (Get-Item -LiteralPath $temporaryJpegAlias).Length
    sha256 = (Get-FileHash -LiteralPath $temporaryJpegAlias -Algorithm SHA256).Hash.ToLowerInvariant()
}
$aliasReceipt = [ordered]@{
    schema_version = 1
    workflow = 'o011-unit10-media-aliases-v1'
    aliases = @($aliasRows)
    wrapper_macro_surface = '\bildeinlesungsvg,\bildeinlesungjpg'
    transient_alias_removed_after_build = $true
}
$aliasReceiptPath = Join-Path $qaDir 'MEDIA_ALIAS_RECEIPT.json'
$aliasReceiptBytes = [Text.UTF8Encoding]::new($false).GetBytes(($aliasReceipt | ConvertTo-Json -Depth 6) + [Environment]::NewLine)
[IO.File]::WriteAllBytes($aliasReceiptPath, $aliasReceiptBytes)

$auxiliaryNames = @(
    'through-unit-10.aux', 'through-unit-10.log', 'through-unit-10.out',
    'through-unit-10.pdf', 'through-unit-10.toc', 'through-unit-10.lof',
    'through-unit-10.fls', 'through-unit-10.fdb_latexmk'
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
            & $pdfLatex '-interaction=nonstopmode' '-halt-on-error' '-file-line-error' '-recorder' '-jobname=through-unit-10' 'generated/through-unit-10-driver.tex' 2>&1 |
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
    $built = Join-Path $buildDir 'through-unit-10.pdf'
    if (-not (Test-Path -LiteralPath $built -PathType Leaf)) {
        throw "pdflatex did not create $built"
    }
    $cyclePdf = Join-Path $workDir ("cycle-{0}.pdf" -f $Cycle)
    Copy-Item -LiteralPath $built -Destination $cyclePdf -Force
    return [ordered]@{
        cycle = $Cycle
        pdf = [IO.Path]::GetRelativePath($laneRoot, $cyclePdf).Replace('\', '/')
        bytes = (Get-Item -LiteralPath $cyclePdf).Length
        sha256 = (Get-FileHash -LiteralPath $cyclePdf -Algorithm SHA256).Hash.ToLowerInvariant()
        logs = @($cycleLogs | ForEach-Object {
            [ordered]@{
                path = [IO.Path]::GetRelativePath($laneRoot, $_).Replace('\', '/')
                bytes = (Get-Item -LiteralPath $_).Length
                sha256 = (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash.ToLowerInvariant()
            }
        })
    }
}

try {
    $cycle1 = Invoke-BuildCycle -Cycle 1
    $cycle2 = Invoke-BuildCycle -Cycle 2
    if ($cycle1.bytes -ne $cycle2.bytes -or $cycle1.sha256 -ne $cycle2.sha256) {
        throw "Clean-cycle PDF mismatch: $($cycle1.sha256) != $($cycle2.sha256)"
    }
    Copy-Item -LiteralPath (Join-Path $workDir 'cycle-2.pdf') -Destination $outputPdf -Force

    $inputPaths = @(
        'qa/unit-07/build.json',
        'build/through-unit-10.tex',
        'build/generated/through-unit-10-driver.tex',
        'build/brenner-compat.tex',
        'source/unit_media.json',
        'authority/brenner_media_rights_manifest.csv',
        'authority/media/Tangentialvektor.svg',
        'authority/media/Tangent bundle.svg',
        'authority/media/Torus vectors oblique.jpg',
        'build/generated/media/Tangentialvektor.png',
        'build/generated/media/Tangent bundle.png',
        'build/generated/media/Tangent_bundle.png',
        'build/generated/unit08-media-attribution-cumulative.tex',
        'build/generated/unit09-media-attribution-cumulative.tex',
        'build/generated/unit10-media-attribution-cumulative.tex',
        'qa/unit-08_media.json',
        'qa/unit-09_media.json',
        'qa/unit-10_media.json',
        'qa/unit-08/POST_CORRECTION_MATH_QA.json',
        'qa/unit-09/POST_CORRECTION_MATH_QA.json',
        'qa/unit-10/POST_CORRECTION_MATH_QA.json',
        'qa/unit-10/MEDIA_ALIAS_RECEIPT.json',
        'qa/unit-10/WRAPPER_COMPATIBILITY_RECEIPT.json',
        'scripts/build_through_unit10.ps1',
        'scripts/verify_unit_translation.py',
        'scripts/prepare_unit_tex.py',
        'scripts/prepare_unit_media.py'
    )
    foreach ($pair in $translationPairs) {
        $inputPaths += 'authority/expanded/' + $pair.source
        $inputPaths += 'source/units/' + $pair.target.Replace('\', '/')
        $inputPaths += 'qa/' + $pair.receipt.Replace('\', '/')
        if ($pair.Contains('corrections')) {
            $inputPaths += '00_control/' + $pair.corrections
        }
    }
    foreach ($item in $preparations) {
        $inputPaths += 'build/generated/' + $item[1]
        $inputPaths += 'qa/' + $item[2].Replace('\', '/')
    }
    $inputPaths = @($inputPaths | Sort-Object -Unique)
    $inputs = @($inputPaths | ForEach-Object {
        $path = Join-Path $laneRoot $_
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Declared build input missing: $path"
        }
        [ordered]@{
            path = $_.Replace('\', '/')
            bytes = (Get-Item -LiteralPath $path).Length
            sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    })
    $engineVersion = (& $pdfLatex --version | Select-Object -First 1)
    $receipt = [ordered]@{
        schema_version = 1
        workflow = 'o011-through-unit10-pdf-build-v1'
        engine = $engineVersion
        command = 'pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -recorder -jobname=through-unit-10 generated/through-unit-10-driver.tex (three passes per clean cycle; two cycles)'
        deterministic_clean_cycles = $true
        cumulative_prefix_receipt = 'qa/unit-07/build.json'
        cycles = @($cycle1, $cycle2)
        inputs = $inputs
        output = [ordered]@{
            path = [IO.Path]::GetRelativePath($laneRoot, $outputPdf).Replace('\', '/')
            bytes = (Get-Item -LiteralPath $outputPdf).Length
            sha256 = (Get-FileHash -LiteralPath $outputPdf -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }
    $receiptPath = Join-Path $qaDir 'build.json'
    $receiptBytes = [Text.UTF8Encoding]::new($false).GetBytes(($receipt | ConvertTo-Json -Depth 8) + [Environment]::NewLine)
    [IO.File]::WriteAllBytes($receiptPath, $receiptBytes)
}
finally {
    if (Test-Path -LiteralPath $temporaryJpegAlias -PathType Leaf) {
        $temporaryIdentity = Get-Identity -Path $temporaryJpegAlias
        $canonicalIdentity = Get-Identity -Path $jpegSource
        if ($temporaryIdentity.bytes -ne $canonicalIdentity.bytes -or $temporaryIdentity.sha256 -ne $canonicalIdentity.sha256) {
            throw "Refusing to remove changed temporary JPEG alias: $temporaryJpegAlias"
        }
        Remove-Item -LiteralPath $temporaryJpegAlias -Force
    }
    Clear-ExactAuxiliaryFiles
}

Write-Output ($receipt | ConvertTo-Json -Depth 8)
