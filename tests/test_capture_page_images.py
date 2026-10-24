"""capture_page_images.plan_images: order, roles, captions and chapters, with thumbnails and icons left out."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import capture_page_images as c  # noqa: E402

HTML = """
<p class="post__heading">первая глава</p>
<p class="post__text">Текст перед картинкой.</p>
<figure class="post__image-block"><img class="post__image" data-src="https://h.example/media/cache/aa/bb/one.jpg" width="700" height="400" src="">
<figcaption>Выписка из Росреестра</figcaption></figure>
<figure class="post__reference-block"><p>not a picture</p></figure>
<div class="post__gallery-photos"><a data-thumb="https://h.example/media/cache/cc/dd/thumb.jpg" href="https://h.example/media/cache/cc/dd/full.jpg"></a></div>
<p class="post__heading">вторая глава</p>
<figure class="post__image-block"><img class="post__image" data-src="https://h.example/media/cache/aa/bb/one.jpg" src=""></figure>
<figure class="post__image-block"><img class="post__image" data-src="https://other.example/media/cache/zz/two.jpg" src=""></figure>
<img src="https://h.example/static/favicon.png">
"""


def test_roles_order_captions_chapters():
    rows = c.plan_images(HTML)
    assert [(r["role"], r["url"].rsplit("/", 1)[1]) for r in rows] == [
        ("content", "one.jpg"), ("gallery_full", "full.jpg"), ("content", "two.jpg")]
    assert rows[0]["caption"] == "Выписка из Росреестра" and rows[0]["chapter"] == "первая глава"
    assert rows[0]["before"] == "Текст перед картинкой." and rows[0]["width"] == "700"
    assert rows[2]["chapter"] == "вторая глава"
    assert [r["n"] for r in rows] == [1, 2, 3]


def test_host_filter_and_duplicates():
    rows = c.plan_images(HTML, host="h.example")
    assert [r["url"].rsplit("/", 1)[1] for r in rows] == ["one.jpg", "full.jpg"]


if __name__ == "__main__":
    test_roles_order_captions_chapters()
    test_host_filter_and_duplicates()
    print("ok")
