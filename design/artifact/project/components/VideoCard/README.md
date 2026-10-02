# VideoCard

A video shown as its poster still plus a line saying where the original is and whether we hold a copy.

- No platform player is embedded (decision 02.10.2026): players track readers, break when a post is deleted, and do not run in Artifacts.
- The play mark is drawn over the poster to say "this is a video", not to play it.
- The line under the caption is the record's `video.original`, followed by "Not archived" when `video.archived` is false.
- Example: the maker's Q&A video thumbnail from its customer chat.
