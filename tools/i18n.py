"""Split an HTML fragment into translatable segments and put translations back.

A segment is a run of text plus inline tags between block-level tags, or the value
of an alt / aria-label attribute. Translations live in src/i18n/vi/<page>.json as
{"English segment": "Vietnamese segment"}; anything missing stays in English.
"""
import re

INLINE = {"a", "strong", "em", "b", "i", "span", "small", "br", "time", "abbr", "sup", "sub", "code", "cite", "q", "u", "mark"}
SKIP = {"svg", "script", "style"}
TOKEN = re.compile(r"(<!--.*?-->|<[^>]+>)", re.S)
LETTER = re.compile(r"[A-Za-zÀ-ỹ]")


def _tagname(tok):
    m = re.match(r"</?\s*([a-zA-Z0-9]+)", tok)
    return m.group(1).lower() if m else ""


def runs(html):
    """Yield (start, end) spans of translatable text runs."""
    parts = TOKEN.split(html)
    pos, run_start, skip, out = 0, None, 0, []
    has_text = False

    def close(at):
        nonlocal run_start, has_text
        if run_start is not None and has_text:
            seg = html[run_start:at]
            # trim surrounding whitespace
            l = len(seg) - len(seg.lstrip()); r = len(seg.rstrip())
            out.append((run_start + l, run_start + r))
        run_start, has_text = None, False

    for p in parts:
        if not p:
            continue
        is_tag = p.startswith("<")
        name = _tagname(p) if is_tag and not p.startswith("<!--") else ""
        if is_tag and name in SKIP:
            close(pos)
            skip += -1 if p.startswith("</") else (0 if p.endswith("/>") else 1)
        elif skip:
            pass
        elif is_tag and (name not in INLINE or p.startswith("<!--")):
            close(pos)
        else:
            if run_start is None:
                run_start = pos
            if not is_tag and LETTER.search(p):
                has_text = True
        pos += len(p)
    close(pos)
    return out


def _trim_edges(seg):
    """Move dangling leading closing tags / trailing opening tags out of a segment."""
    lead = re.match(r"^((?:\s*</[a-z]+>)*\s*)", seg).group(1)
    trail = re.search(r"((?:<[a-z][^>]*>\s*)*)$", seg).group(1)
    core = seg[len(lead):len(seg) - len(trail)] if trail else seg[len(lead):]
    return lead, core, trail


ATTR = re.compile(r'\b(alt|aria-label)="([^"]*[A-Za-zÀ-ỹ][^"]*)"')


def segments(html):
    segs = []
    for a, b in runs(html):
        lead, core, trail = _trim_edges(html[a:b])
        if LETTER.search(re.sub(r"<[^>]+>", "", core)):
            segs.append(core)
    for m in ATTR.finditer(html):
        segs.append(m.group(2))
    seen, uniq = set(), []
    for s in segs:
        if s not in seen:
            seen.add(s); uniq.append(s)
    return uniq


def translate(html, table):
    if not table:
        return html
    pieces, last = [], 0
    for a, b in runs(html):
        lead, core, trail = _trim_edges(html[a:b])
        pieces.append(html[last:a])
        pieces.append(lead + table.get(core, core) + trail)
        last = b
    pieces.append(html[last:])
    out = "".join(pieces)
    return ATTR.sub(lambda m: f'{m.group(1)}="{table.get(m.group(2), m.group(2))}"', out)
