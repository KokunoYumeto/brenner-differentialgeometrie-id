[CmdletBinding()]
param(
    [string] $AuthorityRoot = (Join-Path (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path 'authority')
)

$ErrorActionPreference = 'Stop'

$authorityRoot = (Resolve-Path -LiteralPath $AuthorityRoot).Path
$mediawikiRoot = Join-Path $authorityRoot 'mediawiki'
$course = 'Kurs:Differentialgeometrie (Osnabrück 2023)'
$rootTitles = @($course) + (1..29 | ForEach-Object { "$course/Vorlesung $_" }) + (1..29 | ForEach-Object { "$course/Arbeitsblatt $_" })
$surfaceTitles = @(
    (1..29 | ForEach-Object { "$course/Vorlesung $_/latex" })
    (1..29 | ForEach-Object { "$course/Arbeitsblatt $_/latex" })
    (1..29 | ForEach-Object { "$course/Vorlesung $_/kontrolle" })
    (1..29 | ForEach-Object { "$course/Arbeitsblatt $_/kontrolle" })
    'Projekt:Semantische Vorlagen/Skriptvorspann in Latex'
)

function Export-SelectedRevisionManifest {
    param(
        [Parameter(Mandatory)] [string] $XmlPath,
        [Parameter(Mandatory)] [string[]] $SelectedTitles,
        [Parameter(Mandatory)] [string] $OutputPath
    )

    [xml] $doc = Get-Content -LiteralPath $XmlPath -Raw -Encoding utf8
    $manager = [System.Xml.XmlNamespaceManager]::new($doc.NameTable)
    $manager.AddNamespace('mw', $doc.DocumentElement.NamespaceURI)
    $byTitle = @{}
    foreach ($page in $doc.SelectNodes('/mw:mediawiki/mw:page', $manager)) {
        $title = $page.SelectSingleNode('mw:title', $manager).InnerText
        $byTitle[$title] = $page
    }

    $xmlSha256 = (Get-FileHash -LiteralPath $XmlPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $rows = foreach ($title in $SelectedTitles) {
        if (-not $byTitle.ContainsKey($title)) { throw "Selected title absent from export: $title" }
        $page = $byTitle[$title]
        $revision = $page.SelectSingleNode('mw:revision', $manager)
        $textNode = $revision.SelectSingleNode('mw:text', $manager)
        $text = if ($null -eq $textNode) { '' } else { $textNode.InnerText }
        [pscustomobject]@{
            title = $title
            namespace = $page.SelectSingleNode('mw:ns', $manager).InnerText
            pageid = $page.SelectSingleNode('mw:id', $manager).InnerText
            revid = $revision.SelectSingleNode('mw:id', $manager).InnerText
            timestamp_utc = $revision.SelectSingleNode('mw:timestamp', $manager).InnerText
            mediawiki_sha1_base36 = $revision.SelectSingleNode('mw:sha1', $manager).InnerText
            text_utf8_bytes = [Text.Encoding]::UTF8.GetByteCount($text)
            source_export_file = [IO.Path]::GetFileName($XmlPath)
            source_export_sha256 = $xmlSha256
        }
    }
    if ($rows.Count -ne $SelectedTitles.Count) { throw "Expected $($SelectedTitles.Count) rows; got $($rows.Count)" }
    $rows | Export-Csv -LiteralPath $OutputPath -NoTypeInformation -Encoding utf8
}

$rootManifest = Join-Path $authorityRoot 'brenner_selected_root_revisions.csv'
$surfaceManifest = Join-Path $authorityRoot 'brenner_selected_surface_revisions.csv'
Export-SelectedRevisionManifest -XmlPath (Join-Path $mediawikiRoot 'brenner_course_recursive_current.xml') -SelectedTitles $rootTitles -OutputPath $rootManifest
Export-SelectedRevisionManifest -XmlPath (Join-Path $mediawikiRoot 'brenner_latex_kontrolle_recursive_current.xml') -SelectedTitles $surfaceTitles -OutputPath $surfaceManifest

Get-Item -LiteralPath $rootManifest, $surfaceManifest | ForEach-Object {
    [pscustomobject]@{
        path = $_.FullName
        rows = (Import-Csv -LiteralPath $_.FullName).Count
        bytes = $_.Length
        sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
} | ConvertTo-Json -Depth 3
