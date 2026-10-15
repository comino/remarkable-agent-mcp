# Licensing and provenance

The source in this repository remains under the [MIT license](LICENSE).
It builds on [Sam Morrow's remarkable-mcp](https://github.com/SamMorrowDrums/remarkable-mcp);
its copyright notice and contributor credit are retained. The Python import
name, MCP tool names and existing configuration paths preserve that lineage
and compatibility. The project is not affiliated with reMarkable AS.

## Dependency licenses

An MIT label for this repository does not describe every part of the installed
application. In particular, these required dependencies have additional terms:

| Dependency | Published license | Role |
|---|---|---|
| [PyMuPDF](https://pymupdf.io/licensing) | AGPL-3.0 or a commercial license from its publisher | PDF rendering, extraction and document generation |
| [EbookLib](https://github.com/aerkalov/ebooklib) | AGPL-3.0 | EPUB reading |

The build produces this project's source/wheel; an installer obtains its
dependencies separately. That separation is not a claim that an installed or
bundled combination is exempt from dependency license requirements. Anyone
distributing or hosting a combined application must evaluate and satisfy the
applicable terms, including corresponding-source obligations where required.
A commercial PyMuPDF license does not change EbookLib's license.

This release does not replace those dependencies or relicense upstream code.
Before publishing a bundled distribution or making a permissive-only claim,
resolve its licensing approach. For dependency versions see `uv.lock`; retain
the dependencies' own license files and notices when redistributing them.
