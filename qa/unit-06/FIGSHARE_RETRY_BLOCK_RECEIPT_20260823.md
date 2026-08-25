# Figshare Unit 6 retry — closed before mutation

Date: 2026-08-23 (Europe/Berlin)

The authorized, bounded retry of the existing Unit 6 Figshare lineage used the
existing article `33314790`, project `280296`, and collection `8668413`. It
first proved the public Zenodo Unit 6 record `22070425` and its six release
bytes, then queried the required public project membership. The transaction
stopped before any authenticated or mutating Figshare request because the
article was not visible as a public member of project `280296`.

Result: **no remote mutation; no duplicate article; no publication claim**.

The retry command used the existing local publisher and runtime-only token
file; the token value was neither printed nor written to this receipt. The
bounded failure was:

`article is not a public member of required Figshare project 280296`

This is a visibility/predecessor problem, not a Zenodo problem. Retry the same
article lineage only after the public project/article inventory becomes
readable. Unit 6 remains publicly preserved and byte-verified on Zenodo DOI
`10.5281/zenodo.22070425`.
