from flask import Flask, render_template_string, request, redirect, url_for, flash, jsonify
import json
import os
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")
DATA_FILE = Path("materials.json")


def load_materials():
    if DATA_FILE.exists():
        try:
            with DATA_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_materials(materials):
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(materials, f, indent=4, ensure_ascii=False)


def normalize_datasheet(source: str) -> str:
    source = (source or "").strip()
    if not source:
        return ""
    if source.lower().startswith(("http://", "https://")):
        return source
    if "." in source and " " not in source:
        return "https://" + source
    return source


HTML = r'''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Material Database Pro</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root{
      --bg:#070b16; --panel:#0d1424; --panel2:#111b2e; --card:#101827; --text:#eef4ff;
      --muted:#8ea0b8; --line:rgba(148,163,184,.18); --blue:#38bdf8; --blue2:#0ea5e9;
      --violet:#8b5cf6; --green:#34d399; --red:#fb7185; --orange:#fb923c; --yellow:#facc15;
      --shadow:0 24px 70px rgba(0,0,0,.45); --radius:22px;
    }
    *{box-sizing:border-box} html{scroll-behavior:smooth}
    body{margin:0;min-height:100vh;font-family:Inter,Arial,sans-serif;color:var(--text);background:
      radial-gradient(circle at 15% 10%, rgba(56,189,248,.18), transparent 28%),
      radial-gradient(circle at 80% 0%, rgba(139,92,246,.17), transparent 30%),
      linear-gradient(135deg,#050816,#0b1120 55%,#0f172a);}
    body:before{content:"";position:fixed;inset:0;pointer-events:none;background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);background-size:44px 44px;mask-image:linear-gradient(to bottom,black,transparent 85%)}
    .app{display:grid;grid-template-columns:270px 1fr;min-height:100vh}.sidebar{position:sticky;top:0;height:100vh;padding:24px;border-right:1px solid var(--line);background:rgba(7,11,22,.72);backdrop-filter:blur(18px)}
    .brand{display:flex;gap:12px;align-items:center;margin-bottom:28px}.logo{width:46px;height:46px;border-radius:16px;background:linear-gradient(135deg,var(--blue),var(--violet));display:grid;place-items:center;font-weight:900;box-shadow:0 14px 35px rgba(14,165,233,.35)}
    .brand h2{font-size:18px;margin:0}.brand span{font-size:12px;color:var(--muted)}
    .nav a{display:flex;align-items:center;gap:10px;color:#cbd5e1;text-decoration:none;padding:12px 14px;border-radius:14px;margin:6px 0;font-weight:600}.nav a:hover,.nav a.active{background:rgba(56,189,248,.12);color:white;border:1px solid rgba(56,189,248,.16)}
    .side-note{position:absolute;left:24px;right:24px;bottom:24px;padding:16px;border:1px solid var(--line);border-radius:18px;background:rgba(17,27,46,.75);color:var(--muted);font-size:13px;line-height:1.55}
    main{padding:28px;max-width:1450px;width:100%;margin:auto}.topbar{display:flex;justify-content:space-between;gap:18px;align-items:center;margin-bottom:22px}.title h1{font-size:34px;line-height:1.05;margin:0 0 8px}.title p{margin:0;color:var(--muted)}
    .pill{padding:11px 14px;border-radius:999px;border:1px solid rgba(56,189,248,.25);background:rgba(56,189,248,.11);color:#bae6fd;font-weight:700;white-space:nowrap}.hero{border:1px solid var(--line);border-radius:28px;background:linear-gradient(135deg,rgba(16,24,39,.94),rgba(17,27,46,.75));box-shadow:var(--shadow);padding:24px;margin-bottom:20px;position:relative;overflow:hidden}.hero:after{content:"";position:absolute;right:-100px;top:-120px;width:310px;height:310px;background:radial-gradient(circle,rgba(56,189,248,.22),transparent 65%)}
    .stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.stat{padding:18px;border:1px solid var(--line);border-radius:20px;background:rgba(2,6,23,.42)}.stat small{display:block;color:var(--muted);font-weight:700}.stat strong{display:block;font-size:28px;margin-top:7px}.stat em{font-style:normal;color:var(--green);font-size:12px}
    .grid{display:grid;grid-template-columns:1.05fr .95fr;gap:20px}.card{border:1px solid var(--line);border-radius:var(--radius);background:rgba(16,24,39,.86);box-shadow:0 14px 45px rgba(0,0,0,.28);padding:22px}.card-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:16px}.card h2{font-size:20px;margin:0}.hint{color:var(--muted);font-size:13px;line-height:1.5}
    label{display:block;margin:13px 0 7px;color:#d7e3f4;font-weight:700;font-size:14px}input,select{width:100%;padding:14px 15px;border-radius:15px;border:1px solid var(--line);background:#070d19;color:var(--text);outline:none;font-size:15px;transition:.2s}input:focus,select:focus{border-color:rgba(56,189,248,.7);box-shadow:0 0 0 4px rgba(56,189,248,.1)}.row{display:grid;grid-template-columns:1fr 1fr;gap:13px}.actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:16px}button,.btn{border:0;border-radius:15px;padding:13px 16px;color:white;cursor:pointer;font-weight:800;background:linear-gradient(135deg,var(--blue2),#2563eb);text-decoration:none;display:inline-flex;align-items:center;gap:8px;box-shadow:0 12px 24px rgba(14,165,233,.18)}button:hover,.btn:hover{transform:translateY(-1px);filter:brightness(1.08)}.danger{background:linear-gradient(135deg,#f43f5e,#be123c)}.green{background:linear-gradient(135deg,#34d399,#059669);color:#052e16}.orange{background:linear-gradient(135deg,#fb923c,#ea580c)}.purple{background:linear-gradient(135deg,#8b5cf6,#6d28d9)}.ghost{background:rgba(148,163,184,.12);box-shadow:none;border:1px solid var(--line)}
    .flash{padding:14px 16px;border:1px solid rgba(52,211,153,.25);border-radius:16px;background:rgba(6,78,59,.35);color:#d1fae5;margin-bottom:16px;font-weight:700}.warn{padding:13px 14px;border-radius:16px;background:rgba(251,146,60,.12);border:1px solid rgba(251,146,60,.25);color:#fed7aa;margin-top:14px}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:18px;margin-top:12px}table{width:100%;border-collapse:collapse;min-width:860px}th,td{padding:14px 12px;text-align:center;border-bottom:1px solid var(--line)}th{position:sticky;top:0;background:#0b2a43;color:#e0f2fe;font-size:13px;text-transform:uppercase;letter-spacing:.04em}tr{background:rgba(2,6,23,.24)}tr:hover{background:rgba(56,189,248,.06)}td a{color:#7dd3fc;font-weight:800}.total{display:flex;justify-content:space-between;align-items:center;margin-top:18px;padding:18px;border-radius:18px;background:linear-gradient(135deg,rgba(250,204,21,.12),rgba(56,189,248,.08));border:1px solid var(--line)}.total span{color:var(--muted);font-weight:800}.total strong{font-size:30px;color:var(--yellow)}.toolbar{display:flex;gap:12px;align-items:center;justify-content:space-between;margin:10px 0}.toolbar input{max-width:360px}.empty{text-align:center;color:var(--muted);padding:26px!important}
    @media(max-width:1050px){.app{grid-template-columns:1fr}.sidebar{position:relative;height:auto}.side-note{position:static;margin-top:20px}.grid,.stats{grid-template-columns:1fr}.topbar{align-items:flex-start;flex-direction:column}main{padding:16px}.row{grid-template-columns:1fr}}
    @media print{.sidebar,.no-print,.actions,.topbar .pill,.hero,.manage-card{display:none!important}body{background:white;color:#111}.app{display:block}main{padding:0}.card{border:0;box-shadow:none;background:white}.table-wrap{border:1px solid #ddd}th{background:#eee;color:#111}tr,td{background:white;color:#111}.total strong{color:#111}a{color:#111}}
  </style>
</head>
<body>
<div class="app">
  <aside class="sidebar no-print">
    <div class="brand"><div class="logo">MD</div><div><h2>Material Database</h2><span>Repair Calculator Pro</span></div></div>
    <nav class="nav"><a class="active" href="#dashboard">📊 Dashboard</a><a href="#materials">🧱 Materials</a><a href="#calculation">🧮 Calculation</a><a href="#report">🖨️ Report</a></nav>
    <div class="side-note">Professional web version for Render. Use online PDF links only, because local computer paths are not public.</div>
  </aside>
  <main>
    <div class="topbar"><div class="title"><h1>Repair Material Calculator Pro</h1><p>Modern material database, quantity takeoff and cost report.</p></div><div class="pill">🌍 GitHub + Render Ready</div></div>
    {% with messages = get_flashed_messages() %}{% if messages %}{% for message in messages %}<div class="flash">✅ {{ message }}</div>{% endfor %}{% endif %}{% endwith %}
    <section class="hero" id="dashboard"><div class="stats"><div class="stat"><small>Total Materials</small><strong>{{ total_materials }}</strong><em>Saved database</em></div><div class="stat"><small>With Data Sheet</small><strong>{{ with_datasheets }}</strong><em>PDF links</em></div><div class="stat"><small>Average Price</small><strong>{{ avg_price }}</strong><em>per kg</em></div><div class="stat"><small>Status</small><strong>Online</strong><em>Ready to share</em></div></div></section>
    <div class="grid">
      <section class="card manage-card" id="materials"><div class="card-head"><h2>Materials Management</h2><span class="hint">Add, update, search and delete materials.</span></div>
        <form method="post" action="{{ url_for('save_material') }}">
          <label>Select Existing Material</label><select id="materialSelect" onchange="fillMaterial()"><option value="">-- Select Material --</option>{% for name, data in materials.items() %}<option value="{{ name }}" data-rate="{{ data.get('rate','') }}" data-price="{{ data.get('price','') }}" data-datasheet="{{ data.get('datasheet','') }}">{{ name }}</option>{% endfor %}</select>
          <label>Search Material</label><input id="searchBox" placeholder="Type material name..." oninput="filterMaterials()">
          <label>Material Name</label><input name="material" id="materialName" required placeholder="Example: Sika MonoTop">
          <div class="row"><div><label>Consumption (kg/m²)</label><input name="rate" id="rate" type="number" step="0.0001" required placeholder="0.00"></div><div><label>Price per kg</label><input name="price" id="price" type="number" step="0.01" required placeholder="0.00"></div></div>
          <label>Data Sheet PDF Link</label><input name="datasheet" id="datasheet" placeholder="https://example.com/datasheet.pdf"><div class="hint">مهم: ارفع ملف PDF على Google Drive أو أي رابط مباشر، ولا تستخدم مسار ملف من جهازك.</div>
          <div class="actions"><button type="submit">💾 Save Material</button><button type="button" class="danger" onclick="deleteMaterial()">🗑️ Delete</button><button type="button" class="purple" onclick="openDataSheet()">📄 Open Data Sheet</button></div>
        </form>
      </section>
      <section class="card" id="calculation"><div class="card-head"><h2>Quick Calculation</h2><span class="hint">Select items then calculate total cost.</span></div>
        <label>Area (m²)</label><input id="area" type="number" step="0.01" placeholder="Enter area, example: 125">
        <label>Add Material To Report</label><select id="calcMaterial"><option value="">-- Select Material --</option>{% for name, data in materials.items() %}<option value="{{ name }}" data-rate="{{ data.get('rate',0) }}" data-price="{{ data.get('price',0) }}" data-datasheet="{{ data.get('datasheet','') }}">{{ name }}</option>{% endfor %}</select>
        <div class="actions"><button type="button" onclick="addToTable()">➕ Add</button><button type="button" class="green" onclick="calculate()">🧮 Calculate</button><button type="button" class="orange" onclick="clearTable()">🧹 Clear</button><button type="button" class="ghost" onclick="window.print()">🖨️ Print</button></div>
        <div class="warn">كل الحسابات تتم مباشرة داخل المتصفح، والتقرير جاهز للطباعة.</div>
      </section>
    </div>
    
<div class="print-header" style="display:none">
<div class="print-title">MATERIAL CALCULATION REPORT</div>
<div class="print-subtitle">Material Database Pro</div>
<div class="report-summary">
<div class="summary-box"><h4>Date</h4><span id="printDate"></span></div>
<div class="summary-box"><h4>Area</h4><span id="printArea">0</span></div>
<div class="summary-box"><h4>Total Cost</h4><span id="printTotal">0</span></div>
</div>
</div>
<section class="card" id="report" style="margin-top:20px"><div class="card-head"><h2>Calculation Report</h2><span class="hint">Printable professional report table.</span></div><div class="toolbar no-print"><input id="tableSearch" placeholder="Search inside report..." oninput="filterTable()"><button class="ghost" onclick="exportCSV()">⬇️ Export CSV</button></div><div class="table-wrap"><table id="reportTable"><thead><tr><th>Material</th><th>Consumption</th><th>Price</th><th>Qty</th><th>Cost</th><th>Data Sheet</th><th class="no-print">Action</th></tr></thead><tbody><tr class="empty-row"><td colspan="7" class="empty">No materials added yet. Choose a material and click Add.</td></tr></tbody></table></div><div class="total"><span>Total Cost</span><strong id="totalCost">0.00</strong></div></section>
  </main>
</div>
<script>
const deleteUrlBase = "{{ url_for('delete_material', material='__MATERIAL__') }}";
function esc(s){return String(s||'').replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));}
function fillMaterial(){const s=document.getElementById('materialSelect');const op=s.options[s.selectedIndex];if(!op.value)return;materialName.value=op.value;rate.value=op.dataset.rate;price.value=op.dataset.price;datasheet.value=op.dataset.datasheet;}
function filterMaterials(){const q=searchBox.value.toLowerCase();for(const op of materialSelect.options){op.hidden=op.value && !op.value.toLowerCase().includes(q);}}
function deleteMaterial(){const name=materialName.value.trim();if(!name){alert('Select material first');return;}if(!confirm('Delete material: '+name+'?'))return;window.location.href=deleteUrlBase.replace('__MATERIAL__',encodeURIComponent(name));}
function openDataSheet(){const link=datasheet.value.trim();if(!link){alert('No Data Sheet link found');return;}window.open(link,'_blank');}
function cleanEmpty(){document.querySelector('.empty-row')?.remove();}
function addToTable(){const select=calcMaterial;const op=select.options[select.selectedIndex];if(!op.value){alert('Select material first');return;}cleanEmpty();const tbody=document.querySelector('#reportTable tbody');for(const row of tbody.rows){if(row.dataset.material===op.value){alert('Material already added');return;}}const row=tbody.insertRow();row.dataset.material=op.value;row.dataset.rate=op.dataset.rate;row.dataset.price=op.dataset.price;row.dataset.datasheet=op.dataset.datasheet||'';row.innerHTML=`<td>${esc(op.value)}</td><td></td><td></td><td></td><td></td><td>${op.dataset.datasheet?`<a href="${esc(op.dataset.datasheet)}" target="_blank">Open PDF</a>`:''}</td><td class="no-print"><button class="danger" onclick="this.closest('tr').remove(); calculate(); restoreEmpty();">Remove</button></td>`;}
function restoreEmpty(){const tbody=document.querySelector('#reportTable tbody');if(!tbody.rows.length){tbody.innerHTML='<tr class="empty-row"><td colspan="7" class="empty">No materials added yet. Choose a material and click Add.</td></tr>';}}
function calculate(){const area=parseFloat(document.getElementById('area').value);if(isNaN(area)||area<=0){alert('Enter valid area');return;}let total=0;const tbody=document.querySelector('#reportTable tbody');for(const row of tbody.rows){if(row.classList.contains('empty-row'))continue;const rate=parseFloat(row.dataset.rate);const price=parseFloat(row.dataset.price);const qty=area*rate;const cost=qty*price;total+=cost;row.cells[1].textContent=rate+' kg/m²';row.cells[2].textContent=price.toFixed(2);row.cells[3].textContent=qty.toFixed(2)+' kg';row.cells[4].textContent=cost.toFixed(2);}totalCost.textContent=total.toFixed(2);
document.getElementById('printDate').innerText=new Date().toLocaleDateString();
document.getElementById('printArea').innerText=area.toFixed(2)+' m²';
document.getElementById('printTotal').innerText=total.toFixed(2);}
function clearTable(){document.querySelector('#reportTable tbody').innerHTML='<tr class="empty-row"><td colspan="7" class="empty">No materials added yet. Choose a material and click Add.</td></tr>';totalCost.textContent='0.00';}
function filterTable(){const q=tableSearch.value.toLowerCase();document.querySelectorAll('#reportTable tbody tr').forEach(r=>{if(r.classList.contains('empty-row'))return;r.style.display=r.innerText.toLowerCase().includes(q)?'':'none';});}
function exportCSV(){let rows=[['Material','Consumption','Price','Qty','Cost','Data Sheet']];document.querySelectorAll('#reportTable tbody tr').forEach(r=>{if(r.classList.contains('empty-row'))return;rows.push([r.cells[0].innerText,r.cells[1].innerText,r.cells[2].innerText,r.cells[3].innerText,r.cells[4].innerText,r.dataset.datasheet||'']);});const csv=rows.map(r=>r.map(v=>'"'+String(v).replaceAll('"','""')+'"').join(',')).join('\n');const blob=new Blob([csv],{type:'text/csv'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='material-report.csv';a.click();}
</script>
</body>
</html>
'''


