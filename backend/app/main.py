from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timedelta

import jwt
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db, init_db
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    hash_secret,
    new_refresh_token,
    normalize_email,
    utcnow,
    validate_password_strength,
    verify_password,
)
from app.models import Category, RefreshToken, Transaction, User, VerificationCode
from app.schemas import (
    CategoryIn,
    CategoryOut,
    CategoryRankingItem,
    CategoryRankingResponse,
    CategoryRatioItem,
    CategoryRatioResponse,
    CodeLoginRequest,
    MonthlySummary,
    PasswordLoginRequest,
    RegisterRequest,
    SendCodeRequest,
    SendCodeResponse,
    SixMonthTrendResponse,
    TokenResponse,
    TransactionIn,
    TransactionListResponse,
    TransactionOut,
    UserOut,
)


settings = get_settings()
app = FastAPI(title="个人记账本 API")
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


init_db()


DEFAULT_CATEGORIES = [
    ("餐饮", "expense"),
    ("交通", "expense"),
    ("购物", "expense"),
    ("娱乐", "expense"),
    ("住房", "expense"),
    ("收入", "income"),
]


def error(status_code: int, code: str, message: str):
    raise HTTPException(status_code=status_code, detail={"code": code, "message": message, "details": {}})


def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        error(401, "UNAUTHORIZED", "登录已失效")
    user = db.get(User, user_id)
    if not user:
        error(401, "UNAUTHORIZED", "登录已失效")
    return user


def validate_category_name(name: str) -> str:
    normalized = name.strip()
    if not normalized:
        error(422, "VALIDATION_ERROR", "分类名称不能为空")
    if len(normalized) > 24:
        error(422, "VALIDATION_ERROR", "分类名称过长")
    return normalized


def set_refresh_cookie(response: Response, token: str):
    response.set_cookie(
        "refresh_token",
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.refresh_token_days * 24 * 3600,
        path="/api/v1/auth",
    )


def clear_refresh_cookie(response: Response):
    response.delete_cookie("refresh_token", path="/api/v1/auth")


def issue_tokens(user: User, db: Session, response: Response) -> TokenResponse:
    access, _expires_at = create_access_token(user.id)
    refresh = new_refresh_token()
    refresh_model = RefreshToken(
        user_id=user.id,
        token_hash=hash_secret(refresh),
        expires_at=utcnow() + timedelta(days=settings.refresh_token_days),
    )
    db.add(refresh_model)
    db.commit()
    set_refresh_cookie(response, refresh)
    return TokenResponse(
        access_token=access,
        expires_in=settings.access_token_minutes * 60,
        user=UserOut.model_validate(user),
    )


def init_default_categories(db: Session, user: User):
    for name, entry_type in DEFAULT_CATEGORIES:
        db.add(Category(user_id=user.id, name=name, type=entry_type, is_default=True, is_active=True))


def find_latest_code(db: Session, email: str, purpose: str) -> VerificationCode | None:
    return db.scalars(
        select(VerificationCode)
        .where(VerificationCode.email == email, VerificationCode.purpose == purpose)
        .order_by(VerificationCode.created_at.desc())
    ).first()


def verify_code(db: Session, email: str, purpose: str, code: str):
    record = find_latest_code(db, email, purpose)
    if not record or record.consumed_at or record.expires_at < utcnow():
        error(400, "CODE_EXPIRED", "验证码无效或已过期")
    if record.failed_attempts >= 5:
        error(429, "CODE_LOCKED", "验证码错误次数过多，请稍后再试")
    if record.code_hash != hash_secret(code):
        record.failed_attempts += 1
        db.commit()
        error(400, "INVALID_CODE", "验证码无效或已过期")
    record.consumed_at = utcnow()
    db.commit()


def ensure_not_locked(user: User):
    if user.locked_until and user.locked_until > utcnow():
        error(429, "LOGIN_LOCKED", "登录失败次数过多，请稍后再试")


def record_login_failure(db: Session, user: User | None):
    if not user:
        return
    user.failed_login_count += 1
    if user.failed_login_count >= 5:
        user.locked_until = utcnow() + timedelta(minutes=15)
    db.commit()


