# ChainCard

One object in a chain: a company, product, storefront, buyer or recipient list.

- The header holds the kind mark and kind label ("Maker", "Sells", "State buyer"), and the company's logo at the right when a media record of genre `logo` exists. A logo drawn for a dark ground (`logo_ground: dark`) sits on the dark plate. Never a product photo in its place.
- The name in Spectral follows, Latin first (STYLE_GUIDE §2.2-2.3a, revised 23.10.2026). A company leads with its documented primary brand, else its transliterated legal name (`small.lat`, `display_name()['latin']`: the legal form transliterated, never translated, OOO, AO, ANO, NPTs), footnoted to the brand's source. The registered Cyrillic name sits beneath it (`small.cyr`): it is never hidden, because sanctions lists and ЕГРЮЛ name the company in that form.
- A sole trader leads with the person's name in Latin, then "Sole trader (IP)", then the ЕГРИП name in Cyrillic.
- A state body is translated (`data/registry/name_translations.json`); its official Cyrillic name and the transliteration a sanctions list would use sit beneath.
- `.hub` is for TsBST only: a 2px ink border. There is no hub colour.
- `.absent` is a dashed card with no shadow, for something a reader would expect that is not there.
- Rows are `p` elements at the note size; each claim ends in a `rm-ref` footnote.
- The consumer supplies the `id` that the chain's lines attach to.
