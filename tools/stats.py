"""Рисует assets/stats.svg в стиле keyf по данным GitHub GraphQL."""
import json, os, sys, urllib.request
from datetime import date

USER = os.environ.get("GH_USER", "rickrollru")
TOKEN = os.environ["GH_TOKEN"]
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "stats.svg")

QUERY = """query($login:String!){user(login:$login){
 followers{totalCount}
 repositories(ownerAffiliations:OWNER,isFork:false,first:100,privacy:PUBLIC){totalCount nodes{stargazerCount
  languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}}
 contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{contributionCount date}}}}}}"""

req = urllib.request.Request("https://api.github.com/graphql",
    data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
    headers={"Authorization": f"bearer {TOKEN}", "User-Agent": "keyf-stats"})
u = json.load(urllib.request.urlopen(req))["data"]["user"]

repos = u["repositories"]["nodes"]
stars = sum(r["stargazerCount"] for r in repos)
langs = {}
for r in repos:
    for e in r["languages"]["edges"]:
        langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
total = sum(langs.values()) or 1
top = sorted(langs.items(), key=lambda x: -x[1])[:5]
cal = u["contributionsCollection"]["contributionCalendar"]
weeks = cal["weeks"][-26:]

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;")

S = []
a = S.append
a('<svg xmlns="http://www.w3.org/2000/svg" width="900" height="300" viewBox="0 0 900 300"><style>'
  '.i{fill:#0a0a0a}.p{fill:#fff}.g{fill:#6b6b6b}.s{stroke:#0a0a0a}.sh{fill:#000;fill-opacity:.4}.dot{fill:#0a0a0a;fill-opacity:.22}'
  '.m{font-family:"JetBrains Mono",ui-monospace,Consolas,"Courier New",monospace}'
  '.t{font-family:"Inter Tight",Inter,"Segoe UI",Helvetica,Arial,sans-serif}'
  '@media (prefers-color-scheme:dark){.i{fill:#f5f5f5}.p{fill:#0d1117}.g{fill:#9a9a9a}.s{stroke:#f5f5f5}.sh{fill:#fff;fill-opacity:.25}.dot{fill:#fff;fill-opacity:.16}}'
  '</style><defs><pattern id="d" width="10" height="10" patternUnits="userSpaceOnUse"><circle class="dot" cx="5" cy="5" r=".9"/></pattern></defs>'
  '<rect class="p" width="900" height="300"/><rect width="900" height="300" fill="url(#d)"/>'
  '<rect class="sh" x="42" y="22" width="816" height="260"/><rect class="p s" x="40.5" y="20.5" width="816" height="260"/>'
  '<rect class="i" x="40" y="20" width="817" height="22"/>'
  f'<text class="p m" x="50" y="35" font-size="12">активность — github.com/{USER}</text>'
  '<text class="p m" x="846" y="35" font-size="12" text-anchor="end" letter-spacing="2">▪▪</text>')

# счётчики
for n, (label, val) in enumerate([("вклад за год", cal["totalContributions"]),
                                  ("репозиториев", u["repositories"]["totalCount"]),
                                  ("звёзд", stars), ("подписчиков", u["followers"]["totalCount"])]):
    x = 62 + n * 100
    a(f'<text class="g m" x="{x}" y="70" font-size="10">▪ {label}</text>'
      f'<text class="i t" x="{x}" y="106" font-size="34" font-weight="600" letter-spacing="-1.5">{val}</text>')

# сетка активности: 26 недель × 7 дней
a('<text class="g m" x="62" y="140" font-size="10">▪ последние полгода</text>')
for wi, w in enumerate(weeks):
    for d in w["contributionDays"]:
        c = d["contributionCount"]
        di = date.fromisoformat(d["date"]).isoweekday() % 7
        x, y = 62 + wi * 14.6, 150 + di * 14.6
        if c == 0:
            a(f'<rect class="p s" x="{x+.5:.1f}" y="{y+.5:.1f}" width="10" height="10" stroke-opacity=".35"/>')
        else:
            op = 0.35 if c < 2 else 0.6 if c < 5 else 0.85 if c < 10 else 1
            a(f'<rect class="i" x="{x:.1f}" y="{y:.1f}" width="11" height="11" fill-opacity="{op}"><title>{d["date"]}: {c}</title></rect>')
a('<text class="g m" x="62" y="272" font-size="10">меньше</text>')
for k, op in enumerate([0, .35, .6, .85, 1]):
    x = 112 + k * 14
    a(f'<rect class="p s" x="{x+.5}" y="263.5" width="10" height="10" stroke-opacity=".35"/>' if op == 0
      else f'<rect class="i" x="{x}" y="263" width="11" height="11" fill-opacity="{op}"/>')
a('<text class="g m" x="190" y="272" font-size="10">больше</text>')

# языки
a('<line class="s" x1="500.5" y1="60" x2="500.5" y2="262" stroke-dasharray="2 3"/>'
  '<text class="g m" x="524" y="70" font-size="10">▪ языки</text>')
for k, (name, size) in enumerate(top):
    y, pct = 96 + k * 34, size / total
    a(f'<text class="i m" x="524" y="{y}" font-size="13">{esc(name)}</text>'
      f'<text class="i m" x="836" y="{y}" font-size="13" text-anchor="end">{pct*100:.1f}%</text>'
      f'<rect class="p s" x="524.5" y="{y+7.5}" width="311" height="8"/>'
      f'<rect class="i" x="524" y="{y+7}" width="{max(2, 312*pct):.1f}" height="9"/>')
if not top:
    a('<text class="g m" x="524" y="96" font-size="13">пока пусто</text>')
a(f'<text class="g m" x="836" y="272" font-size="10" text-anchor="end">обновлено {date.today():%d.%m.%Y}</text></svg>')

open(OUT, "w", encoding="utf-8").write("".join(S))
print("ok", OUT)
