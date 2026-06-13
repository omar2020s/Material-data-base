import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, text


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")


# ================= DATABASE CONFIG =================
database_url = os.environ.get("DATABASE_URL", "sqlite:///local_materials.db")

# Render sometimes provides postgres:// or postgresql://
# We use psycopg v3 driver to avoid psycopg2 errors on Render.
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ================= MODELS =================
class Material(db.Model):
    __tablename__ = "material"

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


# ================= DATABASE INIT / SAFE MIGRATION =================
def ensure_database_columns():
    """Create tables and add missing columns for old PostgreSQL databases."""
    db.create_all()

    engine_name = db.engine.url.get_backend_name()

    # SQLite local development
    if engine_name == "sqlite":
        existing_columns = [
            row["name"]
            for row in db.session.execute(text("PRAGMA table_info(material)")).mappings()
        ]

        if "material_type" not in existing_columns:
            db.session.execute(text("ALTER TABLE material ADD COLUMN material_type VARCHAR(150)"))
        if "datasheet" not in existing_columns:
            db.session.execute(text("ALTER TABLE material ADD COLUMN datasheet TEXT"))
        if "notes" not in existing_columns:
            db.session.execute(text("ALTER TABLE material ADD COLUMN notes TEXT"))
        if "created_at" not in existing_columns:
            db.session.execute(text("ALTER TABLE material ADD COLUMN created_at DATETIME"))
        db.session.commit()
        return

    # PostgreSQL on Render
    db.session.execute(text("ALTER TABLE material ADD COLUMN IF NOT EXISTS material_type VARCHAR(150)"))
    db.session.execute(text("ALTER TABLE material ADD COLUMN IF NOT EXISTS datasheet TEXT"))
    db.session.execute(text("ALTER TABLE material ADD COLUMN IF NOT EXISTS notes TEXT"))
    db.session.execute(text("ALTER TABLE material ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
    db.session.commit()


with app.app_context():
    ensure_database_columns()


# ================= HELPERS =================
def normalize_datasheet(source: str) -> str:
    source = (source or "").strip()

    if not source:
        return ""

    if source.lower().startswith(("http://", "https://")):
        return source

    # If user writes only a domain like example.com/file.pdf
    if "." in source and " " not in source:
        return "https://" + source

    return source


def get_selected_ids():
    ids = request.form.getlist("selected_materials")
    return [int(x) for x in ids if x.isdigit()]


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


# ================= ROUTES =================
@app.route("/", methods=["GET"])
def index():
    search = request.args.get("search", "").strip()
    type_filter = request.args.get("type", "All Types").strip()

    query = Material.query

    if search:
        like_text = f"%{search}%"
        query = query.filter(
            or_(
                Material.name.ilike(like_text),
                Material.material_type.ilike(like_text),
                Material.notes.ilike(like_text),
            )
        )

    if type_filter and type_filter != "All Types":
        query = query.filter(Material.material_type == type_filter)

    materials = query.order_by(Material.name.asc()).all()

    return render_template(
        "index.html",
        materials=materials,
        material_types=get_material_types(),
        search=search,
        type_filter=type_filter,
        edit_material=None,
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

    return redirect(url_for("index"))


@app.route("/material/delete/<int:material_id>", methods=["POST"])
def delete_material(material_id):
    material = Material.query.get_or_404(material_id)
    db.session.delete(material)
    db.session.commit()
    flash("Material deleted successfully.", "success")
    return redirect(url_for("index"))


@app.route("/edit/<int:material_id>", methods=["GET"])
def edit_material(material_id):
    material = Material.query.get_or_404(material_id)
    materials = Material.query.order_by(Material.name.asc()).all()

    return render_template(
        "index.html",
        materials=materials,
        material_types=get_material_types(),
        edit_material=material,
        search="",
        type_filter="All Types",
    )


@app.route("/calculate", methods=["POST"])
def calculate():
    try:
        area = float(request.form.get("area", "0"))
        if area <= 0:
            raise ValueError
    except ValueError:
        flash("Please enter a valid area greater than zero.", "danger")
        return redirect(url_for("index"))

    selected_ids = get_selected_ids()

    if not selected_ids:
        flash("Select at least one material to calculate.", "warning")
        return redirect(url_for("index"))

    selected_materials = (
        Material.query
        .filter(Material.id.in_(selected_ids))
        .order_by(Material.name.asc())
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
    )


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
