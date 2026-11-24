#!/usr/bin/env python3
"""
Animated GitHub stats card (stars, commits, PRs, issues, contributions + rank ring).

Environment variables:
  GITHUB_TOKEN   token for the GitHub GraphQL API (provided by Actions)
  GH_USER        GitHub username
  DISPLAY_NAME   name shown in the title (default: the user's profile name)
  OUTPUT         output file (default assets/github-stats.svg)

Flags: --demo (sample numbers), --placeholder (dashes, no API call)
"""
import json, math, os, sys, urllib.request
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape as esc

USER = os.environ.get("GH_USER", "Lanilka2003")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUTPUT = os.environ.get("OUTPUT", "assets/github-stats.svg")
DISPLAY = os.environ.get("DISPLAY_NAME", "")

SANS = "-apple-system, 'Segoe UI', Ubuntu, Helvetica, Arial, sans-serif"
CY, LI, PK, AM, GR = "#67e8f9", "#c4b5fd", "#f9a8d4", "#fcd34d", "#86efac"

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    name
    followers { totalCount }
    pullRequests { totalCount }
    issues { totalCount }
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      restrictedContributionsCount
      totalPullRequestReviewContributions
    }
    repositoriesContributedTo(first: 1, contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, REPOSITORY]) { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) { nodes { stargazerCount } }
  }
}"""


def fetch():
    now = datetime.now(timezone.utc)
    body = json.dumps({"query": QUERY, "variables": {
        "login": USER, "from": (now - timedelta(days=365)).isoformat(), "to": now.isoformat()}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "stats-card"})
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.load(r)
    if "errors" in res:
        raise SystemExit(f"GraphQL error: {res['errors']}")
    u = res["data"]["user"]
    cc = u["contributionsCollection"]
    return dict(
        name=u["name"] or USER,
        stars=sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
        commits=cc["totalCommitContributions"] + cc["restrictedContributionsCount"],
        prs=u["pullRequests"]["totalCount"],
        issues=u["issues"]["totalCount"],
        contributed=u["repositoriesContributedTo"]["totalCount"],
        reviews=cc["totalPullRequestReviewContributions"],
        followers=u["followers"]["totalCount"],
    )


def rank(d):
    """Same idea as github-readme-stats: weighted percentile -> grade."""
    exp_cdf = lambda x: 1 - 2 ** -x
    log_cdf = lambda x: x / (1 + x)
    parts = [(2, exp_cdf(d["commits"] / 250)), (3, exp_cdf(d["prs"] / 50)), (1, exp_cdf(d["issues"] / 25)),
             (1, exp_cdf(d["reviews"] / 2)), (4, log_cdf(d["stars"] / 50)), (1, log_cdf(d["followers"] / 10))]
    pct = (1 - sum(w * v for w, v in parts) / sum(w for w, _ in parts)) * 100
    for t, g in zip([1, 12.5, 25, 37.5, 50, 62.5, 75, 87.5, 100], ["S", "A+", "A", "A-", "B+", "B", "B-", "C+", "C"]):
        if pct <= t:
            return g, pct
    return "C", pct


ICONS = {  # 16x16 octicons
    "star": "M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Zm0 2.445L6.615 5.5a.75.75 0 0 1-.564.41l-3.097.45 2.24 2.184a.75.75 0 0 1 .216.664l-.528 3.084 2.769-1.456a.75.75 0 0 1 .698 0l2.77 1.456-.53-3.084a.75.75 0 0 1 .216-.664l2.24-2.183-3.096-.45a.75.75 0 0 1-.564-.41L8 2.694Z",
    "commit": "M1.643 3.143 .427 1.927A.25.25 0 0 0 0 2.104V5.75c0 .138.112.25.25.25h3.646a.25.25 0 0 0 .177-.427L2.715 4.215a6.5 6.5 0 1 1-1.18 4.458.75.75 0 1 0-1.493.154 8.001 8.001 0 1 0 1.6-5.684ZM7.75 4a.75.75 0 0 1 .75.75v2.992l2.028.812a.75.75 0 0 1-.557 1.392l-2.5-1A.751.751 0 0 1 7 8.25v-3.5A.75.75 0 0 1 7.75 4Z",
    "pr": "M1.5 3.25a2.25 2.25 0 1 1 3 2.122v5.256a2.251 2.251 0 1 1-1.5 0V5.372A2.25 2.25 0 0 1 1.5 3.25Zm5.677-.177L9.573.677A.25.25 0 0 1 10 .854V2.5h1A2.5 2.5 0 0 1 13.5 5v5.628a2.251 2.251 0 1 1-1.5 0V5a1 1 0 0 0-1-1h-1v1.646a.25.25 0 0 1-.427.177L7.177 3.427a.25.25 0 0 1 0-.354ZM3.75 2.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm0 9.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm8.25.75a.75.75 0 1 0 1.5 0 .75.75 0 0 0-1.5 0Z",
    "issue": "M8 9.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Z M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0ZM1.5 8a6.5 6.5 0 1 0 13 0 6.5 6.5 0 0 0-13 0Z",
    "repo": "M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z",
}


def render(d, placeholder=False):
    W, H = 600, 250
    grade, pct = ("—", 100) if placeholder else rank(d)
    v = (lambda k: "—") if placeholder else (lambda k: f"{d[k]:,}")
    name = DISPLAY or d.get("name") or USER
    rows = [("star", "Total Stars Earned:", v("stars"), AM), ("commit", "Total Commits (last year):", v("commits"), CY),
            ("pr", "Total PRs:", v("prs"), LI), ("issue", "Total Issues:", v("issues"), PK),
            ("repo", "Contributed to (last year):", v("contributed"), GR)]
    R = 54
    C = 2 * math.pi * R
    prog = 0 if placeholder else max(0.04, (100 - pct) / 100)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">']
    s.append(f'''<defs>
<linearGradient id="title" gradientUnits="userSpaceOnUse" x1="36" y1="0" x2="420" y2="0" spreadMethod="reflect">
  <stop offset="0" stop-color="{CY}"/><stop offset=".5" stop-color="{LI}"/><stop offset="1" stop-color="{PK}"/>
  <animateTransform attributeName="gradientTransform" type="translate" values="0 0;380 0;0 0" dur="7s" repeatCount="indefinite"/>
</linearGradient>
<linearGradient id="ring" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{CY}"/><stop offset=".5" stop-color="{LI}"/><stop offset="1" stop-color="{PK}"/></linearGradient>
<linearGradient id="border" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{W}" y2="{H}">
  <stop offset="0" stop-color="{CY}"/><stop offset=".33" stop-color="#a78bfa"/><stop offset=".66" stop-color="#f472b6"/><stop offset="1" stop-color="{CY}"/>
  <animateTransform attributeName="gradientTransform" type="rotate" from="0 {W/2} {H/2}" to="360 {W/2} {H/2}" dur="8s" repeatCount="indefinite"/>
</linearGradient>
</defs>
<style>
.title {{ animation: fade .8s ease-in-out backwards; }}
.row {{ animation: slide .4s ease-in-out backwards; }}
@keyframes fade {{ from {{ opacity:0 }} to {{ opacity:1 }} }}
@keyframes slide {{ from {{ opacity:0; transform: translateX(-12px) }} to {{ opacity:1; transform:none }} }}
.grade {{ transform-box: fill-box; transform-origin: center; animation: pop .8s cubic-bezier(.3,1.6,.5,1) 1s backwards; }}
@keyframes pop {{ from {{ opacity:0; transform: scale(.4) }} to {{ opacity:1; transform: scale(1) }} }}
.prog {{ animation: ring 1.4s cubic-bezier(.3,.9,.4,1) .6s backwards; }}
@keyframes ring {{ from {{ stroke-dashoffset: {C:.1f} }} }}
.ic {{ transform-box: fill-box; transform-origin: center; animation: ic 3s ease-in-out infinite; }}
@keyframes ic {{ 0%,100% {{ transform: scale(1) }} 50% {{ transform: scale(1.12) }} }}
.orbit {{ transform-origin: 480px 135px; animation: spin 6s linear infinite; }}
@keyframes spin {{ to {{ transform: rotate(360deg) }} }}
</style>''')
    s.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="#0b0b10"/>')
    s.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="none" stroke="url(#border)" stroke-width="2" opacity=".45"/>')
    s.append(f'<text x="36" y="52" class="title" font-family="{SANS}" font-size="24" font-weight="700" fill="url(#title)">{esc(name)}\'s GitHub Stats</text>')
    for i, (ic, label, val, col) in enumerate(rows):
        y = 92 + i * 32
        s.append(f'<g class="row" style="animation-delay:{0.45 + i*0.15:.2f}s">')
        s.append(f'<g transform="translate(36,{y-13}) scale(1.15)"><path class="ic" style="animation-delay:-{i*0.6:.1f}s" d="{ICONS[ic]}" fill="{col}"/></g>')
        s.append(f'<text x="66" y="{y}" font-family="{SANS}" font-size="16" font-weight="700" fill="#e2e8f0">{label}</text>')
        s.append(f'<text x="300" y="{y}" font-family="{SANS}" font-size="16" font-weight="700" fill="{col}">{val}</text>')
        s.append('</g>')
    cx, cy = 480, 135
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="#ffffff" stroke-opacity=".08" stroke-width="7"/>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="url(#ring)" stroke-width="7" stroke-linecap="round" class="prog" '
             f'stroke-dasharray="{C:.1f}" stroke-dashoffset="{C*(1-prog):.1f}" transform="rotate(-90 {cx} {cy})"/>')
    s.append(f'<g class="orbit"><circle cx="{cx}" cy="{cy-R-12}" r="2.5" fill="{LI}" opacity=".8"/></g>')
    s.append(f'<text x="{cx}" y="{cy+12}" text-anchor="middle" class="grade" font-family="{SANS}" font-size="34" font-weight="800" fill="#e2e8f0">{grade}</text>')
    s.append(f'<text x="{cx}" y="{cy+R+30}" text-anchor="middle" class="title" style="animation-delay:1.2s" font-family="{SANS}" font-size="12" fill="#94a3b8">'
             f'{"run the workflow to load stats" if placeholder else "rank"}</text>')
    s.append('</svg>')
    return "\n".join(s)


def main():
    placeholder = "--placeholder" in sys.argv
    if placeholder:
        d = {"name": DISPLAY or USER}
    elif "--demo" in sys.argv:
        d = dict(name="Lanilka Rathnaweera", stars=4, commits=176, prs=9, issues=3, contributed=4, reviews=1, followers=12)
    else:
        d = fetch()
    os.makedirs(os.path.dirname(OUTPUT) or ".", exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(render(d, placeholder))
    print(f"Stats card written to {OUTPUT}")


if __name__ == "__main__":
    main()
