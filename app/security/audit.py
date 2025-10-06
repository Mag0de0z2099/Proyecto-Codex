from datetime import datetime

from flask import request

from app.db import db


class AuditEvent(db.Model):
    __tablename__ = "audit_events"

    id = db.Column(db.Integer, primary_key=True)
    ts = db.Column(db.DateTime, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer)
    ip = db.Column(db.String(64))
    ua = db.Column(db.String(256))
    meta = db.Column(db.JSON)


def log_event(evt_type, user_id=None, meta=None):
    ev = AuditEvent(
        ts=datetime.utcnow(),
        type=evt_type,
        user_id=user_id,
        ip=(request.remote_addr if request else None),
        ua=(request.headers.get("User-Agent") if request else None),
        meta=meta or {},
    )
    db.session.add(ev)
    db.session.commit()
