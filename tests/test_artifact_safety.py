"""XSS / artifact-rendering safety tests.

Exercises the real `sanitize_if_html` pipeline (bleach, whitelist-based)
used by src/routers/artifacts.py, rather than asserting against inert
string literals. The requirement (task.md #4.3 / PRD): generated HTML is
untrusted input, and only a fixed whitelist of formatting tags may reach
the browser's dangerouslySetInnerHTML on the frontend.
"""

import pytest

from src.routers.artifacts import ALLOWED_ATTRIBUTES, ALLOWED_TAGS, sanitize_if_html


def test_script_tag_is_stripped():
    dirty = "<p>Hello</p><script>alert('xss')</script>"
    clean = sanitize_if_html("html", dirty)
    assert "<script" not in clean
    assert "</script>" not in clean
    assert "<p>Hello</p>" in clean


def test_script_tag_case_and_attribute_variants_are_stripped():
    variants = [
        "<SCRIPT>alert(1)</SCRIPT>",
        "<ScRiPt src='evil.js'></ScRiPt>",
        "<script type='text/javascript'>alert(1)</script>",
    ]
    for dirty in variants:
        clean = sanitize_if_html("html", dirty)
        assert "<script" not in clean.lower()


def test_event_handler_attributes_are_stripped():
    dirty = "<p onclick=\"alert('xss')\" onmouseover=\"evil()\">Click me</p>"
    clean = sanitize_if_html("html", dirty)
    assert "onclick" not in clean
    assert "onmouseover" not in clean
    assert "<p>Click me</p>" == clean


def test_img_onerror_payload_is_stripped_entirely():
    """<img> isn't in the whitelist at all, so the whole tag (and its
    onerror payload) must disappear, not just the handler."""
    dirty = "<img src=x onerror=\"alert('xss')\">"
    clean = sanitize_if_html("html", dirty)
    assert "onerror" not in clean
    assert "<img" not in clean


def test_iframe_is_blocked():
    dirty = "<p>Before</p><iframe src=\"https://evil.com\"></iframe><p>After</p>"
    clean = sanitize_if_html("html", dirty)
    assert "<iframe" not in clean
    assert "<p>Before</p>" in clean
    assert "<p>After</p>" in clean


def test_object_and_embed_tags_are_blocked():
    for dirty in ['<object data="evil.swf"></object>', '<embed src="evil.swf">']:
        clean = sanitize_if_html("html", dirty)
        assert "<object" not in clean
        assert "<embed" not in clean


def test_svg_onload_payload_is_stripped():
    dirty = "<svg onload=\"alert(1)\"><p>caption</p></svg>"
    clean = sanitize_if_html("html", dirty)
    assert "onload" not in clean
    assert "<svg" not in clean
    assert "<p>caption</p>" in clean


def test_javascript_href_scheme_is_neutralized():
    dirty = "<a href=\"javascript:alert('xss')\">click</a>"
    clean = sanitize_if_html("html", dirty)
    assert "javascript:" not in clean
    assert "<a>click</a>" == clean


def test_data_uri_html_href_is_neutralized():
    dirty = '<a href="data:text/html,<script>alert(1)</script>">click</a>'
    clean = sanitize_if_html("html", dirty)
    assert "data:text/html" not in clean
    assert "<script>" not in clean


def test_style_tag_is_removed_leaving_inert_text():
    """<style> is stripped as a tag; any leftover CSS text is inert
    (rendered as plain text, not interpreted), so no executable payload survives."""
    dirty = "<style>body{background:url(javascript:alert(1))}</style><p>ok</p>"
    clean = sanitize_if_html("html", dirty)
    assert "<style" not in clean
    assert "<p>ok</p>" in clean


def test_allowed_tags_and_href_attribute_are_preserved():
    content = (
        "<h2>Title</h2><p>Content <strong>bold</strong> and <em>emphasis</em></p>"
        "<ul><li>one</li><li>two</li></ul>"
        "<blockquote>quoted</blockquote>"
        "<a href=\"https://example.com\">safe link</a>"
        "<code>inline_code()</code><pre>block code</pre>"
    )
    clean = sanitize_if_html("html", content)
    assert clean == content  # nothing in the whitelist should be touched


def test_only_href_attribute_survives_on_anchor_tags():
    dirty = '<a href="https://example.com" target="_blank" onclick="evil()" style="color:red">link</a>'
    clean = sanitize_if_html("html", dirty)
    assert clean == '<a href="https://example.com">link</a>'


def test_disallowed_tags_not_in_whitelist():
    """Sanity check the whitelist itself: nothing dangerous is accidentally allowed."""
    dangerous = {"script", "iframe", "object", "embed", "svg", "style", "img", "form", "input"}
    assert dangerous.isdisjoint(set(ALLOWED_TAGS))
    assert ALLOWED_ATTRIBUTES == {"a": ["href"]}


def test_markdown_type_passes_through_untouched():
    """Markdown artifacts are never run through the HTML sanitizer - they're
    rendered via react-markdown on the frontend, which doesn't execute raw HTML."""
    raw = "<script>alert(1)</script> ## Heading\n\nSome **bold** text."
    assert sanitize_if_html("markdown", raw) == raw
