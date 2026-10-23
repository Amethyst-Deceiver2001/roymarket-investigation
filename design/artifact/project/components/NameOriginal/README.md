# NameOriginal

A name in running text, Latin or English first, with its original one tap away (STYLE_GUIDE §2.2-2.3a).

- `display_helpers.name_html()` renders it: the visible name, a small RU control, and a native `popover` holding the Cyrillic form and, for a translated state body, its sanctions-style transliteration. Each line has a Copy button (`NAME_JS`); where the clipboard is refused the text is selected instead.
- Not `title=`: a tooltip does not work on touch screens, is unreliable in screen readers and cannot be copied.
- People get no popover: the first mention carries the full ФИО in brackets, later mentions the surname only.
- Ukrainian places are written in Ukrainian-based spelling with no popover.
- Use it on first mention only; cards show the Cyrillic on the line beneath instead.
