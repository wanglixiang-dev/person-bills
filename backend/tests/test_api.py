from __future__ import annotations

import time

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def unique_email(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1000)}@example.com"


def register_user(email: str, password: str = "Password123") -> str:
    code = client.post("/api/v1/auth/send-code", json={"email": email, "purpose": "register"}).json()["dev_code"]
    response = client.post("/api/v1/auth/register", json={"email": email, "code": code, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_register_initializes_default_categories_and_me():
    email = unique_email("register")
    token = register_user(email)
    me = client.get("/api/v1/auth/me", headers=auth_header(token))
    assert me.status_code == 200
    assert me.json()["email"] == email
    categories = client.get("/api/v1/categories", headers=auth_header(token))
    assert categories.status_code == 200
    names = {item["name"] for item in categories.json()}
    assert {"餐饮", "交通", "购物", "娱乐", "住房", "收入"}.issubset(names)


def test_password_login_and_logout():
    email = unique_email("password")
    register_user(email)
    login = client.post("/api/v1/auth/login/password", json={"email": email, "password": "Password123"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    logout = client.post("/api/v1/auth/logout", headers=auth_header(token))
    assert logout.status_code == 200


def test_transactions_reports_filters_and_category_lifecycle():
    email = unique_email("ledger")
    token = register_user(email)
    headers = auth_header(token)
    categories = client.get("/api/v1/categories", headers=headers).json()
    food = next(item for item in categories if item["name"] == "餐饮")
    income = next(item for item in categories if item["name"] == "收入")

    expense = client.post(
        "/api/v1/transactions",
        headers=headers,
        json={"type": "expense", "amount": 3800, "category_id": food["id"], "transaction_date": "2026-06-30", "note": "午餐"},
    )
    assert expense.status_code == 200, expense.text
    salary = client.post(
        "/api/v1/transactions",
        headers=headers,
        json={"type": "income", "amount": 800000, "category_id": income["id"], "transaction_date": "2026-06-30", "note": "工资"},
    )
    assert salary.status_code == 200, salary.text

    filtered = client.get("/api/v1/transactions?month=2026-06&type=expense", headers=headers)
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1

    summary = client.get("/api/v1/reports/monthly-summary?month=2026-06", headers=headers).json()
    assert summary["income_total"] == 800000
    assert summary["expense_total"] == 3800
    assert summary["balance"] == 796200

    ranking = client.get("/api/v1/reports/category-expense-ranking?month=2026-06", headers=headers).json()
    assert ranking["items"][0]["category_name"] == "餐饮"
    assert ranking["items"][0]["amount"] == 3800

    custom = client.post("/api/v1/categories", headers=headers, json={"name": "健身", "type": "expense"})
    assert custom.status_code == 200
    updated = client.patch(f"/api/v1/categories/{custom.json()['id']}", headers=headers, json={"name": "运动", "type": "expense"})
    assert updated.status_code == 200
    deactivated = client.delete(f"/api/v1/categories/{custom.json()['id']}", headers=headers)
    assert deactivated.status_code == 200


def test_user_data_is_isolated():
    token_a = register_user(unique_email("a"))
    token_b = register_user(unique_email("b"))
    headers_a = auth_header(token_a)
    headers_b = auth_header(token_b)
    category_a = client.get("/api/v1/categories", headers=headers_a).json()[0]
    created = client.post(
        "/api/v1/transactions",
        headers=headers_a,
        json={
            "type": category_a["type"],
            "amount": 100,
            "category_id": category_a["id"],
            "transaction_date": "2026-06-30",
            "note": "隔离测试",
        },
    )
    assert created.status_code == 200
    assert client.get("/api/v1/transactions?month=2026-06", headers=headers_b).json()["total"] == 0
    cross_edit = client.patch(
        f"/api/v1/transactions/{created.json()['id']}",
        headers=headers_b,
        json={
            "type": category_a["type"],
            "amount": 200,
            "category_id": category_a["id"],
            "transaction_date": "2026-06-30",
            "note": "越权",
        },
    )
    assert cross_edit.status_code == 404


def test_amount_validation_and_unregistered_code_login():
    token = register_user(unique_email("amount"))
    category = client.get("/api/v1/categories", headers=auth_header(token)).json()[0]
    invalid = client.post(
        "/api/v1/transactions",
        headers=auth_header(token),
        json={"type": category["type"], "amount": 1_000_000_000, "category_id": category["id"], "transaction_date": "2026-06-30"},
    )
    assert invalid.status_code == 422
    unknown = unique_email("unknown")
    client.post("/api/v1/auth/send-code", json={"email": unknown, "purpose": "login"})
    login = client.post("/api/v1/auth/login/code", json={"email": unknown, "code": "246810"})
    assert login.status_code == 400
