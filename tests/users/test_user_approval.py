from datetime import datetime, timezone

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import User


def _user(email: str, pwd: str, approved: bool = False) -> User:
    username = email.split("@", 1)[0]
    user = User(
        email=email,
        username=username,
        password_hash=generate_password_hash(pwd),
        is_active=True,
        is_approved=approved,
    )
    if hasattr(user, "status") and approved:
        user.status = "approved"
    if hasattr(user, "approved_at") and approved:
        user.approved_at = datetime.now(timezone.utc)
    db.session.add(user)
    db.session.commit()
    return user


def test_approve_requires_admin_header(client, app_ctx):
    user = _user("p@p.com", "x", approved=False)
    resp = client.patch(f"/api/v1/users/{user.id}/approve")
    assert resp.status_code == 403


def test_approve_marks_user_as_approved(client, app_ctx):
    user = _user("q@q.com", "x", approved=False)
    resp = client.patch(
        f"/api/v1/users/{user.id}/approve", headers={"X-Role": "admin"}
    )
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["is_approved"] is True
    assert data["approved_at"] is not None


def test_list_filters_pending_and_approved(client, app_ctx):
    pending_user = _user("a@a.com", "x", approved=False)
    approved_user = _user("b@b.com", "x", approved=True)
    resp_pending = client.get("/api/v1/users?status=pending")
    resp_approved = client.get("/api/v1/users?status=approved")
    assert resp_pending.status_code == 200
    assert resp_approved.status_code == 200
    pending_data = resp_pending.get_json()["users"]
    approved_data = resp_approved.get_json()["users"]
    assert any(item["id"] == pending_user.id for item in pending_data)
    assert all(item["is_approved"] is True for item in approved_data)
    assert any(item["id"] == approved_user.id for item in approved_data)
