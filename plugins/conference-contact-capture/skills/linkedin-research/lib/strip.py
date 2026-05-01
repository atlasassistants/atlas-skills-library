"""Medium-strip cleaning of LinkedIn page text dumps.

Removes LinkedIn page chrome (button labels, sidebars, footer, dedup'd headers)
while preserving useful content (post text, experience, education, engagement counts).
"""

import re

BUTTON_LABELS = {
    "Connect", "Follow", "Message", "Send",
    "View my newsletter", "Visit my website",
    "Show more", "More", "Like", "Comment", "Repost",
}

DEGREE_MARKER_RE = re.compile(r"^·\s*(1st|2nd|3rd\+?|Premium|Influencer)\s*$", re.IGNORECASE)

NOISE_PATTERNS = [
    re.compile(r"^Activate to view larger image,?\s*$"),
    re.compile(r"^Loaded \d+ Posts? posts?\s*$"),
    re.compile(r"^Feed post number \d+\s*$"),
    re.compile(r"\{:[a-zA-Z]+\}"),  # unrendered Mustache template tokens (e.g. "Subscribe to {:entityName}")
]

# Rule 1: short-form post age followed by separator bullet, e.g. "38m ·",
# "5d •", "3mo · ", "2w •", "1y •", "2yr • ". Handles both U+00B7 and U+2022.
SHORT_POST_AGE_RE = re.compile(r"^\d+(?:m|h|d|w|mo|y|yr)\s*[·•]\s*$", re.IGNORECASE)

# Rule 3: video player UI lines.
VIDEO_UI_EXACT = {
    "Pause", "Play", "Mute", "Unmute",
    "Playback speed", "Turn closed captions on", "Turn closed captions off",
    "Turn fullscreen on", "Turn fullscreen off",
    "Remaining time",
}
VIDEO_UI_PATTERNS = [
    re.compile(r"^Loaded:\s*\d+(?:\.\d+)?%\s*$"),
    re.compile(r"^\d+:\d+\s*$"),                  # 1:11, 0:23, 12:45
    re.compile(r"^\d+(?:\.\d+)?x\s*$"),            # 1x, 0.5x, 1.5x, 2x
]

# Rule 4: engagement counts. Standalone integer (with optional thousands commas)
# OR "<n> comments|reposts|likes".
ENGAGEMENT_NUMERIC_RE = re.compile(r"^\d{1,3}(?:,\d{3})*\s*$")
ENGAGEMENT_LABEL_RE = re.compile(
    r"^\d{1,3}(?:,\d{3})*\s+(?:comments?|reposts?|likes?)\s*$",
    re.IGNORECASE,
)

# Rule 5: activity tab chrome — when this exact 6-line block appears
# consecutively, drop the whole block.
ACTIVITY_TAB_BLOCK = ("All activity", "Posts", "Comments", "Images", "Articles", "More")

SECTION_HEADERS_TO_REMOVE = (
    "People who follow",
    "People also viewed",
    "More profiles for you",
    "Profile enhanced with Premium",
    "Explore Premium profiles",
    "Recommended Content",
    "Manage your account and privacy",
    # Sidebar widgets that surface on sparse profiles (3rd+, students,
    # no work history). Each can leak suggested page/person content into
    # Profile main / Experience / Education when the page chrome is wider
    # than the actual profile content. "Show all" is the trailing button
    # of these widgets — when it appears standalone it always introduces
    # (or trails) sidebar suggestions, so treat it as a sidebar trigger.
    "Show all",
    "Pages you may like",
    "Pages people you follow",
    "People you may know",
    "Suggested companies",
    "Companies you may want to follow",
    "Suggested for you",
    "Premium profiles",
)

SECTION_SKIP_LINES = 30

# Markdown body sections where sidebar suggestions can leak when the section
# itself is empty. We scrub these of orphan name/About fragments after the
# main pass.
SPARSE_SECTION_HEADERS = ("## Experience", "## Education", "## Skills")