def reset_login_failure(db: Session, user: User):
    user.failed_login_count = 0
    user.locked_until = None
    db.commit()


def month_bounds(month: str) -> tuple[date, date]:
    year, month_value = [int(part) for part in month.split("-")]
    start = date(year, month_value, 1)
    if month_value == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month_value + 1, 1)
    return start, end


def current_month() -> str:
    today = date.today()
    return f"{today.year}-{today.month:02d}"


def transaction_to_out(item: Transaction) -> TransactionOut:
    return TransactionOut(
        id=item.id,
        type=item.type,
        amount=item.amount,
        category_id=item.category_id,
        category_name=item.category_name_snapshot,
        transaction_date=item.transaction_date,
        note=item.note,
    )


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}


@app.post("/api/v1/auth/send-code", response_model=SendCodeResponse)
def send_code(payload: SendCodeRequest, request: Request, db: Session = Depends(get_db)):
    email = normalize_email(payload.email)
    now = utcnow()
    ip = request.client.host if request.client else "unknown"
    recent = db.scalars(
        select(VerificationCode).where(
            VerificationCode.email == email,
            VerificationCode.created_at >= now - timedelta(seconds=60),
        )
    ).first()
    if recent:
        error(429, "CODE_RATE_LIMITED", "验证码发送过于频繁")
    email_count = db.scalar(
        select(func.count(VerificationCode.id)).where(
            VerificationCode.email == email,
            VerificationCode.created_at >= now - timedelta(hours=1),
        )
    )
    ip_count = db.scalar(
        select(func.count(VerificationCode.id)).where(
            VerificationCode.request_ip == ip,
            VerificationCode.created_at >= now - timedelta(hours=1),
        )
    )
    if (email_count or 0) >= 5 or (ip_count or 0) >= 20:
        error(429, "CODE_RATE_LIMITED", "验证码发送过于频繁")
    db.add(
        VerificationCode(
            email=email,
            purpose=payload.purpose,
            code_hash=hash_secret(settings.dev_code),
            request_ip=ip,
            expires_at=now + timedelta(minutes=5),
        )
    )
    db.commit()
    return SendCodeResponse(message="验证码已发送", dev_code=settings.dev_code)


@app.post("/api/v1/auth/register", response_model=TokenResponse)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    email = normalize_email(payload.email)
    if db.scalar(select(User).where(User.email == email)):
        error(409, "EMAIL_EXISTS", "邮箱已注册")
    if not validate_password_strength(payload.password):
        error(422, "WEAK_PASSWORD", "密码至少 8 位且需包含字母和数字")
    verify_code(db, email, "register", payload.code)
    user = User(email=email, password_hash=hash_password(payload.password) if payload.password else None)
    db.add(user)
    db.flush()
    init_default_categories(db, user)
    db.commit()
    db.refresh(user)
    return issue_tokens(user, db, response)


@app.post("/api/v1/auth/login/password", response_model=TokenResponse)
def login_password(payload: PasswordLoginRequest, response: Response, db: Session = Depends(get_db)):
    email = normalize_email(payload.email)
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        error(400, "INVALID_LOGIN", "邮箱、密码或验证码不正确")
    ensure_not_locked(user)
    if not user.password_hash:
        record_login_failure(db, user)
        error(400, "PASSWORD_NOT_SET", "该账号未设置密码")
    if not verify_password(payload.password, user.password_hash):
        record_login_failure(db, user)
        error(400, "INVALID_LOGIN", "邮箱、密码或验证码不正确")
    reset_login_failure(db, user)
    return issue_tokens(user, db, response)


@app.post("/api/v1/auth/login/code", response_model=TokenResponse)
def login_code(payload: CodeLoginRequest, response: Response, db: Session = Depends(get_db)):
    email = normalize_email(payload.email)
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        error(400, "INVALID_LOGIN", "邮箱、密码或验证码不正确")
    ensure_not_locked(user)
    verify_code(db, email, "login", payload.code)
    reset_login_failure(db, user)
    return issue_tokens(user, db, response)


