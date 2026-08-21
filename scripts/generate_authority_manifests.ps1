[CmdletBinding()]
param(
    [string] $OutputRoot = (Join-Path (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path 'authority')
)

$ErrorActionPreference = 'Stop'

$freezeRoot = (Resolve-Path -LiteralPath $OutputRoot).Path
$retrievedUtc = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')
$course = 'Kurs:Differentialgeometrie (Osnabrück 2023)'
$rootTitles = @($course) + (1..29 | ForEach-Object { "$course/Vorlesung $_" }) + (1..29 | ForEach-Object { "$course/Arbeitsblatt $_" })
$surfaceTitles = @(
    (1..29 | ForEach-Object { "$course/Vorlesung $_/latex" })
    (1..29 | ForEach-Object { "$course/Arbeitsblatt $_/latex" })
    (1..29 | ForEach-Object { "$course/Vorlesung $_/kontrolle" })
    (1..29 | ForEach-Object { "$course/Arbeitsblatt $_/kontrolle" })
    'Projekt:Semantische Vorlagen/Skriptvorspann in Latex'
)

$imageTitles = @(
    'File:2019-07-Helix.jpg',
    'File:3d-function-6.svg',
    'File:Cilinderprojectie-constructie.jpg',
    'File:Circle - black simple.svg',
    'File:Circle on sphere wireframe 10deg 6r.svg',
    'File:Euler spiral.svg',
    'File:Evolute-parab.svg',
    'File:Fiddler crab mobius strip.gif',
    'File:Georg Friedrich Bernhard Riemann.jpeg',
    'File:Great circle passing through two points.svg',
    'File:Hyperboloid1.png',
    'File:Hyperboloid2.png',
    'File:Inclusion-exclusion.svg',
    'File:Inner point.png',
    'File:Insect on a torus tracing out a non-trivial geodesic.gif',
    'File:Integral apl rot obsah1.svg',
    'File:Manifold zahyou3.png',
    'File:Minimal surface curvature planes-de.svg',
    'File:Möbius strip.jpg',
    'File:Not-star-shaped.svg',
    'File:Parabola circle.svg',
    "File:Parallel lines in Poincare's model of hyperbolic geometry.svg",
    'File:Parallel transport sphere2.svg',
    'File:Partition of unity illustration.svg',
    'File:Planned flight map of the Oiseau Blanc.svg',
    'File:Poincarehalfplaneconform.gif',
    'File:Runge theorem.svg',
    'File:Sphere with three handles.png',
    'File:SS-stokes.jpg',
    'File:Stereographic projection in 3D.png',
    'File:Tangent bundle.svg',
    'File:Tangentialvektor.svg',
    'File:Théorème-de-Brouwer-(cond-1).jpg',
    'File:Théorème-de-Brouwer-(cond-2).jpg',
    'File:Toroidal coord.png',
    'File:Torus vectors oblique.jpg'
)

$headers = @{ 'User-Agent' = 'Codex-O011-freeze/1.0 (source metadata audit)' }
$api = 'https://de.wikiversity.org/w/api.php?action=query&format=json&formatversion=2&prop=imageinfo&iiprop=url|size|sha1|mime|extmetadata&titles='
$data = Invoke-RestMethod -Uri ($api + [uri]::EscapeDataString(($imageTitles -join '|'))) -Headers $headers -Method Get
$mediaRows = foreach ($page in $data.query.pages) {
    $info = $page.imageinfo[0]
    $meta = $info.extmetadata
    [pscustomobject]@{
        retrieved_utc = $retrievedUtc
        title = ($page.title -replace '^Datei:', 'File:')
        bytes = $info.size
        width = $info.width
        height = $info.height
        mime = $info.mime
        commons_sha1_hex = $info.sha1
        license = $meta.LicenseShortName.value
        license_url = $meta.LicenseUrl.value
        attribution_required = $meta.AttributionRequired.value
        copyrighted = $meta.Copyrighted.value
        artist_html = $meta.Artist.value
        credit_html = $meta.Credit.value
        original_url = ($info.url -replace '\?.*$', '')
        description_url = $info.descriptionurl
        metadata_api = 'https://de.wikiversity.org/w/api.php (foreign-repository imageinfo/extmetadata)'
    }
}
$mediaRows = @($mediaRows | Sort-Object title)
if ($mediaRows.Count -ne 36) { throw "Expected 36 media rows; got $($mediaRows.Count)" }

$mediaPath = Join-Path $freezeRoot 'brenner_media_rights_manifest.csv'
$mediaRows | Export-Csv -LiteralPath $mediaPath -NoTypeInformation -Encoding utf8

$linkRows = @()
foreach ($row in $mediaRows) {
    $linkRows += [pscustomobject]@{
        title = $row.title
        class = 'commons_image_asset'
        exists = $true
        status = 'metadata_verified'
        bytes = $row.bytes
        commons_sha1_hex = $row.commons_sha1_hex
        license = $row.license
        source_url = $row.original_url
        description_url = $row.description_url
        evidence = 'de.wikiversity foreign-repository imageinfo/extmetadata'
    }
}

foreach ($kind in @('Vorlesung', 'Arbeitsblatt')) {
    foreach ($number in 1..29) {
        $name = "File:Differentialgeometrie (Osnabrück 2023)$kind$number.pdf"
        $isLecture4 = ($kind -eq 'Vorlesung' -and $number -eq 4)
        $linkRows += [pscustomobject]@{
            title = $name
            class = 'per_unit_pdf_link'
            exists = $isLecture4
            status = if ($isLecture4) { 'commons_file_verified' } else { 'missing_upload_placeholder' }
            bytes = if ($isLecture4) { 210221 } else { $null }
            commons_sha1_hex = if ($isLecture4) { '610c2216778a3121aee356f992560cd55ed90690' } else { $null }
            license = if ($isLecture4) { 'CC BY-SA 4.0' } else { $null }
            source_url = if ($isLecture4) { 'https://upload.wikimedia.org/wikipedia/commons/9/93/Differentialgeometrie_%28Osnabr%C3%BCck_2023%29Vorlesung4.pdf' } else { $null }
            description_url = if ($isLecture4) { 'https://commons.wikimedia.org/wiki/File:Differentialgeometrie_(Osnabr%C3%BCck_2023)Vorlesung4.pdf' } else { $null }
            evidence = if ($isLecture4) { 'Commons file metadata/category listing frozen 2026-08-21' } else { 'Course link resolves to Commons UploadWizard; absent from official Commons course PDF category on 2026-08-21' }
        }
    }
}
$linkRows = @($linkRows | Sort-Object class, title)
if ($linkRows.Count -ne 94) { throw "Expected 94 links; got $($linkRows.Count)" }
if ((@($linkRows | Where-Object { $_.class -eq 'commons_image_asset' })).Count -ne 36) { throw 'Expected 36 image links' }
if ((@($linkRows | Where-Object { $_.class -eq 'per_unit_pdf_link' })).Count -ne 58) { throw 'Expected 58 PDF links' }
if ((@($linkRows | Where-Object { $_.class -eq 'per_unit_pdf_link' -and $_.exists })).Count -ne 1) { throw 'Expected exactly one existing PDF' }

$linksPath = Join-Path $freezeRoot 'brenner_94_link_classification.csv'
$linkRows | Export-Csv -LiteralPath $linksPath -NoTypeInformation -Encoding utf8

$receiptLines = [System.Collections.Generic.List[string]]::new()
$receiptLines.Add('Brenner Differentialgeometrie authority/export receipt')
$receiptLines.Add("generated_utc: $retrievedUtc")
$receiptLines.Add('canonical_course_url: https://de.wikiversity.org/wiki/Kurs:Differentialgeometrie_(Osnabr%C3%BCck_2023)')
$receiptLines.Add('canonical_course_pageid: 142521')
$receiptLines.Add('canonical_course_revid: 889544')
$receiptLines.Add('canonical_course_revision_timestamp: 2023-03-07T11:39:09Z')
$receiptLines.Add('canonical_course_api_sha1_hex: e274ea4f0ae092736a5df23dfd3bb744184a9f2d')
$receiptLines.Add('author/course_teacher: Holger Brenner')
$receiptLines.Add('authority_teaching_page: https://de.wikiversity.org/wiki/Benutzer:Holger_Brenner/Lehre')
$receiptLines.Add('authority_course_catalog: https://de.wikiversity.org/wiki/Mathematik/Kurse/H%C3%B6here_Analysis')
$receiptLines.Add('course_text_license: CC BY-SA 4.0 (individual Commons media have their own licenses; see CSV)')
$receiptLines.Add('license_url: https://creativecommons.org/licenses/by-sa/4.0/')
$receiptLines.Add('')
$receiptLines.Add('SPECIAL:EXPORT RECIPE')
$receiptLines.Add('endpoint: POST https://de.wikiversity.org/wiki/Special:Export')
$receiptLines.Add('content_type: application/x-www-form-urlencoded')
$receiptLines.Add('fields: pages=<newline-separated exact titles>; curonly=1; templates=1; wpDownload=1')
$receiptLines.Add('warning: this is a request-time current-revision recursive export, not an immutable archive endpoint; freeze authority is the resulting file SHA-256 plus embedded pageid/revid/timestamp/sha1 revision set.')
$receiptLines.Add('')
$receiptLines.Add('ROOT EXPORT FILE')
$receiptLines.Add('file: brenner_course_recursive_current.xml')
$receiptLines.Add('bytes: 3538709')
$receiptLines.Add('sha256: 6b96c90a8b1e52fac57c735f28d0babc56a95050ca015075b755179270d75d14')
$receiptLines.Add('export_timestamp_utc: 2026-08-21T09:52:04Z')
$receiptLines.Add('recursive_pages: 2715 (NS0=2151, NS10=197, NS106=367)')
$receiptLines.Add('revision_set_sha256_sorted_title_pageid_revid_timestamp_sha1: 4810e9c13e352db58d7ceb5495c1cf86cb991d2193eaf6a344a48799e7ab0f71')
$receiptLines.Add('selected_root_title_count: 59')
$receiptLines.Add('selected_root_titles:')
foreach ($title in $rootTitles) { $receiptLines.Add("  $title") }
$receiptLines.Add('')
$receiptLines.Add('LATEX/KONTROLLE EXPORT FILE')
$receiptLines.Add('file: brenner_latex_kontrolle_recursive_current.xml')
$receiptLines.Add('bytes: 3722387')
$receiptLines.Add('sha256: 4c489c44a3d856304a8724e04c1007aa8b18d0e7099257aaf711a084eab0de7c')
$receiptLines.Add('export_timestamp_utc: 2026-08-21T09:58:52Z')
$receiptLines.Add('recursive_pages: 2866 (NS0=2154, NS10=193, NS106=491, NS108=28)')
$receiptLines.Add('revision_set_sha256_sorted_title_pageid_revid_timestamp_sha1: e274c45e0496b3e842d7aa2a4f7c68005f7a6b58c6bcb3ce1c6763cdefb0da28')
$receiptLines.Add('selected_surface_title_count: 117 (116 lecture/worksheet latex+kontrolle surfaces plus the official preamble)')
$receiptLines.Add('selected_surface_titles:')
foreach ($title in $surfaceTitles) { $receiptLines.Add("  $title") }
$receiptLines.Add('')
$receiptLines.Add('EXPANDTEMPLATES RECIPE')
$receiptLines.Add('endpoint: GET https://de.wikiversity.org/w/api.php')
$receiptLines.Add('parameters: action=expandtemplates; format=json; formatversion=2; prop=wikitext|categories|modules|jsconfigvars; title=<exact .../latex surface title>; text={{Latex}}')
$receiptLines.Add('note: expanded output is body/custom-macro TeX and contains HTML <br /> and entities; it is not a standalone compilable LaTeX document.')
$receiptLines.Add('')
$receiptLines.Add('OFFICIAL PDF EXPORT WITNESS')
$receiptLines.Add('endpoint: POST https://de.wikiversity.org/wiki/Spezial:DownloadAsPdf')
$receiptLines.Add('fields: action=redirect-to-electron; page=<exact regular page title>')
$receiptLines.Add('note: valid tagged PDF export works, but visual QA found reader-blocking title/edit-URL overflow, navigation clutter, and a nearly blank last page; use only as a witness/fallback.')
$receiptLines.Add('')
$receiptLines.Add('94-LINK CLASSIFICATION')
$receiptLines.Add('query: action=query; prop=images; imlimit=max over the 59 selected root pages')
$receiptLines.Add('unique_file_links: 94')
$receiptLines.Add('commons_image_assets: 36')
$receiptLines.Add('per_unit_pdf_links: 58')
$receiptLines.Add('existing_per_unit_pdfs: 1 (Vorlesung4)')
$receiptLines.Add('missing_upload_placeholders: 57')
$receiptLines.Add('image_binary_total_bytes_from_api: 10809589')
$receiptLines.Add('license_distribution: Public domain=16; CC BY 2.5=1; CC BY 3.0=2; CC BY-SA 3.0=11; CC BY-SA 4.0=6')
$receiptLines.Add('media_warning: preserve per-component attribution/license; do not blanket-relicense Commons assets as course text.')

$receiptPath = Join-Path $freezeRoot 'brenner_export_and_title_inventory_receipt.txt'
[System.IO.File]::WriteAllLines($receiptPath, $receiptLines, [System.Text.UTF8Encoding]::new($false))

Get-Item -LiteralPath $mediaPath, $linksPath, $receiptPath | ForEach-Object {
    [pscustomobject]@{
        path = $_.FullName
        bytes = $_.Length
        sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
} | ConvertTo-Json -Depth 3
