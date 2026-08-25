# Figshare Unit 6 publication preflight — closed without mutation

Date: 2026-08-23 (Europe/Berlin)

The authorized Unit 6 update was attempted against the existing work lineage
(article `33314790`) in project `280296` and Indonesian collection `8668413`.
The transaction was stopped before any remote mutation because the required
predecessor was not visible to the authenticated/public Figshare API:

- `GET /v2/articles/33314790` returned HTTP 404 (`Entity not found`).
- `GET /v2/projects/280296/articles` returned an empty article list.
- `GET /v2/collections/8668413/articles` returned an empty article list.
- Exact DOI search for `10.6084/m9.figshare.33314790.v2` returned no item.
- The DOI redirect currently reaches an AWS WAF challenge (HTTP 202), not a
  readable article record.

The publisher therefore performed no create, update, publish, collection
addition, or deletion, and created no duplicate article. The existing Unit 5
Figshare receipt remains historical evidence only. The Unit 6 reader-first
payload is preserved and publicly verified on the existing Zenodo concept;
Figshare remains `pending_predecessor_visibility` and must be retried only
after the same article/project/collection preflight succeeds.

No credential, token value, private locator, or personal path is recorded in
this receipt.
