"""Rewrite the open-source contributions table in README.md from the GitHub search API."""
import html
import json
import os
import re
import sys
import urllib.request

USER = "quantum-shubham"
README = "README.md"
START, END = "<!-- CONTRIBUTIONS:START -->", "<!-- CONTRIBUTIONS:END -->"


def fetch_prs():
    # shortcut: first 100 results only, paginate once there are more
    url = f"https://api.github.com/search/issues?q=is:pr+author:{USER}+-user:{USER}&sort=created&order=desc&per_page=100"
    headers = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as r:
        return json.load(r)["items"]


def badge(label, value, color, logo):
    return f'<img src="https://img.shields.io/badge/{label}-{value}-{color}?style=for-the-badge&logo={logo}&logoColor=white" />'


def render(prs):
    is_merged = lambda pr: bool((pr.get("pull_request") or {}).get("merged_at"))
    # rejected / abandoned PRs are not shown; merged first, each group newest first
    shown = sorted((pr for pr in prs if pr["state"] == "open" or is_merged(pr)), key=lambda pr: not is_merged(pr))
    repos = [pr["repository_url"].split("/repos/", 1)[1] for pr in shown]
    merged = sum(map(is_merged, shown))
    lines = [
        " ".join([
            badge("Merged_PRs", merged, "8957e5", "git"),
            badge("In_review", len(shown) - merged, "1f6feb", "github"),
            badge("Projects", len(set(repos)), "111111", "opensourceinitiative"),
        ]),
        "",
        "| Project | Contribution | Status |",
        "|:--|:--|:--:|",
    ]
    for pr, repo in zip(shown, repos):
        owner = repo.split("/", 1)[0]
        # maintainers can rename PRs: neutralise HTML, comment markers and table/link syntax
        title = html.escape(" ".join(pr["title"].split())).translate({ord(c): "\\" + c for c in "|[]"})
        status = f"https://img.shields.io/github/pulls/detail/state/{repo}/{pr['number']}?style=flat-square&label="
        lines.append(
            f'| <img src="https://github.com/{owner}.png?size=40" width="20" height="20" /> [**{repo}**](https://github.com/{repo})'
            f' | [{title}]({pr["html_url"]}) | <img src="{status}" /> |'
        )
    return "\n".join(lines)


def update(readme, table):
    pattern = re.compile(re.escape(START) + ".*?" + re.escape(END), re.S)
    if not pattern.search(readme):
        sys.exit(f"markers {START} / {END} not found in {README}")
    return pattern.sub(lambda _: f"{START}\n{table}\n{END}", readme)


if __name__ == "__main__":
    with open(README) as f:
        old = f.read()
    new = update(old, render(fetch_prs()))
    if new != old:
        with open(README, "w") as f:
            f.write(new)
