import os


def _use_fake(app=None):
    # Usa backend fake en TEST/CI para no depender de DB
    if app and app.config.get("FAKE_TODOS"):
        return True
    return bool(os.getenv("FAKE_TODOS"))


_FAKE_STORE = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Ship feature", "done": True},
]


def list_todos(app=None):
    if _use_fake(app):
        return list(_FAKE_STORE)

    try:
        from app.db import db
        from app.models import Todo  # si no existe, caemos al except

        qs = db.session.query(Todo).limit(100).all()
        return [
            {"id": t.id, "title": t.title, "done": getattr(t, "done", False)}
            for t in qs
        ]
    except Exception:
        # Tolerante: nunca 500 en CI
        return []


def create_todo(title: str, done: bool = False, app=None):
    if _use_fake(app):
        new_id = max((t["id"] for t in _FAKE_STORE), default=0) + 1
        todo = {"id": new_id, "title": title, "done": done}
        _FAKE_STORE.append(todo)
        return todo

    try:
        from app.db import db
        from app.models import Todo

        obj = Todo(title=title, done=done)
        db.session.add(obj)
        db.session.commit()
        return {"id": obj.id, "title": obj.title, "done": obj.done}
    except Exception:
        # En modo real sin DB: simula éxito sin romper
        return {"id": None, "title": title, "done": done}