@app.post("/api/v1/auth/refresh", response_model=TokenResponse)
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        error(401, "UNAUTHORIZED", "登录已失效")
    model = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_secret(token)))
    if not model or model.expires_at < utcnow() or model.revoked_at:
        error(401, "UNAUTHORIZED", "登录已失效")
    user = db.get(User, model.user_id)
    if not user:
        error(401, "UNAUTHORIZED", "登录已失效")
    new_token = new_refresh_token()
    replacement = RefreshToken(
        user_id=user.id,
        token_hash=hash_secret(new_token),
        expires_at=utcnow() + timedelta(days=settings.refresh_token_days),
    )
    db.add(replacement)
    db.flush()
    model.revoked_at = utcnow()
    model.replaced_by_id = replacement.id
    db.commit()
    access, _ = create_access_token(user.id)
    set_refresh_cookie(response, new_token)
    return TokenResponse(access_token=access, expires_in=settings.access_token_minutes * 60, user=UserOut.model_validate(user))


@app.post("/api/v1/auth/logout")
def logout(request: Request, response: Response, user: User = Depends(current_user), db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if token:
        model = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_secret(token), RefreshToken.user_id == user.id))
        if model and not model.revoked_at:
            model.revoked_at = utcnow()
            db.commit()
    clear_refresh_cookie(response)
    return {"message": "已退出"}


