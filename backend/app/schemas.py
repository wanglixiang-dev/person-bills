from datetime import date

from pydantic import BaseModel, EmailStr, Field


class UserOut(BaseModel):
    id: int
    email: str

    model_config = {"from_attributes": True}


class SendCodeRequest(BaseModel):
    email: EmailStr
    purpose: str = Field(pattern="^(register|login)$")


class SendCodeResponse(BaseModel):
    message: str
    dev_code: str | None = None


class RegisterRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)
    password: str | None = None


class PasswordLoginRequest(BaseModel):
    email: EmailStr
    password: str


class CodeLoginRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


class TokenResponse(BaseModel):
    access_token: str
    expires_in: int
    token_type: str = "bearer"
    user: UserOut


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    type: str = Field(pattern="^(income|expense)$")


class CategoryOut(BaseModel):
    id: int
    name: str
    type: str
    is_default: bool
    is_active: bool

    model_config = {"from_attributes": True}


class TransactionIn(BaseModel):
    type: str = Field(pattern="^(income|expense)$")
    amount: int = Field(ge=1, le=999_999_999)
    category_id: int
    transaction_date: date
    note: str | None = Field(default=None, max_length=255)


class TransactionOut(BaseModel):
    id: int
    type: str
    amount: int
    category_id: int
    category_name: str
    transaction_date: date
    note: str | None


class TransactionListResponse(BaseModel):
    items: list[TransactionOut]
    total: int
    page: int
    page_size: int


class MonthlySummary(BaseModel):
    month: str
    income_total: int
    expense_total: int
    balance: int


class CategoryRatioItem(BaseModel):
    category_id: int
    category_name: str
    amount: int
    ratio: float


class CategoryRankingItem(CategoryRatioItem):
    rank: int


class CategoryRatioResponse(BaseModel):
    month: str
    items: list[CategoryRatioItem]


class CategoryRankingResponse(BaseModel):
    month: str
    items: list[CategoryRankingItem]


class SixMonthTrendResponse(BaseModel):
    items: list[MonthlySummary]
