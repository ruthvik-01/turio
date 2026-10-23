"""Read positional text in section-backed columns, without a resume template."""
from app.services.resume_parser import _BULLET_PREFIX, _section_for


def ordered_text(page, fallback):
    words = page.extract_words(x_tolerance=1, y_tolerance=3, keep_blank_chars=False)
    if not words:
        return fallback
    rows = []
    for word in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if not rows or abs(rows[-1][0]["top"] - word["top"]) > 3:
            rows.append([word])
        else:
            rows[-1].append(word)
    lines, gaps = [], []
    for row in rows:
        row.sort(key=lambda w: w["x0"])
        groups = [[]]
        for word in row:
            if groups[-1] and word["x0"] - groups[-1][-1]["x1"] >= max(18, page.width * 0.03):
                gaps.append((groups[-1][-1]["x1"], word["x0"]))
                groups.append([])
            groups[-1].append(word)
        for group in groups:
            lines.append({"text": " ".join(w["text"] for w in group), "x0": group[0]["x0"],
                "x1": group[-1]["x1"], "top": min(w["top"] for w in row),
                "bottom": max(w["bottom"] for w in group)})

    def render(items):
        result, previous = [], None
        for line in sorted(items, key=lambda v: (v["top"], v["x0"])):
            text = line["text"]
            height = max(1, line["bottom"] - line["top"])
            if previous and line["top"] - previous["bottom"] > height * 0.8:
                result.append("")
            # Indented wrap directly following a bullet belongs to that bullet.
            elif previous and result and line["x0"] > previous["x0"] + 2 and not (
                _BULLET_PREFIX.match(text) or _section_for(text)) and _BULLET_PREFIX.match(previous["text"]) and (
                    len(text.split()) > 10 or text.rstrip().endswith((".", ",", "-")) or text[:1].islower()):
                result[-1] += " " + text
                previous = {**line, "text": previous["text"], "x0": previous["x0"]}
                continue
            result.append(text)
            previous = line
        return "\n".join(result)

    def columns(items, depth=0):
        if depth >= 2:
            return render(items)
        candidates = []
        for left_edge, right_edge in gaps:
            cut = (left_edge + right_edge) / 2
            left = [v for v in items if v["x1"] <= cut]
            right = [v for v in items if v["x0"] >= cut]
            # A right-aligned date is not a second column. Both sides must
            # contain independent section headings and source body lines.
            if len(left) < 2 or len(right) < 2 or not all(any(_section_for(v["text"]) for v in side) for side in (left, right)):
                continue
            crossing = [v for v in items if v["x0"] < cut < v["x1"]]
            candidates.append((len(left) + len(right) - 3 * len(crossing), cut))
        if not candidates:
            # Merge aligned segments (e.g. institution and date) back into rows.
            merged = []
            for line in sorted(items, key=lambda v: (v["top"], v["x0"])):
                if merged and abs(merged[-1]["top"] - line["top"]) <= 3:
                    merged[-1] = {**merged[-1], "text": merged[-1]["text"] + " " + line["text"], "x1": line["x1"]}
                else:
                    merged.append(line.copy())
            return render(merged)
        _, cut = max(candidates)
        spanning = sorted((v for v in items if v["x0"] < cut < v["x1"]), key=lambda v: v["top"])
        output, remaining = [], list(items)
        for span in spanning:
            above = [v for v in remaining if v["bottom"] <= span["top"] + 3 and v is not span]
            if above:
                output.extend(columns(side, depth + 1) for side in (
                    [v for v in above if v["x1"] <= cut], [v for v in above if v["x0"] >= cut]) if side)
            output.append(span["text"])
            remaining = [v for v in remaining if v not in above and v is not span]
        output.extend(columns(side, depth + 1) for side in (
            [v for v in remaining if v["x1"] <= cut], [v for v in remaining if v["x0"] >= cut]) if side)
        return "\n\n".join(output)

    return columns(lines)