@app.route("/")
def index():
    materials = load_materials()
    prices = [float(v.get("price", 0) or 0) for v in materials.values()]
    avg_price = f"{(sum(prices) / len(prices)):.2f}" if prices else "0.00"
    with_datasheets = sum(1 for v in materials.values() if v.get("datasheet"))
    return render_template_string(
        HTML,
        materials=materials,
        total_materials=len(materials),
        with_datasheets=with_datasheets,
        avg_price=avg_price,
    )


@app.route("/save", methods=["POST"])
def save_material():
    materials = load_materials()
    material = request.form.get("material", "").strip()
    if not material:
        flash("Enter Material Name")
        return redirect(url_for("index"))
    try:
        rate = float(request.form.get("rate", ""))
        price = float(request.form.get("price", ""))
    except ValueError:
        flash("Invalid consumption or price")
        return redirect(url_for("index"))
    materials[material] = {"rate": rate, "price": price, "datasheet": normalize_datasheet(request.form.get("datasheet", ""))}
    save_materials(materials)
    flash("Material saved successfully")
    return redirect(url_for("index"))


@app.route("/delete/<path:material>")
def delete_material(material):
    materials = load_materials()
    if material in materials:
        del materials[material]
        save_materials(materials)
        flash("Material deleted successfully")
    else:
        flash("Material not found")
    return redirect(url_for("index"))


@app.route("/api/materials")
def api_materials():
    return jsonify(load_materials())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
