[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$laneRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$buildDir = Join-Path $laneRoot 'build'
$generatedDir = Join-Path $buildDir 'generated'
$mediaDir = Join-Path $generatedDir 'media'
$qaDir = Join-Path $laneRoot 'qa\unit-19'
$workDir = Join-Path $laneRoot 'tmp\pdfs\through-unit19-build'
$outputDir = Join-Path $laneRoot 'output\pdf'
$outputPdf = Join-Path $outputDir 'geometri-diferensial-manifold-mulus-hingga-unit-19-id.pdf'
$mediaConfigPath = Join-Path $laneRoot 'source\unit_media.json'

$python = (Get-Command python -ErrorAction Stop).Source

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
    if (
        $null -eq $actual -or
        [long]$actual.bytes -ne $Bytes -or
        $actual.sha256 -ne $Sha256.ToLowerInvariant()
    ) {
        throw ($Label + ' identity mismatch at ' + $Path + ': ' + ($actual | ConvertTo-Json -Compress))
    }
}

function Resolve-ProjectLeaf {
    param([Parameter(Mandatory)][string]$RelativePath)
    if ([IO.Path]::IsPathRooted($RelativePath)) {
        throw "Project-relative path must not be rooted: $RelativePath"
    }
    $candidate = [IO.Path]::GetFullPath((Join-Path $laneRoot $RelativePath))
    $rootPrefix = $laneRoot.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
    if (-not $candidate.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes the project root: $RelativePath"
    }
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        throw "Required file is missing: $RelativePath"
    }
    return $candidate
}