# Language picker entries leak as a list of native-script names with the
# English language in parentheses, e.g. "Norsk (Norwegian)", "Tagalog (Tagalog)",
# "简体中文 (Chinese (Simplified))". The trailing parenthetical English language
# label is the stable signal — and the list of recognised languages is finite.
# This pattern is a safety net for cases where the surrounding "Select
# language" / "Visit our Help Center" markers don't appear.
_LANGUAGE_NAMES = (
    "Arabic", "Bangla", "Bulgarian", "Catalan", "Chinese", "Croatian", "Czech",
    "Danish", "Dutch", "English", "Estonian", "Filipino", "Finnish", "French",
    "German", "Greek", "Gujarati", "Hebrew", "Hindi", "Hungarian", "Indonesian",
    "Italian", "Japanese", "Kannada", "Korean", "Latvian", "Lithuanian",
    "Malay", "Malayalam", "Marathi", "Norwegian", "Polish", "Portuguese",
    "Punjabi", "Romanian", "Russian", "Serbian", "Slovak", "Slovenian",
    "Spanish", "Swedish", "Tagalog", "Tamil", "Telugu", "Thai", "Turkish",
    "Ukrainian", "Vietnamese",
)
_LANGUAGE_ENTRY_RE = re.compile(
    r"\((?:" + "|".join(_LANGUAGE_NAMES) + r")(?:\s*\([^)]+\))?\)\s*$"
)

# Sidebar suggestion-card follower counts (e.g. "9,813 followers") leak into
# Profile main on sparse profiles. The profile owner's own follower count
# also matches this regex, so the rule has to be section-aware: keep the
# FIRST occurrence inside ## Profile main, drop subsequent ones plus the
# 1–2 non-blank lines immediately preceding (those are the page name and
# its industry label).
_FOLLOWERS_LINE_RE = re.compile(r"^\d{1,3}(?:,\d{3})*\s+followers?\s*$", re.IGNORECASE)

# A "looks substantive" line: contains 4 consecutive digits (e.g. a date),
# has a company-like word (Inc, LLC, Ltd, University, College, School),
# or is reasonably long prose (>= 60 chars, more than just a name).
_YEAR_RE = re.compile(r"\b\d{4}\b")
_ORG_TOKEN_RE = re.compile(
    r"\b(Inc|LLC|Ltd|Limited|Corp|Corporation|GmbH|Co\.|University|College|School|Institute|Academy|Pte)\b",
    re.IGNORECASE,
)

TAIL_DROP_MARKERS = (
    "Select language",
    "© 20",  # matches © 2024, 2025, 2026, etc.
    # On sparse profiles the language picker leaks into Profile main with no
    # "Select language" header — instead it follows a "Visit our Help Center."
    # link. Treat that link as a tail-drop trigger so the picker (and any
    # downstream chrome) is dropped until the next markdown section header.
    "Visit our Help Center",
    "Visit help center",
)
TAIL_DROP_BLOCK_HEADERS = (
    "Accessibility",
    "Talent Solutions",
    "Community Guidelines",
)


