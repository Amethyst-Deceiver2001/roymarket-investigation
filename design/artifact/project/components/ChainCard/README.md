# ChainCard

One object in a chain: a company, product, storefront, buyer or recipient list.

- The header holds the kind mark and kind label ("Maker", "Sells", "State buyer"). The name in Spectral follows: Cyrillic as registered, with an English gloss in `<small>`.
- `.hub` is for ЦБСТ only: a 2px ink border. There is no hub colour.
- `.absent` is a dashed card with no shadow, for something a reader would expect that is not there.
- Rows are `p` elements at the note size; each claim ends in a `rm-ref` footnote.
- The consumer supplies the `id` that the chain's lines attach to.
