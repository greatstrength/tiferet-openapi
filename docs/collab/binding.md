# Binding — tiferet-openapi

**Project:** tiferet-openapi
**Repository:** https://github.com/greatstrength/tiferet-openapi
**Status:** Confirmed

This file is the local phone book, not the process. The governing collaboration
process remains the Tiferet framework's `docs/collab/` documentation until this
repository adopts local copies.

## Strands

| Fact | Value |
|---|---|
| Trunk branch | `main` |
| Prototype branch | `v1.x-proto` |
| Prototype strand active | yes |
| RFP id prefix | `TOA1` |
| RFP major | `1` |
| Next freeze id pattern | `TOA1-FREEZE-<nnn>` |

## GitHub

| Fact | Value |
|---|---|
| Owner / repo | `greatstrength/tiferet-openapi` |
| Project | Tiferet Framework- Feature Release (#2) |
| Project node id | `PVT_kwDOCKXjws4A7Y85` |
| Project URL | https://github.com/orgs/greatstrength/projects/2 |

Project #2 is selected because its stated scope includes the Tiferet Framework
and other libraries in the Tiferet ecosystem, and it supplies the size and
release-tracking fields required for trunk TRD planning.

## Project field ids (project #2)

- Status (`PVTSSF_lADOCKXjws4A7Y85zgvs_j4`): Backlog=`f75ad846`, Ready=`08afe404`, In progress=`47fc9ee4`, In review=`4cc61d42`, Done=`98236657`
- Priority (`PVTSSF_lADOCKXjws4A7Y85zgvs_no`): P0=`79628723`, P1=`0a877460`, P2=`da944a9c`
- Size (`PVTSSF_lADOCKXjws4A7Y85zgvs_ns`): XS=`eff732af`, S=`9592a5a3`, M=`9728cbdc`, L=`c53df028`, XL=`7b141a16`
- Estimate (`PVTF_lADOCKXjws4A7Y85zgvs_nw`): number
- Start date (`PVTF_lADOCKXjws4A7Y85zgvs_n4`)
- End date (`PVTF_lADOCKXjws4A7Y85zgvs_n8`)

## Milestone title shapes

- Prototype drafting round: `vX.Y.0bN`
- Trunk release: `vX.Y.Z`

## Notes on this line's tag history

`v1.x-proto` (PR #22) originally tagged this work `v1.0.0b1`, but it shipped
without an RFP behind it and predates this binding, and the tag shape itself
was wrong: it is landed code, so it belongs on the `vX.Y.0aN` alpha line, not
the `vX.Y.0bN` beta-milestone line. The maintainer is correcting this by
retagging it `v1.0.0a1` and removing the affected published package version.
With that correction, `v1.0.0b1` is free and is this line's first proper beta
milestone — the drafting round containing `TOA1-RFP-001` through
`TOA1-RFP-005`.
