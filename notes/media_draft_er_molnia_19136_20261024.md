# Media record waiting for a source id: ER video frame, Скворец (24.10.2026)

The screenshot is held as `data/sources/TGMEDIA_20260807_er_molnia-post19136-frame0m44s-screenshot.png` (sha256 a678fa7320bbf3d7bcb5a55c901f647cd613502abfc0d03fa43c5c7ccb1acbd7), taken from the full video `TGMEDIA_20260807_er_molnia-post19136-media.mp4`. `media.json` needs `source_id` of the post the picture came from (https://t.me/er_molnia/19136), which is not catalogued here, so the record below is not added yet. Add it as the next `m` id once the post has a source id (archive Mac, brief b018); it is ready except for `id` and `source_id`. `deliveries.json` events h0032 and h0033 already carry the item and point at the screenshot file.

```json
{
 "id": "m00XX",
 "kind": "still",
 "genre": "handover",
 "shows": "Кадр из видео United Russia (ER.RU) о передаче помощи в ДНР, около 0:44: в открытом деревянном ящике на пенопластовых вкладышах лежит чёрный дрон с аккумулятором; на этикетке аккумулятора напечатано «СКВОРЕЦ». Субтитр: «наши инновационные «Скворцы» ударные и гексакоптеры». В углу логотип ER.RU и подпись «Донецкая Народная Республика». Скриншот сделан пользователем, без пометок.",
 "shows_en": "Frame from a United Russia (ER.RU) video about an aid handover in the DNR, about 0:44: in an open wooden crate, on foam inserts, lies a black drone with a battery pack whose label is printed “SKVORETS”. The subtitle reads “our innovative ‘Skvortsy’, strike drones and hexacopters”. The ER.RU logo and a “Donetsk People's Republic” tag are in the corners. Screenshot taken by the user, unannotated.",
 "about": [
  {
   "type": "delivery",
   "id": "h0032"
  },
  {
   "type": "delivery",
   "id": "h0033"
  }
 ],
 "asserted_by": "third_party",
 "published": null,
 "captured": "2026-10-24",
 "source_id": "<er_molnia/19136 once catalogued>",
 "original_url": "https://t.me/er_molnia/19136",
 "file": "data/sources/TGMEDIA_20260807_er_molnia-post19136-frame0m44s-screenshot.png",
 "publish": "internal",
 "redact": "none_needed",
 "frame": {
  "t": "0:44"
 },
 "video": {
  "original": "https://t.me/er_molnia/19136",
  "archived": false
 },
 "note": "Linked from Наша Правда post 656 (10.08.2026). Source id not assigned on this machine; the Telegram post is not catalogued. The full video is held locally as TGMEDIA_20260807_er_molnia-post19136-media.mp4 (sha256 4e0f3d2a2b9054beb7d7db240105992e76ad9c8d107e4abd97212bb872b82ecc), not yet RFC 3161 stamped. The brand «СКВОРЕЦ» is on the battery label and in the subtitle; the frame does not show which company made or packed it. No face is in the frame."
}
```
