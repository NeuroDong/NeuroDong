#!/usr/bin/env python3
"""Generate a GitHub stats SVG card using the GitHub API."""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

USERNAME = "NeuroDong"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "readme-stats-generator",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def api_request(url):
    """Make a GitHub API request with pagination support."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code} for {url}: {e.reason}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return None


def api_request_paginated(url):
    """Fetch all pages from a paginated GitHub API endpoint."""
    results = []
    page = 1
    while True:
        paged_url = f"{url}{'&' if '?' in url else '?'}page={page}&per_page=100"
        req = urllib.request.Request(paged_url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                if not data:
                    break
                results.extend(data)
                # Check if there are more pages via Link header
                link = resp.headers.get("Link", "")
                if 'rel="next"' not in link:
                    break
                page += 1
        except urllib.error.HTTPError as e:
            print(f"HTTP Error {e.code} for {paged_url}: {e.reason}", file=sys.stderr)
            break
        except Exception as e:
            print(f"Error fetching {paged_url}: {e}", file=sys.stderr)
            break
    return results


def format_number(n):
    """Format large numbers with k/m suffixes."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}m"
    elif n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def escape_xml(s):
    """Escape special XML characters."""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def generate_svg(stats):
    """Generate an SVG stats card."""
    username = escape_xml(stats["username"])
    stars = format_number(stats["total_stars"])
    commits = format_number(stats.get("total_commits", 0))
    prs = format_number(stats.get("total_prs", 0))
    issues = format_number(stats.get("total_issues", 0))
    repos = format_number(stats["public_repos"])
    followers = format_number(stats["followers"])
    contribs = format_number(stats.get("total_contributions", 0))

    card_width = 500
    card_height = 200
    bg_color = "#ffffff"
    border_color = "#e4e2e2"
    title_color = "#2f80ed"
    text_color = "#434d58"
    icon_color = "#858585"
    label_color = "#555"
    accent_color = "#2f80ed"

    # Icon paths (simple SVG paths for each stat type)
    icons = {
        "star": '<path d="M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.75.75 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25z"/>',
        "commit": '<path d="M1.75 8a6.25 6.25 0 1 1 12.5 0A6.25 6.25 0 0 1 1.75 8zM8 12.75a4.75 4.75 0 1 0 0-9.5 4.75 4.75 0 0 0 0 9.5z"/><path d="M8 4.5a.75.75 0 0 1 .75.75v2h2a.75.75 0 0 1 0 1.5h-2v2a.75.75 0 0 1-1.5 0v-2h-2a.75.75 0 0 1 0-1.5h2v-2A.75.75 0 0 1 8 4.5z"/>',
        "pr": '<path d="M1.5 3.25a2.25 2.25 0 1 1 3 2.122v5.256a2.251 2.251 0 1 1-1.5 0V5.372A2.25 2.25 0 0 1 1.5 3.25zm5.677-.177L9.573.677A.25.25 0 0 1 10 .854V2.5h1A2.5 2.5 0 0 1 13.5 5v5.628a2.251 2.251 0 1 1-1.5 0V5a1 1 0 0 0-1-1h-1v1.646a.25.25 0 0 1-.427.177L7.177 3.427a.25.25 0 0 1 0-.354z"/>',
        "issue": '<path d="M8 1.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13zM0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8zm9 3a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm-.25-6.25a.75.75 0 0 0-1.5 0v3.5a.75.75 0 0 0 1.5 0v-3.5z"/>',
        "repo": '<path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8.5V1.5z"/>',
        "people": '<path d="M3.5 3.25a2.25 2.25 0 1 1 3 2.122v1.44a4.364 4.364 0 0 0-3 1.124.5.5 0 0 1-.5-.866 2.251 2.251 0 0 1-.5-2.698A1.74 1.74 0 0 1 3.5 3.25zm7.5 0a2.25 2.25 0 1 1-3 2.122v1.44a4.364 4.364 0 0 1 3 1.124.5.5 0 0 0 .5-.866 2.251 2.251 0 0 0 .5-2.698A1.74 1.74 0 0 0 11 3.25zm2 0h.002zM5.875 9.813A3.126 3.126 0 0 1 8 9h.25a.75.75 0 0 1 0 1.5H8a1.625 1.625 0 0 0-1.596 1.358.75.75 0 0 1-1.486-.204 3.124 3.124 0 0 1 .957-1.841zM12 9a3.126 3.126 0 0 0-2.125.813 3.124 3.124 0 0 1 .957 1.841.75.75 0 0 1-1.486.204A1.625 1.625 0 0 0 7.75 10.5H8a.75.75 0 0 1 0-1.5h.25A3.125 3.125 0 0 1 12 9z"/>',
    }

    # Stats to display: (icon_key, label, value)
    stat_items = [
        ("star", "Total Stars", stars),
        ("people", "Followers", followers),
        ("repo", "Public Repos", repos),
    ]
    if commits != "0":
        stat_items.append(("commit", "Commits (2025)", commits))

    # Build SVG
    svg_parts = []
    svg_parts.append(
        f'<svg width="{card_width}" height="{card_height}" viewBox="0 0 {card_width} {card_height}" '
        f'fill="none" xmlns="http://www.w3.org/2000/svg">'
    )
    # Background
    svg_parts.append(
        f'<rect x="0.5" y="0.5" width="{card_width - 1}" height="{card_height - 1}" '
        f'rx="4.5" fill="{bg_color}" stroke="{border_color}"/>'
    )

    # Title
    svg_parts.append(
        f'<text x="25" y="40" font-family="Segoe UI, Ubuntu, Sans-Serif" '
        f'font-size="18" font-weight="700" fill="{title_color}">'
        f"{username}&#39;s GitHub Stats</text>"
    )
    svg_parts.append(
        f'<line x1="25" y1="52" x2="{card_width - 25}" y2="52" '
        f'stroke="{border_color}" stroke-width="1"/>'
    )

    # Stat items - arrange in a 3x2 grid
    cols = 3
    start_y = 75
    row_height = 55
    col_width = (card_width - 50) / cols

    for i, (icon_key, label, value) in enumerate(stat_items):
        col = i % cols
        row = i // cols
        x = 25 + col * col_width
        y = start_y + row * row_height

        # Icon background circle
        icon_cx = x + 16
        icon_cy = y + 16
        svg_parts.append(
            f'<circle cx="{icon_cx}" cy="{icon_cy}" r="16" fill="#f0f3f7"/>'
        )
        # Icon
        svg_parts.append(
            f'<g transform="translate({icon_cx - 8}, {icon_cy - 8})" '
            f'fill="{icon_color}">{icons.get(icon_key, icons["star"])}</g>'
        )
        # Value
        svg_parts.append(
            f'<text x="{x + 40}" y="{y + 14}" font-family="Segoe UI, Ubuntu, Sans-Serif" '
            f'font-size="20" font-weight="700" fill="{text_color}">{value}</text>'
        )
        # Label
        svg_parts.append(
            f'<text x="{x + 40}" y="{y + 32}" font-family="Segoe UI, Ubuntu, Sans-Serif" '
            f'font-size="12" font-weight="400" fill="{label_color}">{label}</text>'
        )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def main():
    print(f"Generating stats for {USERNAME}...")

    # Fetch user info
    user = api_request(f"https://api.github.com/users/{USERNAME}")
    if not user:
        print("Failed to fetch user info", file=sys.stderr)
        sys.exit(1)

    # Fetch all repos for the user
    repos = api_request_paginated(f"https://api.github.com/users/{USERNAME}/repos?type=owner")

    total_stars = sum(r.get("stargazers_count", 0) for r in repos)

    # Try to fetch contribution info via events or search
    # For commits, we can use the search API
    total_commits = 0
    commit_search = api_request(
        f"https://api.github.com/search/commits?q=author:{USERNAME}+committer-date:>2025-01-01&per_page=1"
    )
    if commit_search:
        total_commits = commit_search.get("total_count", 0)

    total_prs = 0
    pr_search = api_request(
        f"https://api.github.com/search/issues?q=author:{USERNAME}+type:pr&per_page=1"
    )
    if pr_search:
        total_prs = pr_search.get("total_count", 0)

    total_issues = 0
    issue_search = api_request(
        f"https://api.github.com/search/issues?q=author:{USERNAME}+type:issue&per_page=1"
    )
    if issue_search:
        total_issues = issue_search.get("total_count", 0)

    stats = {
        "username": USERNAME,
        "public_repos": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "total_stars": total_stars,
        "total_commits": total_commits,
        "total_prs": total_prs,
        "total_issues": total_issues,
        "total_contributions": 0,
    }

    print(f"  Public repos: {stats['public_repos']}")
    print(f"  Followers: {stats['followers']}")
    print(f"  Total stars: {stats['total_stars']}")
    print(f"  Total commits (2025): {stats['total_commits']}")
    print(f"  Total PRs: {stats['total_prs']}")
    print(f"  Total issues: {stats['total_issues']}")

    svg = generate_svg(stats)

    output_path = os.environ.get("OUTPUT_PATH", "profile/stats.svg")
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        f.write(svg)
    print(f"SVG saved to {output_path}")


if __name__ == "__main__":
    main()