function Get-RelativeProjectPath {
    param([Parameter(Mandatory)][string]$Path)
    $candidate = [IO.Path]::GetFullPath($Path)
    $rootPrefix = $laneRoot.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
    if (-not $candidate.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside the project root: $Path"
    }
    return [IO.Path]::GetRelativePath($laneRoot, $candidate).Replace('\', '/')
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

function Invoke-CheckedPython {
    param([Parameter(Mandatory)][string[]]$Arguments)
    & $python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw ('Python command failed with exit code ' + $LASTEXITCODE + ': ' + ($Arguments -join ' '))
    }
}

function Compare-IntegerSequence {
    param(
        [Parameter(Mandatory)][AllowNull()][AllowEmptyCollection()][object[]]$Actual,
        [Parameter(Mandatory)][AllowNull()][AllowEmptyCollection()][int[]]$Expected,
        [Parameter(Mandatory)][string]$Label
    )
    $actualText = (@($Actual | Where-Object { $null -ne $_ } | ForEach-Object { [int]$_ }) -join ',')
    $expectedText = (@($Expected | Where-Object { $null -ne $_ } | ForEach-Object { [int]$_ }) -join ',')
    if ($actualText -ne $expectedText) {
        throw "$Label sequence mismatch: [$actualText] != [$expectedText]"
    }
}

$guardIdentities = [Collections.Generic.Dictionary[string, object]]::new(
    [StringComparer]::OrdinalIgnoreCase
)

function Add-GuardExpected {
    param(
        [Parameter(Mandatory)][string]$RelativePath,
        [Parameter(Mandatory)][long]$Bytes,
        [Parameter(Mandatory)][string]$Sha256,
        [Parameter(Mandatory)][string]$Label
    )
    $normalized = $RelativePath.Replace('\', '/')
    $path = Resolve-ProjectLeaf -RelativePath $normalized
    Assert-Identity -Path $path -Bytes $Bytes -Sha256 $Sha256 -Label $Label
    if ($guardIdentities.ContainsKey($normalized)) {
        $existing = $guardIdentities[$normalized]
        if ([long]$existing.bytes -ne $Bytes -or $existing.sha256 -ne $Sha256.ToLowerInvariant()) {
            throw "Conflicting guarded identities for $normalized"
        }
    }
    else {
        $guardIdentities.Add(
            $normalized,
            [ordered]@{ bytes = $Bytes; sha256 = $Sha256.ToLowerInvariant() }
        )
    }
}

function Add-GuardCurrent {
    param(
        [Parameter(Mandatory)][string]$RelativePath,
        [Parameter(Mandatory)][string]$Label
    )
    $normalized = $RelativePath.Replace('\', '/')
    $path = Resolve-ProjectLeaf -RelativePath $normalized
    $identity = Get-Identity -Path $path
    Add-GuardExpected -RelativePath $normalized -Bytes $identity.bytes -Sha256 $identity.sha256 -Label $Label
    return $identity
}

function Assert-GuardIdentities {
    param([Parameter(Mandatory)][string]$Stage)
    foreach ($relativePath in @($guardIdentities.Keys | Sort-Object)) {
        $expected = $guardIdentities[$relativePath]
        Assert-Identity `
            -Path (Resolve-ProjectLeaf -RelativePath $relativePath) `
            -Bytes $expected.bytes `
            -Sha256 $expected.sha256 `
            -Label "$Stage guarded input"
    }
}

function Assert-RecordedFile {
    param(
        [Parameter(Mandatory)][object]$Row,
        [Parameter(Mandatory)][string]$Label
    )
    if ($null -eq $Row.path -or $null -eq $Row.bytes -or $null -eq $Row.sha256) {
        throw "$Label does not contain path/bytes/sha256"
    }
    $relativePath = [string]$Row.path
    Add-GuardExpected `
        -RelativePath $relativePath `
        -Bytes ([long]$Row.bytes) `
        -Sha256 ([string]$Row.sha256) `
        -Label $Label
    return [ordered]@{
        path = $relativePath.Replace('\', '/')
        bytes = [long]$Row.bytes
        sha256 = ([string]$Row.sha256).ToLowerInvariant()
    }
}

# Fail before any prefix rebuild, generated-file refresh, or receipt write if
# the complete Unit 11--19 live mathematics boundary is not yet admitted.
foreach ($unit in 11..19) {
    $unitText = '{0:D2}' -f $unit
    $postRel = "qa/unit-$unitText/POST_CORRECTION_MATH_QA.json"
    $postPath = Join-Path $laneRoot $postRel
    if (-not (Test-Path -LiteralPath $postPath -PathType Leaf)) {
        throw "Missing required cumulative-build gate: $postRel"
    }
    $postGate = Read-JsonFile -Path $postPath
    if ($postGate.status -ne 'pass' -or $postGate.unit_id -ne "o011-brenner-u$unit") {
        throw "Required cumulative-build gate is not passing for Unit ${unit}: $postRel"
    }
}

# The Unit 10 public boundary freezes the then-current prefix-only media
# configuration. The live configuration now extends through Unit 19, so an
# exact Unit 10 rebuild must use the frozen bytes retained in the published
# Unit 10 source ZIP. The swap is atomic, guarded, recoverable, and restored
# before any Unit 11--19 binding begins. The v10 scripts themselves remain
# byte-for-byte untouched.
$prefixBuildScriptRel = 'scripts/build_through_unit10.ps1'
$prefixVerifyScriptRel = 'scripts/verify_through_unit10_pdf.py'
$prefixWrapperRel = 'build/through-unit-10.tex'
$prefixArchiveRel = 'output/release-unit10/geometri-diferensial-manifold-mulus-brenner-id-unit10-source-20260823.zip'
$prefixArchiveEntry = 'source/unit_media.json'
$prefixFixed = [ordered]@{
    build_script = [ordered]@{ path = $prefixBuildScriptRel; bytes = 25539; sha256 = 'd96c4488494c3ee1ce2b3a4498f582fda4468f20afcb5fe00cb3316bb9279d84' }
    verify_script = [ordered]@{ path = $prefixVerifyScriptRel; bytes = 34642; sha256 = '48dc3cff8b2205b5e8cde9e19bc197644f74320223c41e2661274b14c3ab8e74' }
    wrapper = [ordered]@{ path = $prefixWrapperRel; bytes = 8511; sha256 = 'be9b9fc8adadd331c0949032fb0118e1f0e5fdd9d0dfe7760334c1086112065b' }
    archive = [ordered]@{ path = $prefixArchiveRel; bytes = 1758537; sha256 = '0c160e741e02a711bdbbb984a788459ccb1e4ca94f0809f5add25ec50f8beb3a' }
    media_config_entry = [ordered]@{ path = $prefixArchiveEntry; bytes = 3709; sha256 = '1f5404aad71947dcff064b853f1820b302f5a7e14cbb862631623eeddc2b8cad' }
    pdf = [ordered]@{ path = 'output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-10-id.pdf'; bytes = 5733895; sha256 = '4eaec807347feeab2b3334056d3109d5ce6e5eb30ed3649a507ae6124049856d' }
    build_receipt = [ordered]@{ path = 'qa/unit-10/build.json'; bytes = 20600; sha256 = '4f3146a4889e9be09e17ac5d7a1bb9bfb4a6c609debccd4befb078a1bd33b65d' }
    structural_qa = [ordered]@{ path = 'qa/unit-10/pdf_structural_qa.json'; bytes = 89821; sha256 = '81451a5e7f78f63935e758fa3d277db28b9db252c09c6930fc1cea597c9a47d7' }
}

foreach ($row in @($prefixFixed.build_script, $prefixFixed.verify_script, $prefixFixed.wrapper, $prefixFixed.archive)) {
    Assert-Identity `
        -Path (Resolve-ProjectLeaf -RelativePath $row.path) `
        -Bytes $row.bytes `
        -Sha256 $row.sha256 `
        -Label 'frozen Unit 10 boundary input'
}

foreach ($directory in @($qaDir, $workDir)) {
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
function Read-ZipEntryBytes {
    param(
        [Parameter(Mandatory)][IO.Compression.ZipArchive]$Archive,
        [Parameter(Mandatory)][string]$EntryName
    )
    $matches = @($Archive.Entries | Where-Object { $_.FullName -eq $EntryName })
    if ($matches.Count -ne 1) {
        throw "Expected exactly one $EntryName in $prefixArchiveRel"
    }
    $entryStream = $matches[0].Open()
    try {
        $memory = [IO.MemoryStream]::new()
        try {
            $entryStream.CopyTo($memory)
            return $memory.ToArray()
        }
        finally {
            $memory.Dispose()
        }
    }
    finally {
        $entryStream.Dispose()
    }
}

function Get-ByteArraySha256 {
    param([Parameter(Mandatory)][byte[]]$Bytes)
    $hasher = [Security.Cryptography.SHA256]::Create()
    try {
        return (
            [BitConverter]::ToString($hasher.ComputeHash($Bytes))
        ).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $hasher.Dispose()
    }
}

$archivePath = Resolve-ProjectLeaf -RelativePath $prefixArchiveRel
$archive = [IO.Compression.ZipFile]::OpenRead($archivePath)
try {
    $prefixMediaBytes = Read-ZipEntryBytes -Archive $archive -EntryName $prefixArchiveEntry
    $prefixHistoricalBuildBytes = Read-ZipEntryBytes -Archive $archive -EntryName $prefixFixed.build_receipt.path
    $prefixHistoricalQaBytes = Read-ZipEntryBytes -Archive $archive -EntryName $prefixFixed.structural_qa.path
}
finally {
    $archive.Dispose()
}
$prefixMediaHash = Get-ByteArraySha256 -Bytes $prefixMediaBytes
if (
    $prefixMediaBytes.Length -ne $prefixFixed.media_config_entry.bytes -or
    $prefixMediaHash -ne $prefixFixed.media_config_entry.sha256
) {
    throw 'Frozen Unit 10 media configuration entry identity mismatch'
}
if (
    $prefixHistoricalBuildBytes.Length -ne $prefixFixed.build_receipt.bytes -or
    (Get-ByteArraySha256 -Bytes $prefixHistoricalBuildBytes) -ne $prefixFixed.build_receipt.sha256
) {
    throw 'Frozen Unit 10 build receipt entry identity mismatch'
}
if (
    $prefixHistoricalQaBytes.Length -ne $prefixFixed.structural_qa.bytes -or
    (Get-ByteArraySha256 -Bytes $prefixHistoricalQaBytes) -ne $prefixFixed.structural_qa.sha256
) {
    throw 'Frozen Unit 10 structural QA entry identity mismatch'
}

# Earlier failed prefix experiments may have overwritten these two historical
# receipts even though the public PDF stayed byte-identical. Restore the exact
# published receipt bytes from the frozen source archive before proceeding.
[IO.File]::WriteAllBytes(
    (Resolve-ProjectLeaf -RelativePath $prefixFixed.build_receipt.path),
    $prefixHistoricalBuildBytes
)
[IO.File]::WriteAllBytes(
    (Resolve-ProjectLeaf -RelativePath $prefixFixed.structural_qa.path),
    $prefixHistoricalQaBytes
)

$liveMediaIdentityBefore = Get-Identity -Path $mediaConfigPath

foreach ($row in @($prefixFixed.pdf, $prefixFixed.build_receipt, $prefixFixed.structural_qa)) {
    Assert-Identity `
        -Path (Resolve-ProjectLeaf -RelativePath $row.path) `
        -Bytes $row.bytes `
        -Sha256 $row.sha256 `
        -Label 'preserved exact Unit 10 public-boundary artifact'
}
$prefixQa = Read-JsonFile -Path (Resolve-ProjectLeaf -RelativePath $prefixFixed.structural_qa.path)
if (
    $prefixQa.passed -ne $true -or
    $prefixQa.workflow -ne 'o011-through-unit10-pdf-structural-accessibility-qa-v1'
) {
    throw 'Frozen Unit 10 structural QA is not passing'
}
$liveMediaIdentityAfter = Get-Identity -Path $mediaConfigPath
if (
    $liveMediaIdentityBefore.bytes -ne $liveMediaIdentityAfter.bytes -or
    $liveMediaIdentityBefore.sha256 -ne $liveMediaIdentityAfter.sha256
) {
    throw 'Live Units 1-19 media configuration changed during read-only Unit 10 prefix verification'
}
$prefixTransactionReceipt = [ordered]@{
    schema_version = 1
    workflow = 'o011-unit19-unit10-prefix-preservation-v2'
    public_boundary = $prefixFixed
    archive_evidence = [ordered]@{
        path = $prefixArchiveRel
        media_config_entry = $prefixFixed.media_config_entry
        build_receipt_entry = $prefixFixed.build_receipt
        structural_qa_entry = $prefixFixed.structural_qa
        exact_entries_verified = $true
    }
    live_media_configuration = [ordered]@{
        path = 'source/unit_media.json'
        before = $liveMediaIdentityBefore
        after = $liveMediaIdentityAfter
        untouched_byte_identically = (
            $liveMediaIdentityBefore.bytes -eq $liveMediaIdentityAfter.bytes -and
            $liveMediaIdentityBefore.sha256 -eq $liveMediaIdentityAfter.sha256
        )
    }
    verification = [ordered]@{
        public_pdf_and_historical_receipts_match_frozen_identities = $true
        historical_receipts_restored_from_verified_archive_entries = $true
        legacy_prefix_rebuild_skipped = $true
        reason = 'The append-only live build graph has evolved after Unit 10; rebuilding the old receipt would replace immutable public provenance even though the PDF remains byte-identical.'
    }
}
$prefixTransactionReceiptPath = Join-Path $qaDir 'UNIT10_PREFIX_PRESERVATION_RECEIPT.json'
$utf8NoBom = [Text.UTF8Encoding]::new($false)
[IO.File]::WriteAllBytes(
    $prefixTransactionReceiptPath,
    $utf8NoBom.GetBytes(($prefixTransactionReceipt | ConvertTo-Json -Depth 8) + "`n")
)

# Only after the exact public Unit 10 prefix and frozen archive witnesses pass
# without altering the live media configuration do we bind the changing
# extension. Every target identity comes
# from a passing translation receipt and must agree with the unit's explicit
# passing POST mathematics QA.
foreach ($directory in @($generatedDir, $mediaDir, $outputDir)) {
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
}
$pdfLatex = (Get-Command pdflatex -ErrorAction Stop).Source

$unitSpecs = @(
    [pscustomobject]@{ unit = 11; solutions = [int[]]@(10, 14); exercise_count = 39; media = [string[]]@('Toroidal coord.png') },
    [pscustomobject]@{ unit = 12; solutions = [int[]]@(11, 12); exercise_count = 29; media = [string[]]@('Fiddler crab mobius strip.gif', 'Inclusion-exclusion.svg') },
    [pscustomobject]@{ unit = 13; solutions = [int[]]@(1, 10, 11, 16, 18, 19, 21, 22); exercise_count = 24; media = [string[]]@('Möbius strip.jpg') },
    [pscustomobject]@{ unit = 14; solutions = [int[]]@(5, 6, 9, 11, 12, 13, 14); exercise_count = 18; media = [string[]]@() },
    [pscustomobject]@{ unit = 15; solutions = [int[]]@(1, 11, 12, 13); exercise_count = 16; media = [string[]]@() },
    [pscustomobject]@{ unit = 16; solutions = [int[]]@(1, 12); exercise_count = 21; media = [string[]]@('Georg Friedrich Bernhard Riemann.jpeg', 'Sphere with three handles.png') },
    [pscustomobject]@{ unit = 17; solutions = [int[]]@(2, 4); exercise_count = 19; media = [string[]]@('Cilinderprojectie-constructie.jpg') },
    [pscustomobject]@{ unit = 18; solutions = [int[]]@(8, 11, 13, 14); exercise_count = 21; media = [string[]]@('Poincarehalfplaneconform.gif', 'Hyperboloid2.png') },
    [pscustomobject]@{ unit = 19; solutions = [int[]]@(); exercise_count = 12; media = [string[]]@() }
)
$unitBindings = @()
$preparationBindings = @()

foreach ($spec in $unitSpecs) {
    $unit = [int]$spec.unit
    $unitText = '{0:D2}' -f $unit
    $postRel = "qa/unit-$unitText/POST_CORRECTION_MATH_QA.json"
    $postPath = Resolve-ProjectLeaf -RelativePath $postRel
    $post = Read-JsonFile -Path $postPath
    if ($post.status -ne 'pass' -or $post.unit_id -ne "o011-brenner-u$unit") {
        throw "Unit $unit POST mathematics QA is absent, stale, or not passing"
    }
    $postIdentity = Add-GuardCurrent -RelativePath $postRel -Label "Unit $unit POST mathematics QA"

    if ([int]$post.source_closure.exercise_count -ne [int]$spec.exercise_count) {
        throw "Unit $unit POST QA exercise count mismatch"
    }
    $postSolutionIndices = if ($null -ne $post.source_closure.supplied_solution_indices) {
        @($post.source_closure.supplied_solution_indices)
    }
    elseif ($null -ne $post.authority.supplied_solution_indices) {
        @($post.authority.supplied_solution_indices)
    }
    else {
        @()
    }
    Compare-IntegerSequence `
        -Actual $postSolutionIndices `
        -Expected $spec.solutions `
        -Label "Unit $unit POST QA supplied solutions"

    $closureRel = "qa/unit-$unitText/solution_closure.json"
    $closurePath = Resolve-ProjectLeaf -RelativePath $closureRel
    $closure = Read-JsonFile -Path $closurePath
    if ([int]$closure.exercise_count -ne [int]$spec.exercise_count) {
        throw "Unit $unit frozen solution closure exercise count mismatch"
    }
    Compare-IntegerSequence `
        -Actual @($closure.supplied_solution_indices) `
        -Expected $spec.solutions `
        -Label "Unit $unit frozen supplied solutions"
    $closureIdentity = Add-GuardCurrent -RelativePath $closureRel -Label "Unit $unit solution closure"

    $arrayTargetSchema = $post.targets -is [System.Array]
    if ($arrayTargetSchema) {
        $lecturePostTargets = @($post.targets | Where-Object { $_.path -eq "source/units/unit-$unitText/lecture${unitText}.id.tex" })
        $worksheetPostTargets = @($post.targets | Where-Object { $_.path -eq "source/units/unit-$unitText/worksheet${unitText}.id.tex" })
    }
    else {
        $lecturePostTargets = @($post.targets.lecture)
        $worksheetPostTargets = @($post.targets.worksheet)
    }
    if ($lecturePostTargets.Count -ne 1 -or $worksheetPostTargets.Count -ne 1) {
        throw "Unit $unit POST QA does not bind one lecture and one worksheet target"
    }

    $expectedTranslations = @(
        [pscustomobject]@{
            role = 'lecture'; exercise = $null
            source = "authority/expanded/lecture${unitText}_source.de.tex"
            target = "source/units/unit-$unitText/lecture${unitText}.id.tex"
            receipt = "qa/unit-$unitText/lecture${unitText}_translation.json"
            output = "build/generated/lecture${unitText}.id.build.tex"
            preparation = "qa/unit-$unitText/lecture${unitText}_prepare.json"
            post_target = $lecturePostTargets[0]
            post_authority = $post.authority.lecture
        },
        [pscustomobject]@{
            role = 'worksheet'; exercise = $null
            source = "authority/expanded/worksheet${unitText}_source.de.tex"
            target = "source/units/unit-$unitText/worksheet${unitText}.id.tex"
            receipt = "qa/unit-$unitText/worksheet${unitText}_translation.json"
            output = "build/generated/worksheet${unitText}.id.build.tex"
            preparation = "qa/unit-$unitText/worksheet${unitText}_prepare.json"
            post_target = $worksheetPostTargets[0]
            post_authority = $post.authority.worksheet
        }
    )

    if ($arrayTargetSchema) {
        $postSolutionRows = @($post.targets | Where-Object { $null -ne $_.exercise })
        $postAuthoritySolutionRows = @()
        foreach ($exercise in $spec.solutions) {
            $closureMatches = @(
                $closure.exercises |
                    Where-Object { [int]$_.exercise_index -eq $exercise -and $_.exists -eq $true }
            )
            if ($closureMatches.Count -ne 1 -or $null -eq $closureMatches[0].expanded_latex.sanitized_source) {
                throw "Unit $unit solution $exercise lacks one frozen sanitized authority in solution_closure.json"
            }
            $sanitizedSource = $closureMatches[0].expanded_latex.sanitized_source
            $postAuthoritySolutionRows += [pscustomobject]@{
                exercise = $exercise
                path = $sanitizedSource.path
                bytes = [long]$sanitizedSource.bytes
                sha256 = $sanitizedSource.sha256
            }
        }
    }
    else {
        $postSolutionRows = @($post.targets.supplied_solutions)
        $postAuthoritySolutionRows = @($post.authority.supplied_solutions)
    }
    Compare-IntegerSequence `
        -Actual @($postSolutionRows | ForEach-Object { $_.exercise }) `
        -Expected $spec.solutions `
        -Label "Unit $unit POST target solution rows"
    Compare-IntegerSequence `
        -Actual @($postAuthoritySolutionRows | ForEach-Object { $_.exercise }) `
        -Expected $spec.solutions `
        -Label "Unit $unit POST authority solution rows"

    foreach ($exercise in $spec.solutions) {
        $postTargetMatches = @($postSolutionRows | Where-Object { [int]$_.exercise -eq $exercise })
        $postAuthorityMatches = @($postAuthoritySolutionRows | Where-Object { [int]$_.exercise -eq $exercise })
        if ($postTargetMatches.Count -ne 1 -or $postAuthorityMatches.Count -ne 1) {
            throw "Unit $unit solution $exercise is not uniquely represented in POST QA"
        }
        $exerciseText = '{0:D2}' -f $exercise
        $expectedTranslations += [pscustomobject]@{
            role = 'solution'; exercise = $exercise
            source = "authority/expanded/worksheet${unitText}_exercise${exerciseText}_solution_source.de.tex"
            target = "source/units/unit-$unitText/worksheet${unitText}_exercise${exerciseText}_solution.id.tex"
            receipt = "qa/unit-$unitText/worksheet${unitText}_exercise${exerciseText}_solution_translation.json"
            output = "build/generated/worksheet${unitText}_exercise${exerciseText}_solution.id.build.tex"
            preparation = "qa/unit-$unitText/worksheet${unitText}_exercise${exerciseText}_solution_prepare.json"
            post_target = $postTargetMatches[0]
            post_authority = $postAuthorityMatches[0]
        }
    }

    $translationRows = @()
    foreach ($item in $expectedTranslations) {
        $receiptPath = Resolve-ProjectLeaf -RelativePath $item.receipt
        $translation = Read-JsonFile -Path $receiptPath
        if (
            $translation.status -ne 'pass' -or
            @($translation.failures).Count -ne 0 -or
            $translation.source -ne $item.source -or
            $translation.target -ne $item.target
        ) {
            throw "Passing translation receipt closure failed: $($item.receipt)"
        }
        $sourcePath = Resolve-ProjectLeaf -RelativePath $item.source
        $targetPath = Resolve-ProjectLeaf -RelativePath $item.target
        Assert-Identity `
            -Path $sourcePath `
            -Bytes ([long]$translation.source_bytes) `
            -Sha256 ([string]$translation.source_sha256) `
            -Label "Unit $unit translation authority"
        Assert-Identity `
            -Path $targetPath `
            -Bytes ([long]$translation.target_bytes) `
            -Sha256 ([string]$translation.target_sha256) `
            -Label "Unit $unit translated target"
        if (
            $item.post_target.path -ne $item.target -or
            [long]$item.post_target.bytes -ne [long]$translation.target_bytes -or
            $item.post_target.sha256 -ne $translation.target_sha256 -or
            $item.post_authority.path -ne $item.source -or
            [long]$item.post_authority.bytes -ne [long]$translation.source_bytes -or
            $item.post_authority.sha256 -ne $translation.source_sha256
        ) {
            throw "Unit $unit translation receipt does not agree with passing POST QA: $($item.target)"
        }
        $translationReceiptIdentity = Get-Identity -Path $receiptPath
        $declaredReceiptPath = [string]$item.post_target.translation_receipt
        if (
            ($declaredReceiptPath.Length -gt 0 -and $declaredReceiptPath -ne $item.receipt) -or
            $item.post_target.translation_receipt_sha256 -ne $translationReceiptIdentity.sha256 -or
            (
                $null -ne $item.post_target.translation_receipt_bytes -and
                [long]$item.post_target.translation_receipt_bytes -ne [long]$translationReceiptIdentity.bytes
            )
        ) {
            throw "Unit $unit POST QA translation-receipt binding mismatch: $($item.receipt)"
        }

        Add-GuardExpected -RelativePath $item.source -Bytes $translation.source_bytes -Sha256 $translation.source_sha256 -Label "Unit $unit live authority"
        Add-GuardExpected -RelativePath $item.target -Bytes $translation.target_bytes -Sha256 $translation.target_sha256 -Label "Unit $unit live target"
        Add-GuardExpected -RelativePath $item.receipt -Bytes $translationReceiptIdentity.bytes -Sha256 $translationReceiptIdentity.sha256 -Label "Unit $unit passing translation receipt"

        Invoke-CheckedPython @(
            (Join-Path $laneRoot 'scripts\prepare_unit_tex.py'),
            $targetPath,
            (Join-Path $laneRoot $item.output),
            '--project-root', $laneRoot,
            '--receipt', (Join-Path $laneRoot $item.preparation)
        ) | Out-Null
        $preparation = Read-JsonFile -Path (Resolve-ProjectLeaf -RelativePath $item.preparation)
        if (
            $preparation.input -ne $item.target -or
            [long]$preparation.input_bytes -ne [long]$translation.target_bytes -or
            $preparation.input_sha256 -ne $translation.target_sha256 -or
            $preparation.output -ne $item.output
        ) {
            throw "Unit $unit preparation receipt input/output binding mismatch: $($item.preparation)"
        }
        Assert-Identity `
            -Path (Resolve-ProjectLeaf -RelativePath $item.output) `
            -Bytes ([long]$preparation.output_bytes) `
            -Sha256 ([string]$preparation.output_sha256) `
            -Label "Unit $unit prepared fragment"
        $postPreparedMatches = @($post.prepared_fragments | Where-Object { $_.path -eq $item.output })
        if (
            $postPreparedMatches.Count -ne 1 -or
            [long]$postPreparedMatches[0].bytes -ne [long]$preparation.output_bytes -or
            $postPreparedMatches[0].sha256 -ne $preparation.output_sha256
        ) {
            throw "Unit $unit prepared fragment does not agree with passing POST QA: $($item.output)"
        }
        $preparationIdentity = Add-GuardCurrent -RelativePath $item.preparation -Label "Unit $unit preparation receipt"
        Add-GuardExpected -RelativePath $item.output -Bytes $preparation.output_bytes -Sha256 $preparation.output_sha256 -Label "Unit $unit prepared output"

        $translationRows += [ordered]@{
            role = $item.role
            exercise = $item.exercise
            authority = [ordered]@{ path = $item.source; bytes = [long]$translation.source_bytes; sha256 = $translation.source_sha256 }
            target = [ordered]@{ path = $item.target; bytes = [long]$translation.target_bytes; sha256 = $translation.target_sha256 }
            translation_receipt = [ordered]@{ path = $item.receipt; bytes = $translationReceiptIdentity.bytes; sha256 = $translationReceiptIdentity.sha256; status = 'pass' }
            prepared = [ordered]@{ path = $item.output; bytes = [long]$preparation.output_bytes; sha256 = $preparation.output_sha256 }
            preparation_receipt = [ordered]@{ path = $item.preparation; bytes = $preparationIdentity.bytes; sha256 = $preparationIdentity.sha256 }
        }
        $preparationBindings += [ordered]@{
            unit = $unit
            role = $item.role
            exercise = $item.exercise
            path = $item.preparation
            rendered_interactive_gif_links = @($preparation.rendered_interactive_gif_links)
        }
    }

    $declaredCorrectionManifests = @()
    if ($null -ne $post.PSObject.Properties['correction_manifests']) {
        $declaredCorrectionManifests = @($post.correction_manifests)
    }
    if ($unit -eq 14) {
        # Unit 14 predates the correction_manifests field in the per-unit POST
        # schema. Bind its exact retained manifests here without rewriting the
        # already-closed Unit 14 receipt, including the disclosed late prose
        # refinement closure for O011-TRANS-0168.
        $declaredCorrectionManifests = @(
            [pscustomobject]@{ path = 'qa/unit-14/LECTURE14_PROTECTED_CORRECTIONS.json'; bytes = 5833; sha256 = '05b2bcc4cc1389384fa1cafe946814cff1321499bbac01a6a53b3366a78ee9ec' },
            [pscustomobject]@{ path = 'qa/unit-14/WORKSHEET14_PROTECTED_CORRECTIONS.json'; bytes = 3302; sha256 = 'dd01551c857b761d99c628280884bda00a7e54337e2260af8469a49846eae526' },
            [pscustomobject]@{ path = 'qa/unit-14/SOLUTION14_05_PROTECTED_CORRECTIONS.json'; bytes = 702; sha256 = 'd2c633467c4e97f52fb839745d9c58beca2d311fb0b8152be33945539df4921b' },
            [pscustomobject]@{ path = 'qa/unit-14/SOLUTION14_06_PROTECTED_CORRECTIONS.json'; bytes = 675; sha256 = '7e3054aaaf9e684125e85626b40f4c3f6d9ae4f587da83519df141bf24cf39e4' },
            [pscustomobject]@{ path = 'qa/unit-14/SOLUTION14_09_PROTECTED_CORRECTIONS.json'; bytes = 959; sha256 = 'a67548e28c40b6064a81551c821fe9725482391b8d4c84db327d01b6512f2a1d' },
            [pscustomobject]@{ path = 'qa/unit-14/SOLUTION14_12_PROTECTED_CORRECTIONS.json'; bytes = 690; sha256 = 'da43908ef20230231fbb9ff8f0b6774348be5dcd30d510cf18ae7c402b1323e5' },
            [pscustomobject]@{ path = 'qa/unit-14/UNIT14_POST_REVIEW_CORRECTION_CLOSURE.json'; bytes = 2409; sha256 = '03b3b5674cb806244b6af17f2a5dcaa507c08751be0569a67bd7b95a87b65a08' },
            [pscustomobject]@{ path = 'qa/unit-14/UNIT14_INTERNAL_ENVIRONMENT_CORRECTION.json'; bytes = 1255; sha256 = '3416e7b9811f63dd4ee7c06c6776df0afa08dfaaea6c6f16fca9cdbdb63e18d2' }
        )
    }
    elseif ($unit -eq 15) {
        # O011-CORR-0180 is a source-language grammar defect translated to its
        # unambiguous intended meaning, so it has evidence closure rather than
        # a protected-math delta row.
        $declaredCorrectionManifests += [pscustomobject]@{
            path = 'qa/unit-15/UNIT15_COUNTABLE_ATLAS_CORRECTION_CLOSURE.json'
            bytes = 1330
            sha256 = '448d60c3d35ef8b29b37d5f6623300b14303de56027fb0e9edeb3a8252dbee7c'
        }
        $declaredCorrectionManifests += [pscustomobject]@{
            path = 'qa/unit-15/UNIT15_INTERNAL_ENVIRONMENT_CORRECTION.json'
            bytes = 1258
            sha256 = '29161dda0b39947b848814b1ef7784ceaa56461f15ff38f7dcfb918dd1b975b9'
        }
    }

    $correctionRows = @()
    foreach ($row in $declaredCorrectionManifests) {
        $correctionRows += Assert-RecordedFile -Row $row -Label "Unit $unit protected correction manifest"
    }
    $unitBindings += [ordered]@{
        unit = $unit
        post_qa = [ordered]@{ path = $postRel; bytes = $postIdentity.bytes; sha256 = $postIdentity.sha256; status = 'pass' }
        solution_closure = [ordered]@{ path = $closureRel; bytes = $closureIdentity.bytes; sha256 = $closureIdentity.sha256 }
        exercise_count = [int]$spec.exercise_count
        supplied_solution_numbers = [int[]]$spec.solutions
        translations = @($translationRows)
        correction_manifests = @($correctionRows)
    }
}

# Rebuild the exact Unit 11--19 static-media receipts against the live Unit 19
# configuration in a milestone-local namespace. Earlier per-unit receipts are
# immutable published evidence and must not be rewritten merely because the
# cumulative media configuration gained later-unit entries. The Unit 12 GIF
# derivative is frame zero by construction in prepare_unit_media.py and is
# rechecked below against its passing historical animation QA.
$mediaBindings = @()
foreach ($spec in $unitSpecs) {
    $unit = [int]$spec.unit
    $unitText = '{0:D2}' -f $unit
    $receiptRel = "qa/unit-19/cumulative-media/unit-${unitText}_media.json"
    Invoke-CheckedPython @(
        (Join-Path $laneRoot 'scripts\prepare_unit_media.py'),
        '--manifest', (Join-Path $laneRoot 'authority\brenner_media_rights_manifest.csv'),
        '--project-root', $laneRoot,
        '--source-dir', (Join-Path $laneRoot 'authority\media'),
        '--output-dir', $mediaDir,
        '--media-config', $mediaConfigPath,
        '--unit-number', $unit.ToString(),
        '--heading-level', 'section',
        '--attribution-tex', (Join-Path $generatedDir ("unit${unitText}-media-attribution-cumulative.tex")),
        '--receipt', (Join-Path $laneRoot $receiptRel)
    ) | Out-Null
    $mediaReceipt = Read-JsonFile -Path (Resolve-ProjectLeaf -RelativePath $receiptRel)
    if (
        [int]$mediaReceipt.unit_number -ne $unit -or
        $mediaReceipt.heading_level -ne 'section' -or
        $mediaReceipt.media_config -ne 'source/unit_media.json'
    ) {
        throw "Unit $unit media receipt boundary mismatch"
    }
    $liveConfigIdentity = Get-Identity -Path $mediaConfigPath
    if ($mediaReceipt.media_config_sha256 -ne $liveConfigIdentity.sha256) {
        throw "Unit $unit media receipt is not bound to the live Unit 19 config"
    }
    $actualNames = @($mediaReceipt.media | ForEach-Object { [string]$_.filename })
    if (($actualNames -join '|') -ne (@($spec.media) -join '|')) {
        throw "Unit $unit media filename closure mismatch: $($actualNames -join ', ')"
    }
    $assetRows = @()
    foreach ($row in @($mediaReceipt.media)) {
        Assert-Identity `
            -Path (Resolve-ProjectLeaf -RelativePath $row.canonical_path) `
            -Bytes ([long]$row.canonical_bytes) `
            -Sha256 ([string]$row.canonical_sha256) `
            -Label "Unit $unit canonical media"
        Add-GuardExpected -RelativePath $row.canonical_path -Bytes $row.canonical_bytes -Sha256 $row.canonical_sha256 -Label "Unit $unit canonical media"
        $derivativeBinding = $null
        if ($null -ne $row.derivative) {
            Assert-Identity `
                -Path (Resolve-ProjectLeaf -RelativePath $row.derivative.path) `
                -Bytes ([long]$row.derivative.bytes) `
                -Sha256 ([string]$row.derivative.sha256) `
                -Label "Unit $unit print derivative"
            Add-GuardExpected -RelativePath $row.derivative.path -Bytes $row.derivative.bytes -Sha256 $row.derivative.sha256 -Label "Unit $unit print derivative"
            $derivativeBinding = [ordered]@{
                path = $row.derivative.path
                bytes = [long]$row.derivative.bytes
                sha256 = $row.derivative.sha256
                source_kind = $row.derivative.source_kind
                frame_index = $row.derivative.frame_index
            }
        }
        $assetRows += [ordered]@{
            filename = $row.filename
            canonical = [ordered]@{ path = $row.canonical_path; bytes = [long]$row.canonical_bytes; sha256 = $row.canonical_sha256 }
            derivative = $derivativeBinding
        }
    }
    $attribution = Assert-RecordedFile -Row $mediaReceipt.attribution_tex -Label "Unit $unit media attribution fragment"
    $receiptIdentity = Add-GuardCurrent -RelativePath $receiptRel -Label "Unit $unit media receipt"
    $mediaBindings += [ordered]@{
        unit = $unit
        receipt = [ordered]@{ path = $receiptRel; bytes = $receiptIdentity.bytes; sha256 = $receiptIdentity.sha256 }
        source_count = [int]$mediaReceipt.source_count
        derivative_count = [int]$mediaReceipt.derivative_count
        attribution = $attribution
        assets = @($assetRows)
    }
}

$interactiveManifestRel = 'source/unit11_interactive_media.json'
$interactiveQaRel = 'qa/unit-11/INTERACTIVE_MEDIA_QA.json'
$interactiveManifest = Read-JsonFile -Path (Resolve-ProjectLeaf -RelativePath $interactiveManifestRel)
$interactiveQa = Read-JsonFile -Path (Resolve-ProjectLeaf -RelativePath $interactiveQaRel)
if ($interactiveQa.status -ne 'pass' -or @($interactiveQa.assets).Count -ne 1 -or @($interactiveManifest.assets).Count -ne 1) {
    throw 'Unit 11 interactive-media receipt is not passing or is not a one-asset closure'
}
$interactiveAsset = $interactiveManifest.assets[0]
$interactiveQaAsset = $interactiveQa.assets[0]
if (
    $interactiveAsset.filename -ne 'Aufgabe79.27.gif' -or
    $interactiveQaAsset.filename -ne 'Aufgabe79.27.gif' -or
    [long]$interactiveAsset.bytes -ne [long]$interactiveQaAsset.bytes -or
    $interactiveAsset.sha256 -ne $interactiveQaAsset.sha256
) {
    throw 'Unit 11 interactive GIF authority/QA binding mismatch'
}
$interactiveCanonicalRel = 'authority/media/Aufgabe79.27.gif'
Add-GuardExpected -RelativePath $interactiveCanonicalRel -Bytes $interactiveAsset.bytes -Sha256 $interactiveAsset.sha256 -Label 'Unit 11 interactive GIF'
$interactiveManifestIdentity = Add-GuardCurrent -RelativePath $interactiveManifestRel -Label 'Unit 11 interactive-media manifest'
$interactiveQaIdentity = Add-GuardCurrent -RelativePath $interactiveQaRel -Label 'Unit 11 interactive-media QA'
$solution10Preparation = @($preparationBindings | Where-Object { $_.unit -eq 11 -and $_.role -eq 'solution' -and $_.exercise -eq 10 })
if (
    $solution10Preparation.Count -ne 1 -or
    @($solution10Preparation[0].rendered_interactive_gif_links).Count -ne 1 -or
    $solution10Preparation[0].rendered_interactive_gif_links[0].filename -ne 'Aufgabe79.27.gif'
) {
    throw 'Unit 11 prepared Solution 10 does not retain the exact interactive GIF link'
}
$interactiveBinding = [ordered]@{
    manifest = [ordered]@{ path = $interactiveManifestRel; bytes = $interactiveManifestIdentity.bytes; sha256 = $interactiveManifestIdentity.sha256 }
    qa = [ordered]@{ path = $interactiveQaRel; bytes = $interactiveQaIdentity.bytes; sha256 = $interactiveQaIdentity.sha256; status = 'pass' }
    asset = [ordered]@{ path = $interactiveCanonicalRel; bytes = [long]$interactiveAsset.bytes; sha256 = $interactiveAsset.sha256 }
    prepared_link_count = 1
}

$animatedQaRel = 'qa/unit-12/ANIMATED_MEDIA_QA.json'
$animatedQa = Read-JsonFile -Path (Resolve-ProjectLeaf -RelativePath $animatedQaRel)
if ($animatedQa.status -ne 'pass') {
    throw 'Unit 12 animated-media QA is not passing'
}
$gifMediaBinding = @(
    $mediaBindings |
        Where-Object { $_.unit -eq 12 } |
        ForEach-Object { $_.assets } |
        Where-Object { $_.filename -eq 'Fiddler crab mobius strip.gif' }
)
if ($gifMediaBinding.Count -ne 1 -or $null -eq $gifMediaBinding[0].derivative) {
    throw 'Unit 12 GIF is missing its static PDF derivative binding'
}
$gifDerivative = $gifMediaBinding[0].derivative
if (
    $gifDerivative.path -ne 'build/generated/media/Fiddler_crab_mobius_strip.png' -or
    $gifDerivative.source_kind -ne 'gif' -or
    [int]$gifDerivative.frame_index -ne 0 -or
    $animatedQa.static_pdf_fallback.path -ne $gifDerivative.path -or
    [long]$animatedQa.static_pdf_fallback.bytes -ne [long]$gifDerivative.bytes -or
    $animatedQa.static_pdf_fallback.sha256 -ne $gifDerivative.sha256 -or
    [int]$animatedQa.static_pdf_fallback.frame_index -ne 0
) {
    throw 'Unit 12 GIF frame-zero PDF fallback does not agree with passing animation QA'
}
$historicalUnit12MediaReceipt = Assert-RecordedFile `
    -Row $animatedQa.bindings.media_receipt `
    -Label 'Unit 12 historical animated-media receipt'
$animatedQaIdentity = Add-GuardCurrent -RelativePath $animatedQaRel -Label 'Unit 12 animated-media QA'
$animatedBinding = [ordered]@{
    qa = [ordered]@{ path = $animatedQaRel; bytes = $animatedQaIdentity.bytes; sha256 = $animatedQaIdentity.sha256; status = 'pass' }
    historical_media_receipt = $historicalUnit12MediaReceipt
    canonical_animation = $gifMediaBinding[0].canonical
    static_pdf_fallback = $gifDerivative
}

# Create only the exact MediaWiki loader aliases needed beyond the already
# rebuilt Unit 10 prefix. The Unit 10 JPEG alias remains transient; the static
# PNG aliases are generated build artifacts and are hash-receipted.
$persistentAliases = @(
    [ordered]@{
        source = 'authority/media/Toroidal coord.png'
        target = 'build/generated/media/Toroidal_coord.png'
        role = 'Unit 11 MediaWiki underscore-normalized PNG loader alias'
    },
    [ordered]@{
        source = 'authority/media/Sphere with three handles.png'
        target = 'build/generated/media/Sphere_with_three_handles.png'
        role = 'Unit 16 MediaWiki underscore-normalized PNG loader alias'
    },
    [ordered]@{
        source = 'authority/media/Hyperboloid2.png'
        target = 'build/generated/media/Hyperboloid2.png'
        role = 'Unit 18 MediaWiki static PNG loader alias'
    }
)
$aliasRows = @()
foreach ($alias in $persistentAliases) {
    $sourcePath = Resolve-ProjectLeaf -RelativePath $alias.source
    $targetPath = Join-Path $laneRoot $alias.target
    Copy-Item -LiteralPath $sourcePath -Destination $targetPath -Force
    $sourceIdentity = Get-Identity -Path $sourcePath
    Assert-Identity -Path $targetPath -Bytes $sourceIdentity.bytes -Sha256 $sourceIdentity.sha256 -Label 'persistent media alias'
    Add-GuardExpected -RelativePath $alias.target -Bytes $sourceIdentity.bytes -Sha256 $sourceIdentity.sha256 -Label 'persistent media alias'
    $aliasRows += [ordered]@{
        source = $alias.source
        target = $alias.target
        role = $alias.role
        transient = $false
        bytes = $sourceIdentity.bytes
        sha256 = $sourceIdentity.sha256
    }
}

$temporaryJpegSourceRel = 'authority/media/Torus vectors oblique.jpg'
$temporaryJpegAliasRel = 'authority/media/Torus_vectors_oblique.jpg'
$temporaryJpegSource = Resolve-ProjectLeaf -RelativePath $temporaryJpegSourceRel
$temporaryJpegAlias = Join-Path $laneRoot $temporaryJpegAliasRel
$temporaryJpegIdentity = Get-Identity -Path $temporaryJpegSource
if (Test-Path -LiteralPath $temporaryJpegAlias -PathType Leaf) {
    Assert-Identity -Path $temporaryJpegAlias -Bytes $temporaryJpegIdentity.bytes -Sha256 $temporaryJpegIdentity.sha256 -Label 'pre-existing transient Unit 10 JPEG alias'
    Remove-Item -LiteralPath $temporaryJpegAlias -Force
}
Copy-Item -LiteralPath $temporaryJpegSource -Destination $temporaryJpegAlias
$aliasRows += [ordered]@{
    source = $temporaryJpegSourceRel
    target = $temporaryJpegAliasRel
    role = 'transient Unit 10 MediaWiki underscore-normalized JPEG loader alias'
    transient = $true
    bytes = $temporaryJpegIdentity.bytes
    sha256 = $temporaryJpegIdentity.sha256
}
$temporaryRiemannSourceRel = 'authority/media/Georg Friedrich Bernhard Riemann.jpeg'
$temporaryRiemannAliasRel = 'authority/media/Georg_Friedrich_Bernhard_Riemann.jpg'
$temporaryRiemannSource = Resolve-ProjectLeaf -RelativePath $temporaryRiemannSourceRel
$temporaryRiemannAlias = Join-Path $laneRoot $temporaryRiemannAliasRel
$temporaryRiemannIdentity = Get-Identity -Path $temporaryRiemannSource
if (Test-Path -LiteralPath $temporaryRiemannAlias -PathType Leaf) {
    Assert-Identity -Path $temporaryRiemannAlias -Bytes $temporaryRiemannIdentity.bytes -Sha256 $temporaryRiemannIdentity.sha256 -Label 'pre-existing transient Unit 16 JPEG loader alias'
    Remove-Item -LiteralPath $temporaryRiemannAlias -Force
}
Copy-Item -LiteralPath $temporaryRiemannSource -Destination $temporaryRiemannAlias
$aliasRows += [ordered]@{
    source = $temporaryRiemannSourceRel
    target = $temporaryRiemannAliasRel
    role = 'transient Unit 16 MediaWiki underscore-normalized JPEG loader alias'
    transient = $true
    bytes = $temporaryRiemannIdentity.bytes
    sha256 = $temporaryRiemannIdentity.sha256
}
$aliasReceipt = [ordered]@{
    schema_version = 1
    workflow = 'o011-unit19-cumulative-media-aliases-v1'
    aliases = @($aliasRows)
    transient_alias_removed_after_pipeline = $true
}
$aliasReceiptPath = Join-Path $qaDir 'MEDIA_ALIAS_RECEIPT.json'
[IO.File]::WriteAllBytes(
    $aliasReceiptPath,
    $utf8NoBom.GetBytes(($aliasReceipt | ConvertTo-Json -Depth 6) + "`n")
)

# Derive the Unit 19 reader driver from the exact frozen Unit 10 wrapper. This
# keeps the public v10 wrapper immutable while preserving its centered A4/22mm
# geometry and compatibility surface.
$wrapperPath = Resolve-ProjectLeaf -RelativePath $prefixWrapperRel
$driverRel = 'build/generated/through-unit-19-driver.tex'
$driverPath = Join-Path $laneRoot $driverRel
$wrapperText = [IO.File]::ReadAllText($wrapperPath, [Text.Encoding]::UTF8).Replace("`r`n", "`n").Replace("`r", "`n")
$compatMarker = '\input{brenner-compat.tex}'
if (($wrapperText.Split($compatMarker).Count - 1) -ne 1) {
    throw 'Unit 10 wrapper must contain exactly one compatibility-layer input'
}
$environmentAliases = @'
\newtheorem{Proposisi}[fakt]{Proposisi}
\newtheorem{Lema}[fakt]{Lema}
% Keep each source image and caption together when it fits as a single block.
\renewcommand{\bild}[1]{%
\par\vspace{4mm}%
\noindent\begin{minipage}{\linewidth}#1\end{minipage}%
\par}
% Keep source filenames with underscores safe in the persisted list of figures.
\renewcommand{\bildlizenz}[6]{%
\ifthenelse{\equal{#2}{}}%
{\addcontentsline{lof}{figure}{Sumber = \protect\nolinkurl{#1}, Kreator = Pengguna #3 di #4, Lisensi = #5 \bildlizenzskip}}%
{\ifthenelse{\equal{#3}{}}%
{\addcontentsline{lof}{figure}{Sumber = \protect\nolinkurl{#1}, Kreator = #2, Lisensi = #5 \bildlizenzskip}}%
{\addcontentsline{lof}{figure}{Sumber = \protect\nolinkurl{#1}, Kreator = #2 (diunggah oleh Pengguna #3 di #4), Lisensi = #5 \bildlizenzskip}}}}
'@
$driverText = $wrapperText.Replace($compatMarker, $compatMarker + "`n" + $environmentAliases.TrimEnd())

foreach ($replacement in @(
    @('Pembaca kumulatif hingga Unit 10', 'Pembaca kumulatif hingga Unit 19'),
    @('Kuliah 1--10 dan Lembar Kerja 1--10', 'Kuliah 1--19 dan Lembar Kerja 1--19')
)) {
    if (($driverText.Split($replacement[0]).Count - 1) -ne 1) {
        throw "Unit 10 wrapper text marker is not unique: $($replacement[0])"
    }
    $driverText = $driverText.Replace($replacement[0], $replacement[1])
}

$unitExtension = @'

\part{Unit 11}
\chapter[Kuliah 11]{Kuliah 11: Produk Manifold}
\input{generated/lecture11.id.build.tex}

\chapter{Lembar Kerja 11}
\input{generated/worksheet11.id.build.tex}

\section*{Solusi yang disediakan oleh sumber}
\addcontentsline{toc}{section}{Solusi yang disediakan oleh sumber}
\subsection*{Solusi Soal 11.10}
\input{generated/worksheet11_exercise10_solution.id.build.tex}
\subsection*{Solusi Soal 11.14}
\input{generated/worksheet11_exercise14_solution.id.build.tex}

\part{Unit 12}
\chapter[Kuliah 12]{Kuliah 12: Bundel Vektor}
\input{generated/lecture12.id.build.tex}

\chapter{Lembar Kerja 12}
\input{generated/worksheet12.id.build.tex}

\section*{Solusi yang disediakan oleh sumber}
\addcontentsline{toc}{section}{Solusi yang disediakan oleh sumber}
\subsection*{Solusi Soal 12.11}
\input{generated/worksheet12_exercise11_solution.id.build.tex}
\subsection*{Solusi Soal 12.12}
\input{generated/worksheet12_exercise12_solution.id.build.tex}

\part{Unit 13}
\chapter[Kuliah 13]{Kuliah 13: Konstruksi Bundel Vektor}
\input{generated/lecture13.id.build.tex}

\chapter{Lembar Kerja 13}
\input{generated/worksheet13.id.build.tex}

\section*{Solusi yang disediakan oleh sumber}
\addcontentsline{toc}{section}{Solusi yang disediakan oleh sumber}
\subsection*{Solusi Soal 13.1}
\input{generated/worksheet13_exercise01_solution.id.build.tex}
\subsection*{Solusi Soal 13.10}
\input{generated/worksheet13_exercise10_solution.id.build.tex}
\subsection*{Solusi Soal 13.11}
\input{generated/worksheet13_exercise11_solution.id.build.tex}
\subsection*{Solusi Soal 13.16}
\input{generated/worksheet13_exercise16_solution.id.build.tex}
\subsection*{Solusi Soal 13.18}
\input{generated/worksheet13_exercise18_solution.id.build.tex}
\subsection*{Solusi Soal 13.19}
\input{generated/worksheet13_exercise19_solution.id.build.tex}
\subsection*{Solusi Soal 13.21}
\input{generated/worksheet13_exercise21_solution.id.build.tex}
\subsection*{Solusi Soal 13.22}
\input{generated/worksheet13_exercise22_solution.id.build.tex}

\part{Unit 14}
\chapter[Kuliah 14]{Kuliah 14: Bentuk Diferensial pada Manifold}
\input{generated/lecture14.id.build.tex}

\chapter{Lembar Kerja 14}
\input{generated/worksheet14.id.build.tex}

\section*{Solusi yang disediakan oleh sumber}
\addcontentsline{toc}{section}{Solusi yang disediakan oleh sumber}
\subsection*{Solusi Soal 14.5}
\input{generated/worksheet14_exercise05_solution.id.build.tex}
\subsection*{Solusi Soal 14.6}
\input{generated/worksheet14_exercise06_solution.id.build.tex}
\subsection*{Solusi Soal 14.9}
\input{generated/worksheet14_exercise09_solution.id.build.tex}
\subsection*{Solusi Soal 14.11}
\input{generated/worksheet14_exercise11_solution.id.build.tex}
\subsection*{Solusi Soal 14.12}
\input{generated/worksheet14_exercise12_solution.id.build.tex}
\subsection*{Solusi Soal 14.13}
\input{generated/worksheet14_exercise13_solution.id.build.tex}
\subsection*{Solusi Soal 14.14}
\input{generated/worksheet14_exercise14_solution.id.build.tex}

\part{Unit 15}
\chapter[Kuliah 15]{Kuliah 15: Integrasi pada Manifold}
\input{generated/lecture15.id.build.tex}

\chapter{Lembar Kerja 15}
\input{generated/worksheet15.id.build.tex}

\section*{Solusi yang disediakan oleh sumber}
\addcontentsline{toc}{section}{Solusi yang disediakan oleh sumber}
\subsection*{Solusi Soal 15.1}
\input{generated/worksheet15_exercise01_solution.id.build.tex}
\subsection*{Solusi Soal 15.11}
\input{generated/worksheet15_exercise11_solution.id.build.tex}
\subsection*{Solusi Soal 15.12}
\input{generated/worksheet15_exercise12_solution.id.build.tex}
\subsection*{Solusi Soal 15.13}
\input{generated/worksheet15_exercise13_solution.id.build.tex}

\part{Unit 16}
\chapter[Kuliah 16]{Kuliah 16: Manifold Riemann}
\input{generated/lecture16.id.build.tex}

\chapter{Lembar Kerja 16}
\input{generated/worksheet16.id.build.tex}

\section*{Solusi yang disediakan oleh sumber}
\addcontentsline{toc}{section}{Solusi yang disediakan oleh sumber}
\subsection*{Solusi Soal 16.1}
\input{generated/worksheet16_exercise01_solution.id.build.tex}
\subsection*{Solusi Soal 16.12}
\input{generated/worksheet16_exercise12_solution.id.build.tex}

\part{Unit 17}
\chapter[Kuliah 17]{Kuliah 17: Perhitungan pada Manifold Riemann}
\input{generated/lecture17.id.build.tex}

\chapter{Lembar Kerja 17}
\input{generated/worksheet17.id.build.tex}

\section*{Solusi yang disediakan oleh sumber}
\addcontentsline{toc}{section}{Solusi yang disediakan oleh sumber}
\subsection*{Solusi Soal 17.2}
\input{generated/worksheet17_exercise02_solution.id.build.tex}
\subsection*{Solusi Soal 17.4}
\input{generated/worksheet17_exercise04_solution.id.build.tex}

\part{Unit 18}
\chapter[Kuliah 18]{Kuliah 18: Isometri dan Permukaan Hiperbolik}
\input{generated/lecture18.id.build.tex}

\chapter{Lembar Kerja 18}
\input{generated/worksheet18.id.build.tex}

\section*{Solusi yang disediakan oleh sumber}
\addcontentsline{toc}{section}{Solusi yang disediakan oleh sumber}
\subsection*{Solusi Soal 18.8}
\input{generated/worksheet18_exercise08_solution.id.build.tex}
\subsection*{Solusi Soal 18.11}
\input{generated/worksheet18_exercise11_solution.id.build.tex}
\subsection*{Solusi Soal 18.13}
\input{generated/worksheet18_exercise13_solution.id.build.tex}
\subsection*{Solusi Soal 18.14}
\input{generated/worksheet18_exercise14_solution.id.build.tex}

\part{Unit 19}
\chapter[Kuliah 19]{Kuliah 19: Pemetaan Weingarten dan Kelengkungan Gauss}
\input{generated/lecture19.id.build.tex}

\chapter{Lembar Kerja 19}
\input{generated/worksheet19.id.build.tex}

'@
$backmatterMarker = '\backmatter'
if (($driverText.Split($backmatterMarker).Count - 1) -ne 1) {
    throw 'Unit 10 wrapper must contain exactly one backmatter marker'
}
$driverText = $driverText.Replace($backmatterMarker, $unitExtension.TrimStart() + "`n" + $backmatterMarker)

$attributionMarker = '\input{generated/unit10-media-attribution-cumulative.tex}'
if (($driverText.Split($attributionMarker).Count - 1) -ne 1) {
    throw 'Unit 10 wrapper must contain exactly one Unit 10 attribution input'
}
$attributionExtension = @'
\input{generated/unit11-media-attribution-cumulative.tex}
\input{generated/unit12-media-attribution-cumulative.tex}
\input{generated/unit13-media-attribution-cumulative.tex}
\input{generated/unit14-media-attribution-cumulative.tex}
\input{generated/unit15-media-attribution-cumulative.tex}
\input{generated/unit16-media-attribution-cumulative.tex}
\input{generated/unit17-media-attribution-cumulative.tex}
\input{generated/unit18-media-attribution-cumulative.tex}
\input{generated/unit19-media-attribution-cumulative.tex}
'@
$driverText = $driverText.Replace($attributionMarker, $attributionMarker + "`n" + $attributionExtension.TrimEnd())
$driverText = $driverText.Replace("`r`n", "`n").Replace("`r", "`n")
[IO.File]::WriteAllBytes($driverPath, $utf8NoBom.GetBytes($driverText))

if (
    $driverText.Count -eq 0 -or
    $driverText.IndexOf('\documentclass[11pt,a4paper,oneside]{book}', [StringComparison]::Ordinal) -lt 0 -or
    $driverText.IndexOf('\usepackage[a4paper,margin=22mm,headheight=15pt]{geometry}', [StringComparison]::Ordinal) -lt 0
) {
    throw 'Derived Unit 19 driver lost the centered A4/22mm geometry contract'
}
$driverIdentity = Get-Identity -Path $driverPath
$wrapperReceipt = [ordered]@{
    schema_version = 1
    workflow = 'o011-unit19-wrapper-derivation-v1'
    input = [ordered]@{ path = $prefixWrapperRel; bytes = $prefixFixed.wrapper.bytes; sha256 = $prefixFixed.wrapper.sha256 }
    output = [ordered]@{ path = $driverRel; bytes = $driverIdentity.bytes; sha256 = $driverIdentity.sha256 }
    geometry = [ordered]@{ paper = 'A4'; margin = '22mm'; centered = $true; class_option = 'oneside' }
    extension_units = @(11, 12, 13, 14, 15, 16, 17, 18, 19)
    supplied_solutions = [ordered]@{
        '11' = @(10, 14)
        '12' = @(11, 12)
        '13' = @(1, 10, 11, 16, 18, 19, 21, 22)
        '14' = @(5, 6, 9, 11, 12, 13, 14)
        '15' = @(1, 11, 12, 13)
        '16' = @(1, 12)
        '17' = @(2, 4)
        '18' = @(8, 11, 13, 14)
        '19' = @()
    }
    unit12_gif_static_pdf_fallback = [ordered]@{ path = $gifDerivative.path; frame_index = 0; sha256 = $gifDerivative.sha256 }
}
$wrapperReceiptPath = Join-Path $qaDir 'WRAPPER_DERIVATION_RECEIPT.json'
[IO.File]::WriteAllBytes(
    $wrapperReceiptPath,
    $utf8NoBom.GetBytes(($wrapperReceipt | ConvertTo-Json -Depth 7) + "`n")
)

# Import the current identity of every transitive Unit 10 input except the
# append-only shared media configuration. The historical receipt remains an
# immutable public snapshot; later production legitimately evolved several
# shared build helpers and cumulative receipts. Current identities still guard
# the complete live build graph against changes during the Unit 19 cycles.
$prefixBuildReceipt = Read-JsonFile -Path (Resolve-ProjectLeaf -RelativePath $prefixFixed.build_receipt.path)
foreach ($row in @($prefixBuildReceipt.inputs)) {
    if ($row.path -ne 'source/unit_media.json') {
        Add-GuardCurrent -RelativePath $row.path -Label 'current Unit 10 transitive input' | Out-Null
    }
}
foreach ($row in @(
    $prefixFixed.build_script,
    $prefixFixed.verify_script,
    $prefixFixed.wrapper,
    $prefixFixed.archive,
    $prefixFixed.pdf,
    $prefixFixed.build_receipt,
    $prefixFixed.structural_qa
)) {
    Add-GuardExpected -RelativePath $row.path -Bytes $row.bytes -Sha256 $row.sha256 -Label 'exact Unit 10 prefix boundary'
}
Add-GuardCurrent -RelativePath 'source/unit_media.json' -Label 'untouched live Unit 19 media configuration' | Out-Null
Add-GuardCurrent -RelativePath 'authority/brenner_media_rights_manifest.csv' -Label 'media rights manifest' | Out-Null
Add-GuardCurrent -RelativePath 'scripts/prepare_unit_tex.py' -Label 'TeX preparer' | Out-Null
Add-GuardCurrent -RelativePath 'scripts/prepare_unit_media.py' -Label 'media preparer' | Out-Null
Add-GuardCurrent -RelativePath 'scripts/build_through_unit19.ps1' -Label 'Unit 19 build script' | Out-Null
Add-GuardCurrent -RelativePath 'scripts/verify_through_unit19_pdf.py' -Label 'Unit 19 structural verifier' | Out-Null
Add-GuardCurrent -RelativePath (Get-RelativeProjectPath -Path $prefixTransactionReceiptPath) -Label 'Unit 10 prefix preservation receipt' | Out-Null
Add-GuardCurrent -RelativePath (Get-RelativeProjectPath -Path $aliasReceiptPath) -Label 'Unit 19 media alias receipt' | Out-Null
Add-GuardCurrent -RelativePath (Get-RelativeProjectPath -Path $wrapperReceiptPath) -Label 'Unit 19 wrapper receipt' | Out-Null
Add-GuardExpected -RelativePath $driverRel -Bytes $driverIdentity.bytes -Sha256 $driverIdentity.sha256 -Label 'Unit 19 driver'

$auxiliaryNames = @(
    'through-unit-19.aux', 'through-unit-19.log', 'through-unit-19.out',
    'through-unit-19.pdf', 'through-unit-19.toc', 'through-unit-19.lof',
    'through-unit-19.fls', 'through-unit-19.fdb_latexmk'
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
    param([Parameter(Mandatory)][int]$Cycle)
    Assert-GuardIdentities -Stage "before clean cycle $Cycle"
    Clear-ExactAuxiliaryFiles
    $cycleLogs = @()
    Push-Location $buildDir
    try {
        foreach ($pass in 1..3) {
            $logPath = Join-Path $workDir ("cycle-{0}-pass-{1}.console.txt" -f $Cycle, $pass)
            & $pdfLatex '-interaction=nonstopmode' '-halt-on-error' '-file-line-error' '-recorder' '-jobname=through-unit-19' 'generated/through-unit-19-driver.tex' 2>&1 |
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
    $built = Join-Path $buildDir 'through-unit-19.pdf'
    if (-not (Test-Path -LiteralPath $built -PathType Leaf)) {
        throw "pdflatex did not create $built"
    }
    Assert-GuardIdentities -Stage "after clean cycle $Cycle"
    $cyclePdf = Join-Path $workDir ("cycle-{0}.pdf" -f $Cycle)
    Copy-Item -LiteralPath $built -Destination $cyclePdf -Force
    return [ordered]@{
        cycle = $Cycle
        pdf = Get-RelativeProjectPath -Path $cyclePdf
        bytes = (Get-Item -LiteralPath $cyclePdf).Length
        sha256 = (Get-FileHash -LiteralPath $cyclePdf -Algorithm SHA256).Hash.ToLowerInvariant()
        logs = @($cycleLogs | ForEach-Object {
            [ordered]@{
                path = Get-RelativeProjectPath -Path $_
                bytes = (Get-Item -LiteralPath $_).Length
                sha256 = (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash.ToLowerInvariant()
            }
        })
    }
}

$receipt = $null
try {
    $cycle1 = Invoke-BuildCycle -Cycle 1
    $cycle2 = Invoke-BuildCycle -Cycle 2
    if ($cycle1.bytes -ne $cycle2.bytes -or $cycle1.sha256 -ne $cycle2.sha256) {
        throw "Clean-cycle PDF mismatch: $($cycle1.sha256) != $($cycle2.sha256)"
    }
    Assert-GuardIdentities -Stage 'before final PDF installation'
    Copy-Item -LiteralPath (Join-Path $workDir 'cycle-2.pdf') -Destination $outputPdf -Force

    $inputs = @($guardIdentities.Keys | Sort-Object | ForEach-Object {
        $identity = $guardIdentities[$_]
        [ordered]@{ path = $_; bytes = [long]$identity.bytes; sha256 = $identity.sha256 }
    })
    $engineVersion = (& $pdfLatex --version | Select-Object -First 1)
    $outputIdentity = Get-Identity -Path $outputPdf
    $receipt = [ordered]@{
        schema_version = 1
        workflow = 'o011-through-unit19-pdf-build-v1'
        engine = $engineVersion
        command = 'pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -recorder -jobname=through-unit-19 generated/through-unit-19-driver.tex (three passes per clean cycle; two clean cycles)'
        deterministic_clean_cycles = $true
        cumulative_prefix = [ordered]@{
            exact_through_unit = 10
            preservation_receipt = Get-RelativeProjectPath -Path $prefixTransactionReceiptPath
            build = $prefixFixed.build_receipt
            structural_qa = $prefixFixed.structural_qa
            pdf = $prefixFixed.pdf
            frozen_media_config_archive = $prefixFixed.archive
            frozen_media_config_entry = $prefixFixed.media_config_entry
        }
        wrapper = $wrapperReceipt
        unit_bindings = @($unitBindings)
        media_bindings = @($mediaBindings)
        interactive_media_binding = $interactiveBinding
        animated_media_binding = $animatedBinding
        cycles = @($cycle1, $cycle2)
        inputs = $inputs
        output = [ordered]@{
            path = Get-RelativeProjectPath -Path $outputPdf
            bytes = $outputIdentity.bytes
            sha256 = $outputIdentity.sha256
        }
        structural_verifier = [ordered]@{
            path = 'scripts/verify_through_unit19_pdf.py'
            bytes = $guardIdentities['scripts/verify_through_unit19_pdf.py'].bytes
            sha256 = $guardIdentities['scripts/verify_through_unit19_pdf.py'].sha256
            output = 'qa/unit-19/pdf_structural_qa.json'
        }
    }
    $receiptPath = Join-Path $qaDir 'build.json'
    [IO.File]::WriteAllBytes(
        $receiptPath,
        $utf8NoBom.GetBytes(($receipt | ConvertTo-Json -Depth 12) + "`n")
    )

    Invoke-CheckedPython @((Join-Path $laneRoot 'scripts\verify_through_unit19_pdf.py')) | Out-Null
    $structuralQa = Read-JsonFile -Path (Join-Path $qaDir 'pdf_structural_qa.json')
    if ($structuralQa.passed -ne $true) {
        throw 'Cumulative Unit 19 structural/accessibility QA did not pass'
    }
}
finally {
    if (Test-Path -LiteralPath $temporaryJpegAlias -PathType Leaf) {
        Assert-Identity -Path $temporaryJpegAlias -Bytes $temporaryJpegIdentity.bytes -Sha256 $temporaryJpegIdentity.sha256 -Label 'transient Unit 10 JPEG alias cleanup'
        Remove-Item -LiteralPath $temporaryJpegAlias -Force
    }
    if (Test-Path -LiteralPath $temporaryRiemannAlias -PathType Leaf) {
        Assert-Identity -Path $temporaryRiemannAlias -Bytes $temporaryRiemannIdentity.bytes -Sha256 $temporaryRiemannIdentity.sha256 -Label 'transient Unit 16 JPEG loader alias cleanup'
        Remove-Item -LiteralPath $temporaryRiemannAlias -Force
    }
    Clear-ExactAuxiliaryFiles
}

Write-Output ($receipt | ConvertTo-Json -Depth 12)
