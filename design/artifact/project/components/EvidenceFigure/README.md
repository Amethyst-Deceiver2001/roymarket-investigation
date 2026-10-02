# EvidenceFigure

One picture as evidence: the image, who published it, what is visible, its date and a footnote.

- The provenance label comes from the media record's `asserted_by`: "Published by ООО «ПОКРОВ»", "Posted by a third party", "From press coverage". It is said in words, never with colour.
- The caption is the record's `shows`: what someone who looked at the picture saw. A picture is evidence only for that.
- The image sits in a 4:3 frame with `object-fit: contain`, so it is never cropped in a way that changes what it shows.
- Records marked `internal` or still awaiting a blur (`blur_pending`) are never rendered (`media_about()`).
- Example: the «Булат» v.4 card on the dealer's own site.
