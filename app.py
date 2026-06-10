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
    # On the web version, local computer paths cannot be shared globally.
    # If the user types example.com/file.pdf, convert it to https://example.com/file.pdf
    if "." in source and " " not in source:
        return "https://" + source
    return source


HTML = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Repair Material Calculator Pro</title>
  <style>
    :root{
      --bg:#0f172a; --card:#111827; --card2:#1f2937; --text:#e5e7eb;
      --muted:#9ca3af; --primary:#0ea5e9; --primary2:#0284c7;
      --danger:#ef4444; --green:#22c55e; --yellow:#facc15; --border:#334155;
    }
    *{box-sizing:border-box}
    body{
      margin:0; font-family:Arial, Helvetica, sans-serif; color:var(--text);
      background:linear-gradient(135deg,#020617,#0f172a 45%,#111827);
      min-height:100vh;
    }
    .container{max-width:1250px; margin:auto; padding:24px}
    .hero{
      display:flex; justify-content:space-between; align-items:center; gap:18px;
      padding:24px; border:1px solid var(--border); border-radius:22px;
      background:rgba(17,24,39,.86); box-shadow:0 18px 40px rgba(0,0,0,.35);
      margin-bottom:18px;
    }
    h1{margin:0; font-size:32px}
    .sub{color:var(--muted); margin-top:8px}
    .badge{background:#082f49;color:#bae6fd;border:1px solid #075985;padding:10px 14px;border-radius:999px}
    .grid{display:grid; grid-template-columns:1.1fr .9fr; gap:18px}
    .card{
      background:rgba(17,24,39,.88); border:1px solid var(--border);
      border-radius:18px; padding:18px; box-shadow:0 12px 30px rgba(0,0,0,.22);
    }
    label{display:block; margin:10px 0 6px; color:#cbd5e1; font-weight:bold}
    input, select{
      width:100%; padding:13px 14px; border-radius:12px; border:1px solid var(--border);
      background:#020617; color:var(--text); outline:none; font-size:15px;
    }
    input:focus, select:focus{border-color:var(--primary)}
    .row{display:grid; grid-template-columns:1fr 1fr; gap:12px}
    .actions{display:flex; flex-wrap:wrap; gap:10px; margin-top:14px}
    button, .btn{
      border:0; border-radius:12px; padding:12px 16px; color:white; cursor:pointer;
      font-weight:bold; background:var(--primary); text-decoration:none; display:inline-block;
    }
    button:hover,.btn:hover{background:var(--primary2)}
    .danger{background:var(--danger)}
    .green{background:var(--green); color:#052e16}
    .orange{background:#f97316}
    .purple{background:#7c3aed}
    table{width:100%; border-collapse:collapse; overflow:hidden; border-radius:14px; margin-top:12px}
    th,td{padding:12px; border-bottom:1px solid var(--border); text-align:center}
    th{background:#0ea5e9; color:white}
    tr{background:#111827}
    tr:nth-child(even){background:#0b1220}
    .total{
      margin-top:16px; text-align:right; color:var(--yellow); font-size:28px; font-weight:bold;
    }
    .msg{padding:12px 14px;border-radius:12px;margin:10px 0;background:#064e3b;color:#d1fae5}
    .warn{color:#fef3c7;background:#78350f;padding:10px;border-radius:10px;margin-top:10px}
    .small{color:var(--muted); font-size:13px}
    @media(max-width:900px){
      .grid{grid-template-columns:1fr}
      .hero{flex-direction:column; align-items:flex-start}
      .row{grid-template-columns:1fr}
      table{font-size:13px}
      .container{padding:12px}
      th,td{padding:8px}
    }
    @media print{
      body{background:white;color:black}
      .no-print,.card form,.hero .badge,.actions{display:none!important}
      .card,.hero{box-shadow:none;border:0;background:white}
      th{background:#ddd!important;color:black}
      tr{background:white!important;color:black}
      a{color:black}
    }
  </style>
</head>
<body>
<div class="container">
  <div class="hero">
    <div>
      <h1>Repair Material Calculator Pro</h1>
      <div class="sub">Online version ready for GitHub + Render deployment</div>
    </div>
    <div class="badge">Web App / Global Link</div>
  </div>

  {% with messages = get_flashed_messages() %}
    {% if messages %}
      {% for message in messages %}
        <div class="msg">{{ message }}</div>
      {% endfor %}
    {% endif %}
  {% endwith %}

  <div class="grid">
    <div class="card">
      <h2>Materials Management</h2>

      <form method="post" action="{{ url_for('save_material') }}">
        <label>Select Existing Material</label>
        <select id="materialSelect" onchange="fillMaterial()">
          <option value="">-- Select Material --</option>
          {% for name, data in materials.items() %}
            <option value="{{ name }}"
                    data-rate="{{ data.get('rate','') }}"
                    data-price="{{ data.get('price','') }}"
                    data-datasheet="{{ data.get('datasheet','') }}">{{ name }}</option>
          {% endfor %}
        </select>

        <label>Search</label>
        <input id="searchBox" placeholder="Search Material..." oninput="filterMaterials()">

        <label>Material Name</label>
        <input name="material" id="materialName" required>

        <div class="row">
          <div>
            <label>Consumption (kg/m²)</label>
            <input name="rate" id="rate" type="number" step="0.0001" required>
          </div>
          <div>
            <label>Price per kg</label>
            <input name="price" id="price" type="number" step="0.01" required>
          </div>
        </div>

        <label>Data Sheet PDF Link</label>
        <input name="datasheet" id="datasheet" placeholder="Paste online PDF link only">
        <div class="small">مهم: نسخة الإنترنت لا تستطيع فتح ملفات PDF من جهازك. ارفع ملف PDF على Google Drive أو أي رابط مباشر وضع الرابط هنا.</div>

        <div class="actions">
          <button type="submit">Add / Update Material</button>
          <button type="button" class="danger" onclick="deleteMaterial()">Delete Material</button>
          <button type="button" class="purple" onclick="openDataSheet()">Open Data Sheet</button>
        </div>
      </form>
    </div>

    <div class="card">
      <h2>Calculation</h2>
      <label>Area (m²)</label>
      <input id="area" type="number" step="0.01" placeholder="Enter area">

      <label>Add Material To Calculation</label>
      <select id="calcMaterial">
        <option value="">-- Select Material --</option>
        {% for name, data in materials.items() %}
          <option value="{{ name }}"
                  data-rate="{{ data.get('rate',0) }}"
                  data-price="{{ data.get('price',0) }}"
                  data-datasheet="{{ data.get('datasheet','') }}">{{ name }}</option>
        {% endfor %}
      </select>

      <div class="actions">
        <button type="button" onclick="addToTable()">Add To Calculation</button>
        <button type="button" class="green" onclick="calculate()">Calculate</button>
        <button type="button" class="orange" onclick="clearTable()">Clear Table</button>
        <button type="button" onclick="window.print()">Print Report</button>
      </div>

      <div class="warn">كل الحسابات تتم داخل المتصفح، ولا تحتاج تثبيت Python على جهاز العميل.</div>
    </div>
  </div>

  <div class="card" style="margin-top:18px">
    <h2>Report Table</h2>
    <table id="reportTable">
      <thead>
        <tr>
          <th>Material</th>
          <th>Consumption</th>
          <th>Price</th>
          <th>Qty</th>
          <th>Cost</th>
          <th>Data Sheet</th>
          <th class="no-print">Action</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
    <div class="total" id="totalCost">Total Cost = 0.00</div>
  </div>
</div>

<script>
const deleteUrlBase = "{{ url_for('delete_material', material='__MATERIAL__') }}";

function fillMaterial(){
  const s = document.getElementById('materialSelect');
  const op = s.options[s.selectedIndex];
  if(!op.value) return;
  document.getElementById('materialName').value = op.value;
  document.getElementById('rate').value = op.dataset.rate;
  document.getElementById('price').value = op.dataset.price;
  document.getElementById('datasheet').value = op.dataset.datasheet;
}

function filterMaterials(){
  const q = document.getElementById('searchBox').value.toLowerCase();
  const s = document.getElementById('materialSelect');
  for (const op of s.options){
    if(!op.value){op.hidden=false; continue;}
    op.hidden = !op.value.toLowerCase().includes(q);
  }
}

function deleteMaterial(){
  const name = document.getElementById('materialName').value.trim();
  if(!name){ alert('Select material first'); return; }
  if(!confirm('Delete material: ' + name + '?')) return;
  window.location.href = deleteUrlBase.replace('__MATERIAL__', encodeURIComponent(name));
}

function openDataSheet(){
  const link = document.getElementById('datasheet').value.trim();
  if(!link){ alert('No Data Sheet link found'); return; }
  window.open(link, '_blank');
}

function addToTable(){
  const select = document.getElementById('calcMaterial');
  const op = select.options[select.selectedIndex];
  if(!op.value){ alert('Select material first'); return; }

  const tbody = document.querySelector('#reportTable tbody');
  for (const row of tbody.rows){
    if(row.dataset.material === op.value){
      alert('Material already added');
      return;
    }
  }

  const row = tbody.insertRow();
  row.dataset.material = op.value;
  row.dataset.rate = op.dataset.rate;
  row.dataset.price = op.dataset.price;
  row.dataset.datasheet = op.dataset.datasheet || '';

  row.innerHTML = `
    <td>${op.value}</td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td>${op.dataset.datasheet ? `<a href="${op.dataset.datasheet}" target="_blank">Open PDF</a>` : ''}</td>
    <td class="no-print"><button class="danger" onclick="this.closest('tr').remove(); calculate();">Remove</button></td>
  `;
}

function calculate(){
  const area = parseFloat(document.getElementById('area').value);
  if(isNaN(area) || area <= 0){ alert('Enter valid area'); return; }

  let total = 0;
  const tbody = document.querySelector('#reportTable tbody');

  for (const row of tbody.rows){
    const rate = parseFloat(row.dataset.rate);
    const price = parseFloat(row.dataset.price);
    const qty = area * rate;
    const cost = qty * price;
    total += cost;

    row.cells[1].textContent = rate + ' kg/m²';
    row.cells[2].textContent = price.toFixed(2);
    row.cells[3].textContent = qty.toFixed(2) + ' kg';
    row.cells[4].textContent = cost.toFixed(2);
  }

  document.getElementById('totalCost').textContent = 'Total Cost = ' + total.toFixed(2);
}

function clearTable(){
  document.querySelector('#reportTable tbody').innerHTML = '';
  document.getElementById('totalCost').textContent = 'Total Cost = 0.00';
}
</script>
</body>
</html>
"""


@app.route("/")
def index():
    materials = load_materials()
    return render_template_string(HTML, materials=materials)


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

    materials[material] = {
        "rate": rate,
        "price": price,
        "datasheet": normalize_datasheet(request.form.get("datasheet", "")),
    }
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
    # Render provides PORT automatically. Locally, app runs on http://127.0.0.1:5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
