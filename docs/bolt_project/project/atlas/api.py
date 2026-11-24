"""Atlas search API + light dashboard. Binds 127.0.0.1 by default."""
import sqlite3
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from . import config, db, github_verify

app = FastAPI(title="Universal Capability Atlas", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    db.migrate()


VALID_COST = {"oss", "free_api_quota", "free_hosted", "paid", "freemium", "unknown"}
VALID_MAINT = {"active", "stale", "archived", "unknown"}


@app.get("/api/v1/categories")
def categories() -> list[dict[str, Any]]:
    return db.query("SELECT * FROM categories ORDER BY id")


@app.get("/api/v1/entries")
def entries(
    q: str = "",
    category: str = "",
    entry_type: str = "",
    licence: str = "",
    cost: str = "",
    maintenance: str = "",
    verified: str = "",
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict[str, Any]]:
    sql = "SELECT e.*, c.name AS category_name FROM entries e JOIN categories c ON c.id=e.category_id WHERE 1=1"
    params: list[Any] = []
    if q.strip():
        sql += " AND (e.name LIKE ? OR e.capability LIKE ? OR e.description LIKE ?)"
        pat = f"%{q.strip()}%"
        params += [pat, pat, pat]
    if category:
        sql += " AND e.category_id=?"
        params.append(category)
    if entry_type:
        sql += " AND e.entry_type=?"
        params.append(entry_type)
    if licence:
        sql += " AND e.licence=?"
        params.append(licence)
    if cost:
        if cost not in VALID_COST:
            raise HTTPException(400, f"cost must be one of {sorted(VALID_COST)}")
        sql += " AND e.cost_class=?"
        params.append(cost)
    if maintenance:
        if maintenance not in VALID_MAINT:
            raise HTTPException(400, f"maintenance must be one of {sorted(VALID_MAINT)}")
        sql += " AND e.maintenance=?"
        params.append(maintenance)
    if verified == "true":
        sql += " AND e.verified_at IS NOT NULL"
    elif verified == "false":
        sql += " AND e.verified_at IS NULL"
    sql += " ORDER BY e.name LIMIT ?"
    params.append(limit)
    return db.query(sql, tuple(params))


@app.get("/api/v1/entries/{eid}")
def entry_detail(eid: str) -> dict[str, Any]:
    row = db.one("SELECT e.*, c.name AS category_name FROM entries e JOIN categories c ON c.id=e.category_id WHERE e.id=?", (eid,))
    if not row:
        raise HTTPException(404, "entry not found")
    return row


@app.post("/api/v1/entries/{eid}/verify")
def entry_verify(eid: str, force: bool = False) -> dict[str, Any]:
    try:
        return github_verify.verify_entry(eid, force=force)
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.post("/api/v1/verify-all")
def verify_all(limit: int = Query(default=25, ge=1, le=200)) -> dict[str, int]:
    return github_verify.verify_all(limit=limit)


@app.get("/api/v1/stats")
def stats() -> dict[str, Any]:
    total = db.one("SELECT COUNT(*) AS n FROM entries")["n"]
    verified = db.one("SELECT COUNT(*) AS n FROM entries WHERE verified_at IS NOT NULL")["n"]
    by_licence = db.query("SELECT licence, COUNT(*) AS n FROM entries GROUP BY licence ORDER BY n DESC")
    by_maint = db.query("SELECT maintenance, COUNT(*) AS n FROM entries GROUP BY maintenance")
    by_cat = db.query(
        "SELECT c.id, c.name, COUNT(e.id) AS entries FROM categories c LEFT JOIN entries e ON e.category_id=c.id GROUP BY c.id ORDER BY c.id"
    )
    return {
        "total_entries": total,
        "verified": verified,
        "unverified": total - verified,
        "by_licence": by_licence,
        "by_maintenance": by_maint,
        "by_category": by_cat,
        "github_token": bool(config.GITHUB_TOKEN),
    }


@app.get("/api/v1/export")
def export(fmt: str = "json") -> Any:
    rows = db.query("SELECT * FROM entries ORDER BY category_id, name")
    if fmt == "json":
        return rows
    if fmt == "markdown":
        lines = ["# Universal Capability Atlas", "", "| Entry | Capability | Category | Licence | Maintenance | Verified |", "|---|---|---|---|---|---|"]
        for r in rows:
            lines.append(f"| {r['name']} | {r['capability']} | {r['category_id']} | {r['licence']} | {r['maintenance']} | {r['verified_at'] or 'no'} |")
        return HTMLResponse("\n".join(lines), media_type="text/markdown")
    raise HTTPException(400, "fmt must be json or markdown")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    stats_ = stats()
    rows = entries(limit=500)
    cats = {c["id"]: c["name"] for c in categories()}
    cards = "".join(
        f"<div class='card'><b>{r['name']}</b>"
        f"<div class='cap'>{r['capability']}</div>"
        f"<div class='meta'>{cats.get(r['category_id'], r['category_id'])} · {r['entry_type']} · "
        f"licence: {r['licence']} · {r['maintenance']} · {'verified ' + r['verified_at'][:10] if r['verified_at'] else 'unverified'}</div>"
        f"<a href='{r['repo_url']}' target='_blank' rel='noopener'>{r['repo_url']}</a></div>"
        for r in rows
    )
    cat_opts = "".join(f"<option value='{cid}'>{name}</option>" for cid, name in cats.items())
    return f"""<!doctype html><html><head><title>Universal Capability Atlas</title><style>
body{{font-family:system-ui;margin:0;background:#0a1220;color:#eef4ff}}
header{{padding:24px 32px;border-bottom:1px solid #1e3a5c;background:#060b14;position:sticky;top:0}}
h1{{margin:0;font-size:20px;letter-spacing:2px;color:#4fd8ff}}
.sub{{color:#64748b;font-size:12px;margin-top:4px}}
.bar{{display:flex;gap:8px;padding:16px 32px;flex-wrap:wrap}}
input,select,button{{background:#0f1a2e;border:1px solid #1e3a5c;color:#eef4ff;border-radius:8px;padding:8px 12px;font-size:14px}}
button{{cursor:pointer}} button:hover{{border-color:#4fd8ff}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px;padding:0 32px 32px}}
.card{{background:#0f1a2e;border:1px solid #1e3a5c;border-radius:12px;padding:14px;font-size:13px;line-height:1.5}}
.card a{{color:#4fd8ff;text-decoration:none;font-size:11px;word-break:break-all}}
.cap{{color:#a8b8d0;margin:4px 0}} .meta{{color:#64748b;font-size:11px;margin-bottom:6px}}
.stat{{color:#ffb454}}</style></head><body>
<header><h1>UNIVERSAL CAPABILITY ATLAS</h1>
<div class="sub">{stats_['total_entries']} entries · <span class="stat">{stats_['verified']} verified against live GitHub</span> · {stats_['unverified']} unverified ·
GitHub token: {'yes' if stats_['github_token'] else 'no (60 req/hr limit)'}</div></header>
<div class="bar">
<input id="q" placeholder="Search capabilities…">
<select id="cat"><option value="">All categories</option>{cat_opts}</select>
<select id="vt"><option value="">Any verification</option><option value="true">Verified</option><option value="false">Unverified</option></select>
<button onclick="load()">Search</button>
<button onclick="fetch('/api/v1/verify-all?limit=25',{{method:'POST'}}).then(r=>r.json()).then(j=>{{alert('verified: '+j.verified+', failed: '+j.failed);load()}})">Verify 25 on GitHub</button>
</div>
<div class="grid" id="grid">{cards}</div>
<script>
async function load() {{
  const p = new URLSearchParams();
  if (q.value) p.set('q', q.value);
  if (cat.value) p.set('category', cat.value);
  if (vt.value) p.set('verified', vt.value);
  const data = await fetch('/api/v1/entries?' + p).then(r => r.json());
  document.getElementById('grid').innerHTML = data.map(r =>
    `<div class='card'><b>${{r.name}}</b><div class='cap'>${{r.capability}}</div>` +
    `<div class='meta'>${{r.category_id}} · ${{r.entry_type}} · licence: ${{r.licence}} · ${{r.maintenance}} · ` +
    `${{r.verified_at ? 'verified ' + r.verified_at.slice(0, 10) : 'unverified'}}</div>` +
    `<a href='${{r.repo_url}}' target='_blank' rel='noopener'>${{r.repo_url}}</a></div>`).join('');
}}
q.addEventListener('keydown', e => {{ if (e.key === 'Enter') load(); }});
</script></body></html>"""
