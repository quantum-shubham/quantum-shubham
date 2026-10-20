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


def render(prs):
    rows = ["| Project | Contribution | Status |", "|:--|:--|:--:|"]
    for pr in prs:
        merged = bool((pr.get("pull_request") or {}).get("merged_at"))
        if pr["state"] == "closed" and not merged:
            continue  # rejected / abandoned PRs are not shown
        repo = pr["repository_url"].split("/repos/", 1)[1]
        # maintainers can rename PRs: neutralise HTML, comment markers and table/link syntax
        title = html.escape(" ".join(pr["title"].split())).translate({ord(c): "\\" + c for c in "|[]"})
        badge = f"https://img.shields.io/github/pulls/detail/state/{repo}/{pr['number']}?style=flat-square&label="
        rows.append(
            f"| [**{repo}**](https://github.com/{repo}) | [{title}]({pr['html_url']}) | <img src=\"{badge}\" /> |"
        )
    return "\n".join(rows)


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