def strip_dossier_text(text: str) -> str:
    """Apply medium-strip cleaning to a single LinkedIn page text dump."""
    lines = text.split("\n")
    filtered = []
    skip_until = -1
    in_tail_block = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # When inside a footer/language-picker tail block, skip until a
        # markdown section header (## ...) signals real content resumed.
        # If no such header appears, the rest of the file is dropped.
        if in_tail_block:
            if stripped.startswith("## "):
                in_tail_block = False
                filtered.append(line)
            continue

        if i < skip_until:
            continue

        if any(m in stripped for m in TAIL_DROP_MARKERS):
            in_tail_block = True
            continue
        if stripped in TAIL_DROP_BLOCK_HEADERS:
            in_tail_block = True
            continue

        if any(stripped.startswith(h) for h in SECTION_HEADERS_TO_REMOVE):
            skip_until = i + SECTION_SKIP_LINES + 1
            continue

        # Rule 5: drop the activity-tab chrome block when seen consecutively.
        if stripped == ACTIVITY_TAB_BLOCK[0]:
            window = [lines[j].strip() for j in range(i, min(i + len(ACTIVITY_TAB_BLOCK), len(lines)))]
            if window == list(ACTIVITY_TAB_BLOCK):
                skip_until = i + len(ACTIVITY_TAB_BLOCK)
                continue

        if stripped in BUTTON_LABELS:
            continue
        if stripped == "·":
            continue
        if DEGREE_MARKER_RE.match(stripped):
            continue
        if any(p.match(stripped) for p in NOISE_PATTERNS):
            continue

        # Rule 1: drop duplicated short-form post age ("38m ·", "3mo •", "2yr •").
        if SHORT_POST_AGE_RE.match(stripped):
            continue

        # Rule 2: drop the visibility suffix line. Keep the time-ago portion by
        # rewriting; if the line ends with "Visible to anyone on or off LinkedIn",
        # strip that suffix (and the preceding " · " / " • " separator).
        if "Visible to anyone on or off LinkedIn" in stripped:
            cleaned = re.sub(
                r"\s*[·•]\s*Visible to anyone on or off LinkedIn\s*$",
                "",
                stripped,
            )
            if cleaned == stripped:
                # No separator before the phrase — drop the entire line.
                continue
            if not cleaned:
                continue
            filtered.append(cleaned)
            continue

        # Rule 3: drop video player UI text.
        if stripped in VIDEO_UI_EXACT:
            continue
        if any(p.match(stripped) for p in VIDEO_UI_PATTERNS):
            continue

        # Rule 4: drop engagement counts (standalone numeric & "<n> comments").
        if ENGAGEMENT_NUMERIC_RE.match(stripped):
            continue
        if ENGAGEMENT_LABEL_RE.match(stripped):
            continue

        # Rule 6: drop language-picker entries by their parenthetical English
        # language label. Defensive — TAIL_DROP_MARKERS usually catches the
        # whole block, but sparse profiles can render the picker without
        # either of those markers.
        if _LANGUAGE_ENTRY_RE.search(stripped):
            continue

        filtered.append(line)

    # Dedupe consecutive identical lines
    out = []
    prev = None
    for line in filtered:
        if line.strip() and line == prev:
            continue
        out.append(line)
        prev = line

    # Second pass: scrub sparse markdown sections (## Experience / ## Education
    # / ## Skills) where the only remaining content is sidebar leak — short
    # orphan name lines and bare "About" links from suggestion cards. We keep
    # the heading but drop the leaked body when the section has no substantive
    # signals (years, organisation tokens, long prose, follower counts of the
    # profile owner's own employer).
    out = _scrub_sparse_sections(out)

    # Third pass: scrub the ## Profile main section of "Pages you may like"
    # sidebar leaks. These cards render as
    #   <stranger headline / page name>
    #   <optional industry label>
    #   <N,NNN followers>
    # The profile owner's own follower count appears once near the top of the
    # section, so we keep the FIRST followers line and drop all subsequent
    # ones plus the 1–2 non-blank lines preceding each one (the page name and
    # its industry label).
    out = _scrub_profile_main_sidebar_cards(out)

    return "\n".join(out)


def _scrub_sparse_sections(lines: list[str]) -> list[str]:
    """Within Experience / Education / Skills body sections, drop sidebar-leak
    fragments — short orphan name lines and bare "About" sidebar-card links —
    that would otherwise be presented to the reader as if they were the
    profile owner's experience or education. Substantive content (years,
    organisation tokens, long prose) is preserved."""
    result: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        if stripped in SPARSE_SECTION_HEADERS:
            # Slice the section and scrub it
            j = i + 1
            while j < n and not lines[j].strip().startswith("## "):
                j += 1
            result.append(line)
            result.extend(_scrub_section_body(lines[i + 1:j]))
            i = j
            continue
        result.append(line)
        i += 1
    return result


def _scrub_section_body(body: list[str]) -> list[str]:
    """Remove orphan name + 'About' sidebar fragments from a section body.

    A line is dropped when it's:
      - a bare "About" link (not part of a paragraph, just the sidebar-card link), OR
      - a short orphan name-shaped line that is NOT adjacent to a substantive
        line (year, organisation token, long prose) on either side.
    """
    # Pre-compute which body lines are "substantive" (anchor real entries).
    substantive = [_is_substantive(s.strip()) for s in body]

    out: list[str] = []
    for idx, raw in enumerate(body):
        s = raw.strip()
        if s == "About":
            # Bare "About" lines inside Experience/Education are sidebar-card
            # link text, not real content. The legitimate profile "About"
            # section sits in Profile main and survives as a section header
            # there.
            continue
        # A line that's itself substantive (org/year/long prose) is never
        # treated as a stray name to drop, even if it happens to match the
        # name-shape regex (e.g. "Ateneo de Manila University").
        if (
            not substantive[idx]
            and _looks_like_orphan_name(s)
            and not _has_substantive_neighbour(substantive, idx, body)
        ):
            continue
        out.append(raw)
    return out


def _is_substantive(s: str) -> bool:
    if not s:
        return False
    if s in {"Experience", "Education", "Skills", "About"}:
        return False
    if _YEAR_RE.search(s):
        return True
    if _ORG_TOKEN_RE.search(s):
        return True
    if len(s) >= 60:
        return True
    return False


