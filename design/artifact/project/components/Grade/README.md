# Grade

A chip that states how well a claim is documented: Documented, Reported or Not documented.

- Text is always present; the colour repeats it. Never show a grade by colour alone.
- The grade comes from `reader_grade()`, which maps every registry confidence value in one table. A page never picks one.
- The Reported chip uses `g-rep-ink` for its text, because the line amber is under 4.5:1 as small text.
