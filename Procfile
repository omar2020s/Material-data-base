import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "repair-material-secret-key")

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///materials.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Material(db.Model):
    __tablename__ = "material"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    material_type = db.Column(db.String(120), nullable=True)
    rate = db.Column(db.Float, nullable=False, default=0)
    price = db.Column(db.Float, nullable=False, default=0)
    datasheet = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def normalize_link(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if value.lower().startswith(("http://", "https://")):
        return value
    if "." in value and not value.startswith("/"):
        return "https://" + value
    return value


def init_database():
    """Create tables and safely add missing columns for old Render PostgreSQL databases."""
    db.create_all()
    inspector = inspect(db.engine)
    if not inspector.has_table("material"):
        db.create_all()
        return

    existing_columns = {col["name"] for col in inspector.get_columns("material")}
    driver = db.engine.url.drivername

    if "postgresql" in driver:
        statements = [
            "ALTER TABLE material ADD COLUMN IF NOT EXISTS material_type VARCHAR(120)",
            "ALTER TABLE material ADD COLUMN IF NOT EXISTS rate DOUBLE PRECISION DEFAULT 0",
            "ALTER TABLE material ADD COLUMN IF NOT EXISTS price DOUBLE PRECISION DEFAULT 0",
            "ALTER TABLE material ADD COLUMN IF NOT EXISTS datasheet TEXT",
            "ALTER TABLE material ADD COLUMN IF NOT EXISTS notes TEXT",
            "ALTER TABLE material ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE material ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ]
    else:
        statements = []
        sqlite_columns = {
            "material_type": "ALTER TABLE material ADD COLUMN material_type VARCHAR(120)",
            "rate": "ALTER TABLE material ADD COLUMN rate FLOAT DEFAULT 0",
            "price": "ALTER TABLE material ADD COLUMN price FLOAT DEFAULT 0",
            "datasheet": "ALTER TABLE material ADD COLUMN datasheet TEXT",
            "notes": "ALTER TABLE material ADD COLUMN notes TEXT",
            "created_at": "ALTER TABLE material ADD COLUMN created_at DATETIME",
            "updated_at": "ALTER TABLE material ADD COLUMN updated_at DATETIME",
        }
        for column, statement in sqlite_columns.items():
            if column not in existing_columns:
                statements.append(statement)

    for statement in statements:
        db.session.execute(text(statement))
    db.session.commit()


with app.app_context():
    init_database()


@app.route("/", methods=["GET"])
def index():
    q = request.args.get("q", "").strip()
    selected_type = request.args.get("type", "All Types").strip()
    edit_id = request.args.get("edit", type=int)

    query = Material.query
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Material.name.ilike(like), Material.material_type.ilike(like)))
    if selected_type and selected_type != "All Types":
        query = query.filter(Material.material_type == selected_type)

    materials = query.order_by(Material.name.asc()).all()
    all_materials = Material.query.order_by(Material.name.asc()).all()
    edit_material = Material.query.get(edit_id) if edit_id else None

    type_rows = db.session.query(Material.material_type).distinct().all()
    types = [row[0] for row in type_rows if row[0]]
    types = ["All Types"] + sorted(types)

    total_materials = Material.query.count()
    total_types = len(types) - 1

    return render_template(
        "index.html",
        materials=materials,
        all_materials=all_materials,
        edit_material=edit_material,
        types=types,
        q=q,
        selected_type=selected_type,
        total_materials=total_materials,
        total_types=total_types,
        result=session.get("last_result"),
    )


@app.route("/save", methods=["POST"])
def save_material():
    material_id = request.form.get("material_id")
    name = request.form.get("name", "").strip()
    material_type = request.form.get("material_type", "").strip()
    notes = request.form.get("notes", "").strip()
    datasheet = normalize_link(request.form.get("datasheet", ""))

    try:
        rate = float(request.form.get("rate", "0") or 0)
        price = float(request.form.get("price", "0") or 0)
    except ValueError:
        flash("Consumption and price must be valid numbers.", "danger")
        return redirect(url_for("index"))

    if not name:
        flash("Material name is required.", "danger")
        return redirect(url_for("index"))

    existing = Material.query.filter(Material.name.ilike(name)).first()
    if material_id:
        material = Material.query.get_or_404(int(material_id))
        if existing and existing.id != material.id:
            flash("Another material already uses this name.", "danger")
            return redirect(url_for("index"))
    else:
        material = existing or Material()

    material.name = name
    material.material_type = material_type
    material.rate = rate
    material.price = price
    material.datasheet = datasheet
    material.notes = notes
    material.updated_at = datetime.utcnow()

    db.session.add(material)
    db.session.commit()
    flash("Material saved successfully.", "success")
    return redirect(url_for("index"))


@app.route("/delete/<int:material_id>", methods=["POST"])
def delete_material(material_id):
    material = Material.query.get_or_404(material_id)
    db.session.delete(material)
    db.session.commit()
    flash("Material deleted successfully.", "success")
    return redirect(url_for("index"))


@app.route("/calculate", methods=["POST"])
def calculate():
    ids = request.form.getlist("material_ids")
    try:
        area = float(request.form.get("area", "0") or 0)
    except ValueError:
        flash("Enter a valid area.", "danger")
        return redirect(url_for("index"))

    if area <= 0:
        flash("Area must be greater than zero.", "danger")
        return redirect(url_for("index"))
    if not ids:
        flash("Select at least one material.", "danger")
        return redirect(url_for("index"))

    materials = Material.query.filter(Material.id.in_([int(i) for i in ids])).order_by(Material.name.asc()).all()
    rows = []
    total = 0
    for m in materials:
        qty = area * (m.rate or 0)
        cost = qty * (m.price or 0)
        total += cost
        rows.append({
            "id": m.id,
            "name": m.name,
            "material_type": m.material_type or "",
            "rate": m.rate or 0,
            "price": m.price or 0,
            "qty": qty,
            "cost": cost,
            "notes": m.notes or "",
            "datasheet": m.datasheet or "",
        })

    session["last_result"] = {
        "area": area,
        "rows": rows,
        "total": total,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    return redirect(url_for("index", _anchor="result"))


@app.route("/report")
def report():
    result = session.get("last_result")
    if not result:
        flash("Calculate first before opening the report.", "warning")
        return redirect(url_for("index"))
    return render_template("report.html", result=result)


@app.route("/clear-result")
def clear_result():
    session.pop("last_result", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
