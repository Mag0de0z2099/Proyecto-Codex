from app.extensions import db


class ChecklistTemplate(db.Model):
    __tablename__ = "checklist_templates"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(160), nullable=False)
    norma = db.Column(db.String(40))
    items = db.relationship(
        "ChecklistItem",
        backref="template",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )


class ChecklistItem(db.Model):
    __tablename__ = "checklist_items"

    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(
        db.Integer,
        db.ForeignKey("checklist_templates.id"),
        nullable=False,
    )
    texto = db.Column(db.String(400), nullable=False)
    tipo = db.Column(db.String(10), nullable=False, default="bool")
    orden = db.Column(db.Integer, default=0)


class ChecklistRun(db.Model):
    __tablename__ = "checklist_runs"

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    equipo_id = db.Column(db.Integer)
    operador_id = db.Column(db.Integer)
    template_id = db.Column(
        db.Integer,
        db.ForeignKey("checklist_templates.id"),
        nullable=False,
    )
    pct_ok = db.Column(db.Float, default=0)
    notas = db.Column(db.Text)

    template = db.relationship("ChecklistTemplate")
    answers = db.relationship(
        "ChecklistAnswer",
        backref="run",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )


class ChecklistAnswer(db.Model):
    __tablename__ = "checklist_answers"

    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(
        db.Integer,
        db.ForeignKey("checklist_runs.id"),
        nullable=False,
    )
    item_id = db.Column(
        db.Integer,
        db.ForeignKey("checklist_items.id"),
        nullable=False,
    )
    valor_bool = db.Column(db.Boolean)
    comentario = db.Column(db.Text)