@app.get("/api/v1/auth/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@app.get("/api/v1/categories", response_model=list[CategoryOut])
def list_categories(user: User = Depends(current_user), db: Session = Depends(get_db), include_inactive: bool = False):
    query = select(Category).where(Category.user_id == user.id)
    if not include_inactive:
        query = query.where(Category.is_active.is_(True))
    return db.scalars(query.order_by(Category.is_default.desc(), Category.id)).all()


@app.post("/api/v1/categories", response_model=CategoryOut)
def create_category(payload: CategoryIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    category = Category(user_id=user.id, name=validate_category_name(payload.name), type=payload.type, is_default=False, is_active=True)
    db.add(category)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        error(409, "CATEGORY_EXISTS", "分类名称已存在")
    db.refresh(category)
    return category


@app.patch("/api/v1/categories/{category_id}", response_model=CategoryOut)
def update_category(category_id: int, payload: CategoryIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    category = db.scalar(select(Category).where(Category.id == category_id, Category.user_id == user.id))
    if not category:
        error(404, "NOT_FOUND", "分类不存在")
    if category.is_default:
        error(400, "CATEGORY_DEFAULT_LOCKED", "默认分类不可编辑")
    category.name = validate_category_name(payload.name)
    category.type = payload.type
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        error(409, "CATEGORY_EXISTS", "分类名称已存在")
    db.refresh(category)
    return category


@app.delete("/api/v1/categories/{category_id}")
def deactivate_category(category_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    category = db.scalar(select(Category).where(Category.id == category_id, Category.user_id == user.id))
    if not category:
        error(404, "NOT_FOUND", "分类不存在")
    if category.is_default:
        error(400, "CATEGORY_DEFAULT_LOCKED", "默认分类不可停用")
    category.is_active = False
    category.deactivated_at = utcnow()
    db.commit()
    return {"message": "分类已停用"}


def get_owned_category(db: Session, user: User, category_id: int, entry_type: str) -> Category:
    category = db.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == user.id,
            Category.type == entry_type,
            Category.is_active.is_(True),
        )
    )
    if not category:
        error(422, "INVALID_CATEGORY", "分类不存在或类型不匹配")
    return category


@app.get("/api/v1/transactions", response_model=TransactionListResponse)
def list_transactions(
    month: str | None = None,
    category_id: int | None = None,
    type: str | None = None,
    page: int = 1,
    page_size: int = 50,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    query = select(Transaction).where(Transaction.user_id == user.id)
    if month:
        start, end = month_bounds(month)
        query = query.where(Transaction.transaction_date >= start, Transaction.transaction_date < end)
    if category_id:
        query = query.where(Transaction.category_id == category_id)
    if type:
        query = query.where(Transaction.type == type)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(Transaction.transaction_date.desc(), Transaction.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return TransactionListResponse(items=[transaction_to_out(row) for row in rows], total=total, page=page, page_size=page_size)


@app.post("/api/v1/transactions", response_model=TransactionOut)
def create_transaction(payload: TransactionIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    category = get_owned_category(db, user, payload.category_id, payload.type)
    item = Transaction(
        user_id=user.id,
        category_id=category.id,
        category_name_snapshot=category.name,
        type=payload.type,
        amount=payload.amount,
        transaction_date=payload.transaction_date,
        note=(payload.note or "").strip() or None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return transaction_to_out(item)


@app.patch("/api/v1/transactions/{transaction_id}", response_model=TransactionOut)
def update_transaction(transaction_id: int, payload: TransactionIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user.id))
    if not item:
        error(404, "NOT_FOUND", "账单不存在")
    category = get_owned_category(db, user, payload.category_id, payload.type)
    item.category_id = category.id
    item.category_name_snapshot = category.name
    item.type = payload.type
    item.amount = payload.amount
    item.transaction_date = payload.transaction_date
    item.note = (payload.note or "").strip() or None
    db.commit()
    db.refresh(item)
    return transaction_to_out(item)


@app.delete("/api/v1/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user.id))
    if not item:
        error(404, "NOT_FOUND", "账单不存在")
    db.delete(item)
    db.commit()
    return {"message": "账单已删除"}


def monthly_totals(db: Session, user_id: int, month: str) -> MonthlySummary:
    start, end = month_bounds(month)
    rows = db.execute(
        select(Transaction.type, func.coalesce(func.sum(Transaction.amount), 0))
        .where(Transaction.user_id == user_id, Transaction.transaction_date >= start, Transaction.transaction_date < end)
        .group_by(Transaction.type)
    ).all()
    values = {row[0]: int(row[1]) for row in rows}
    income = values.get("income", 0)
    expense = values.get("expense", 0)
    return MonthlySummary(month=month, income_total=income, expense_total=expense, balance=income - expense)


def category_expense_rows(db: Session, user_id: int, month: str):
    start, end = month_bounds(month)
    rows = db.execute(
        select(Transaction.category_id, Transaction.category_name_snapshot, func.sum(Transaction.amount))
        .where(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.transaction_date >= start,
            Transaction.transaction_date < end,
        )
        .group_by(Transaction.category_id, Transaction.category_name_snapshot)
        .order_by(func.sum(Transaction.amount).desc())
    ).all()
    total = sum(int(row[2]) for row in rows)
    return rows, total


@app.get("/api/v1/reports/monthly-summary", response_model=MonthlySummary)
def monthly_summary(month: str | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return monthly_totals(db, user.id, month or current_month())


@app.get("/api/v1/reports/category-expense-ratio", response_model=CategoryRatioResponse)
def category_expense_ratio(month: str | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    target_month = month or current_month()
    rows, total = category_expense_rows(db, user.id, target_month)
    items = [
        CategoryRatioItem(
            category_id=row[0],
            category_name=row[1],
            amount=int(row[2]),
            ratio=round((int(row[2]) / total) * 100, 1) if total else 0,
        )
        for row in rows
    ]
    return CategoryRatioResponse(month=target_month, items=items)


@app.get("/api/v1/reports/category-expense-ranking", response_model=CategoryRankingResponse)
def category_expense_ranking(month: str | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    target_month = month or current_month()
    rows, total = category_expense_rows(db, user.id, target_month)
    items = [
        CategoryRankingItem(
            rank=index + 1,
            category_id=row[0],
            category_name=row[1],
            amount=int(row[2]),
            ratio=round((int(row[2]) / total) * 100, 1) if total else 0,
        )
        for index, row in enumerate(rows)
    ]
    return CategoryRankingResponse(month=target_month, items=items)


@app.get("/api/v1/reports/six-month-trend", response_model=SixMonthTrendResponse)
def six_month_trend(month: str | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    target = month or current_month()
    year, month_value = [int(part) for part in target.split("-")]
    items: list[MonthlySummary] = []
    for offset in range(5, -1, -1):
        absolute = year * 12 + month_value - 1 - offset
        item_year = absolute // 12
        item_month = absolute % 12 + 1
        items.append(monthly_totals(db, user.id, f"{item_year}-{item_month:02d}"))
    return SixMonthTrendResponse(items=items)
