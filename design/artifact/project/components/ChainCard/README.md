# ChainCard

One object in a chain: a company, product, storefront, buyer or recipient list.

- The header holds the kind mark and kind label ("Maker", "Sells", "State buyer"), and the company's logo at the right when a media record of genre `logo` exists. A logo drawn for a dark ground (`logo_ground: dark`) sits on the dark plate. Never a product photo in its place.
- The name in Spectral follows. With a documented primary brand (`display_name()`), the brand leads and the registered legal name sits directly beneath it in `<small>`, footnoted to the brand's source (here trademark RU1125967). Without one, the legal name leads with its English gloss. The legal name is never hidden: sanctions lists name the company, not the brand.
- `.hub` is for ЦБСТ only: a 2px ink border. There is no hub colour.
- `.absent` is a dashed card with no shadow, for something a reader would expect that is not there.
- Rows are `p` elements at the note size; each claim ends in a `rm-ref` footnote.
- The consumer supplies the `id` that the chain's lines attach to.
