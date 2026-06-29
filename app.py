import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, text, func

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

# ================= DATABASE CONFIG =================
database_url = os.environ.get("DATABASE_URL", "sqlite:///local_materials.db")

# Render PostgreSQL + psycopg v3
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ================= MODELS =================
class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    material_type = db.Column(db.String(150), nullable=True)
    rate = db.Column(db.Float, nullable=False, default=0)
    price = db.Column(db.Float, nullable=False, default=0)
    datasheet = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def qty(self, area):
        return area * self.rate

    def cost(self, area):
        return self.qty(area) * self.price


# ================= CREATE / UPDATE TABLES =================
def ensure_database_schema():
    """
    Safe schema creation/update.
    It does NOT delete your saved materials.
    """
    db.create_all()

    if db.engine.url.get_backend_name().startswith("postgresql"):
        statements = [
            "ALTER TABLE material ADD COLUMN IF NOT EXISTS material_type VARCHAR(150)",
            "ALTER TABLE material ADD COLUMN IF NOT EXISTS rate DOUBLE PRECISION DEFAULT 0",
            "ALTER TABLE material ADD COLUMN IF NOT EXISTS price DOUBLE PRECISION DEFAULT 0",
            "ALTER TABLE material ADD COLUMN IF NOT EXISTS datasheet TEXT",
            "ALTER TABLE material ADD COLUMN IF NOT EXISTS notes TEXT",
            "ALTER TABLE material ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ]
        for statement in statements:
            db.session.execute(text(statement))
        db.session.commit()


with app.app_context():
    ensure_database_schema()


# ================= HELPERS =================
def normalize_datasheet(source: str) -> str:
    source = (source or "").strip()
    if not source:
        return ""
    if source.lower().startswith(("http://", "https://")):
        return source
    if "." in source and " " not in source:
        return "https://" + source
    return source


def get_selected_ids():
    ids = request.form.getlist("selected_materials")
    return [int(x) for x in ids if x.isdigit()]


def clean_type_list(values):
    clean = []
    seen = set()
    for value in values:
        value = (value or "").strip()
        if value and value not in seen:
            clean.append(value)
            seen.add(value)
    return clean


def get_material_types():
    return [
        row[0]
        for row in db.session.query(Material.material_type)
        .filter(Material.material_type.isnot(None))
        .filter(Material.material_type != "")
        .distinct()
        .order_by(Material.material_type.asc())
        .all()
    ]


def get_dashboard_stats():
    total_materials = Material.query.count()
    total_types = (
        db.session.query(func.count(func.distinct(Material.material_type)))
        .filter(Material.material_type.isnot(None))
        .filter(Material.material_type != "")
        .scalar()
        or 0
    )
    avg_price = db.session.query(func.avg(Material.price)).scalar() or 0
    last_material = Material.query.order_by(Material.created_at.desc()).first()

    type_rows = (
        db.session.query(Material.material_type, func.count(Material.id))
        .filter(Material.material_type.isnot(None))
        .filter(Material.material_type != "")
        .group_by(Material.material_type)
        .order_by(Material.material_type.asc())
        .all()
    )

    return {
        "total_materials": total_materials,
        "total_types": total_types,
        "avg_price": avg_price,
        "last_material": last_material.name if last_material else "-",
        "type_rows": type_rows,
    }


# ================= ROUTES =================
@app.route("/", methods=["GET"])
def index():
    search = request.args.get("search", "").strip()
    selected_types = clean_type_list(request.args.getlist("types"))

    # Backward compatibility for old links like /?type=Epoxy
    old_type = request.args.get("type", "").strip()
    if old_type and old_type not in selected_types:
        selected_types.append(old_type)

    material_types = get_material_types()
    stats = get_dashboard_stats()

    # Important requirement:
    # Do NOT display all materials by default.
    # Materials table appears only after selecting one or more material types.
    materials = []
    table_ready = bool(selected_types)

    if table_ready:
        query = Material.query.filter(Material.material_type.in_(selected_types))

        if search:
            like_text = f"%{search}%"
            query = query.filter(
                or_(
                    Material.name.ilike(like_text),
                    Material.material_type.ilike(like_text),
                    Material.notes.ilike(like_text),
                )
            )

        materials = query.order_by(Material.material_type.asc(), Material.name.asc()).all()

    return render_template(
        "index.html",
        materials=materials,
        material_types=material_types,
        search=search,
        selected_types=selected_types,
        table_ready=table_ready,
        stats=stats,
    )


@app.route("/material/save", methods=["POST"])
def save_material():
    material_id = request.form.get("material_id", "").strip()
    name = request.form.get("name", "").strip()
    material_type = request.form.get("material_type", "").strip()
    datasheet = normalize_datasheet(request.form.get("datasheet", ""))
    notes = request.form.get("notes", "").strip()

    try:
        rate = float(request.form.get("rate", "0"))
        price = float(request.form.get("price", "0"))
    except ValueError:
        flash("Consumption and Price must be valid numbers.", "danger")
        return redirect(url_for("index"))

    if not name:
        flash("Material name is required.", "danger")
        return redirect(url_for("index"))

    if not material_type:
        flash("Material Type is required to keep the database organized.", "warning")
        return redirect(url_for("index"))

    try:
        if material_id:
            material = Material.query.get_or_404(int(material_id))
            material.name = name
            material.material_type = material_type
            material.rate = rate
            material.price = price
            material.datasheet = datasheet
            material.notes = notes
            flash("Material updated successfully.", "success")
        else:
            existing = Material.query.filter_by(name=name).first()
            if existing:
                existing.material_type = material_type
                existing.rate = rate
                existing.price = price
                existing.datasheet = datasheet
                existing.notes = notes
                flash("Existing material updated successfully.", "success")
            else:
                material = Material(
                    name=name,
                    material_type=material_type,
                    rate=rate,
                    price=price,
                    datasheet=datasheet,
                    notes=notes,
                )
                db.session.add(material)
                flash("Material added successfully.", "success")

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Database error: {e}", "danger")

    return redirect(url_for("index", types=[material_type]))


@app.route("/material/delete/<int:material_id>", methods=["GET", "POST"])
def delete_material(material_id):
    material = Material.query.get_or_404(material_id)
    selected_type = material.material_type or ""
    try:
        db.session.delete(material)
        db.session.commit()
        flash("Material deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Delete failed: {e}", "danger")

    return redirect(url_for("index", types=[selected_type] if selected_type else []))


@app.route("/calculate", methods=["POST"])
def calculate():
    selected_types = clean_type_list(request.form.getlist("selected_types"))

    try:
        area = float(request.form.get("area", "0"))
        if area <= 0:
            raise ValueError
    except ValueError:
        flash("Please enter a valid area greater than zero.", "danger")
        return redirect(url_for("index", types=selected_types))

    selected_ids = get_selected_ids()
    if not selected_ids:
        flash("Select at least one material to calculate.", "warning")
        return redirect(url_for("index", types=selected_types))

    selected_materials = (
        Material.query.filter(Material.id.in_(selected_ids))
        .order_by(Material.material_type.asc(), Material.name.asc())
        .all()
    )

    rows = []
    total_cost = 0
    for material in selected_materials:
        qty = material.qty(area)
        cost = material.cost(area)
        total_cost += cost
        rows.append({
            "material": material,
            "qty": qty,
            "cost": cost,
        })

    return render_template(
        "report.html",
        area=area,
        rows=rows,
        total_cost=total_cost,
        now=datetime.now(),
        selected_types=selected_types,
    )


@app.route("/edit/<int:material_id>")
def edit_material(material_id):
    material = Material.query.get_or_404(material_id)
    material_types = get_material_types()
    stats = get_dashboard_stats()

    selected_types = [material.material_type] if material.material_type else []
    materials = (
        Material.query.filter(Material.material_type.in_(selected_types))
        .order_by(Material.material_type.asc(), Material.name.asc())
        .all()
        if selected_types else []
    )

    return render_template(
        "index.html",
        materials=materials,
        material_types=material_types,
        edit_material=material,
        search="",
        selected_types=selected_types,
        table_ready=bool(selected_types),
        stats=stats,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
