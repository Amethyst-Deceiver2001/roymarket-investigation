# TsBST and ROI.MARKET: an open-source investigation

An evidence base on **TsBST** (ЦБСТ, АНО «Центр беспилотных систем»), a Moscow non-profit for the drone industry, and **ROI.MARKET** (РОЙ.МАРКЕТ), the login-only "military marketplace" its circle runs. It follows the chain from the non-profit and its programmes to the makers, the products, the sellers and state buyers, and the units that say they receive them. It is built as a reference for sanctions work.

A solo project by [Alexey Kovalev](https://en.wikipedia.org/wiki/Alexey_Kovalev_(journalist)), an independent Russian reporter in exile. It grew out of [WB Watch](https://amethyst-deceiver2001.github.io/wb-watcher/), a tracker of military goods sold on Wildberries.

## Read it

**The landing page** is the place to start: [amethyst-deceiver2001.github.io/roymarket-investigation](https://amethyst-deceiver2001.github.io/roymarket-investigation/) (source: [`docs/index.html`](docs/index.html)). It tells the story in plain language and links every claim to a numbered source.

Chain views per product («Булат», «Капюшон»), company files and a people matrix exist as private previews and move to the site as each is cleared for publication.

## How claims are graded

Every line is graded by how well a document shows it, never by how likely it sounds.

| Grade | Means |
|---|---|
| **Documented** | A primary document shows it: a company-register extract, a charter, a court filing, a sanctions-list entry. |
| **Reported** | One party's own word, or the press. Attributed to whoever says it. |
| **Not documented** | The link may exist; no source shows it. Kept visible so a gap is not mistaken for a finding. |

Facts come from the original document, read in full in its own language, normally Russian. Quotes are verbatim. A product name is never a company brand, a unit number never identifies a unit, and a delivery post never implies use in combat. The investigation states what ROI.MARKET's public pages show: the catalogue is behind a login, so what is "on the platform" is graded by who claims it.

## What is in the repo

- `data/registry/`: the source of truth. Entities, people, products, deliveries, media, programmes, military units, quotes and sources as JSON, each time-variant fact dated and sourced. Every page is generated from it.
- `exhibits/`: the page builders and their tests. `docs/`: the public site.
- `scripts/`: registry checks, the relationship graph, screening and source tools. `tests/`: their tests.
- `notes/`: the live plan, workstream notes, and reference documents ([`notes/reference/`](notes/reference/)).
- `data/sources/` (archived documents) and `data/roymarket.db` (Telegram posts) are kept locally and are not in the repository.
- [`CLAUDE.md`](CLAUDE.md) holds the working rules; [`STYLE_GUIDE.md`](STYLE_GUIDE.md) the voice and naming. The old layout list is in [`notes/reference/repo_layout.md`](notes/reference/repo_layout.md).

## Rebuild

```
python3 scripts/build_relationship_graph.py
python3 scripts/check_registry.py          # must show 0 errors
python3 exhibits/build_landing.py --out docs/index.html
```

Page builders need Python 3.11 with `beautifulsoup4`; Telegram scripts need Telethon (see `requirements.txt`).

## Corrections and right of reply

If you are named here and a fact is wrong, or you hold a document that shows otherwise, write to kovalever@gmail.com with the page and the line. A correction that rests on a document is made in the registry with its source; the previous wording stays in the history.

## Support

This is my own time and money. If the work is useful to you, donations help with professional services, subscriptions and hosting: PayPal kovalever@googlemail.com, the [Building Democracy Foundation](https://www.paypal.com/donate/?hosted_button_id=TQ6VZ7CFSHTHW) (US, 501(c)(3)), Revolut @alexeypklg, or crypto from the landing page's "About and support" block.

## Licence

Code: MIT ([`LICENSE`](LICENSE)). The registry, the written pages and the notes: CC BY 4.0 ([`LICENSE-DATA.md`](LICENSE-DATA.md)). Third-party pictures, quotations, logos and register content keep their owners' rights. To cite, use "Cite this repository" on the repo page ([`CITATION.cff`](CITATION.cff)).