# A name-shaped line: 1–4 short words, mostly capitalised, optionally ending
# in a period, no descriptive punctuation. Examples: "Rebecca O.", "John Smith".
_NAME_SHAPED_RE = re.compile(r"^[A-Z][A-Za-z'’\-\.]{0,30}(?:\s+[A-Za-z'’\-\.]{1,30}){0,3}\s*$")


def _looks_like_orphan_name(s: str) -> bool:
    if not s or len(s) > 50:
        return False
    if not _NAME_SHAPED_RE.match(s):
        return False
    # Must have at least one capitalised word
    return any(w[:1].isupper() for w in s.split())


def _scrub_profile_main_sidebar_cards(lines: list[str]) -> list[str]:
    """Drop sidebar 'Pages you may like' / 'People you may know' suggestion
    cards that leak into the ## Profile main section without any explicit
    header. Each card is anchored by an N,NNN followers line; we keep the
    first followers line in the section (the profile owner's own count) and
    drop subsequent ones plus the 1–2 non-blank lines preceding each.

    A blank-line-separated 'orphan headline' that immediately precedes the
    first dropped card (with no follower count of its own — e.g. "Aspiring
    Applied Physicist...") is also dropped: it's the headline of an
    earlier card whose follower count fell to a different rule, or a
    standalone 'People you may know' headline.
    """
    # Locate the ## Profile main section.
    start = None
    for i, line in enumerate(lines):
        if line.strip() == "## Profile main":
            start = i + 1
            break
    if start is None:
        return lines

    end = len(lines)
    for i in range(start, len(lines)):
        if lines[i].strip().startswith("## "):
            end = i
            break

    body = lines[start:end]
    follower_indices = [
        idx for idx, raw in enumerate(body)
        if _FOLLOWERS_LINE_RE.match(raw.strip())
    ]
    if len(follower_indices) <= 1:
        return lines  # No sidebar follower-card leaks to scrub.

    drop = set()
    # Keep the first followers line (profile owner's). Drop each subsequent
    # one and the 1–2 non-blank lines immediately preceding it.
    earliest_dropped = None
    for fi in follower_indices[1:]:
        drop.add(fi)
        # Walk backward, drop up to 2 non-blank lines, stop at blank or
        # at an already-dropped index.
        dropped_before = 0
        k = fi - 1
        while k >= 0 and dropped_before < 2:
            if k in drop:
                k -= 1
                continue
            if not body[k].strip():
                k -= 1
                continue  # blank lines are skipped over but don't count
            drop.add(k)
            dropped_before += 1
            if earliest_dropped is None or k < earliest_dropped:
                earliest_dropped = k
            k -= 1
        if earliest_dropped is None or fi < earliest_dropped:
            earliest_dropped = fi

    # Also drop any non-blank line that sits immediately before the earliest
    # dropped block (separated only by blank lines) — that's typically the
    # leading sidebar headline ("Aspiring Applied Physicist..." for People
    # you may know cards) whose own follower line was missing.
    if earliest_dropped is not None:
        k = earliest_dropped - 1
        while k >= 0 and not body[k].strip():
            k -= 1
        if k >= 0:
            s = body[k].strip()
            # Only drop if it doesn't look like profile-owner content. Skip
            # known profile-main labels and any line followed by structural
            # content (markdown header). "Recent posts ... will be displayed
            # here." and "<Name> has no recent posts" are both legitimate
            # profile-empty-state lines and stay.
            if (
                s
                and "has no recent posts" not in s
                and "will be displayed here" not in s
                and not s.startswith("## ")
                and not s.startswith("# ")
                and s not in {"About", "Activity", "Contact info", "Experience", "Education"}
                and not _FOLLOWERS_LINE_RE.match(s)
            ):
                drop.add(k)

    new_body = [raw for idx, raw in enumerate(body) if idx not in drop]
    return lines[:start] + new_body + lines[end:]


def _has_substantive_neighbour(substantive: list[bool], idx: int, body: list[str]) -> bool:
    """Return True if a substantive line sits in the same content block as
    idx — i.e. reachable from idx without crossing a blank line. A blank line
    in the section body is treated as an entry boundary, so a sidebar-leak
    name that's separated from the real entry by a blank line is correctly
    flagged as an orphan, while a name that's contiguous with company/title/
    year lines is preserved as part of the real entry."""
    # Scan upward, stop at blank line
    k = idx - 1
    while k >= 0 and body[k].strip():
        if substantive[k]:
            return True
        k -= 1
    # Scan downward, stop at blank line
    k = idx + 1
    while k < len(body) and body[k].strip():
        if substantive[k]:
            return True
        k += 1
    return False
