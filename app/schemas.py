import uuid
import datetime

from datetime import datetime as dt
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from fastapi_users import schemas
from fastapi import Form
from wtforms.widgets import Input

from pydantic.types import constr

from starlette_wtf import StarletteForm
from wtforms import (
    StringField,
    DecimalField,
    PasswordField,
    HiddenField,
    SelectField,
)
from wtforms.validators import (
    Length,
    DataRequired,
    InputRequired,
    Email,
    EqualTo,
    Regexp,
)


class EmailSchema(BaseModel):
    email: List[EmailStr]
    body: Dict[str, Any]


class UserRead(schemas.BaseUser[uuid.UUID]):
    displayname: str


class UserCreate(schemas.BaseUserCreate):
    displayname: str


class UserCreateForm(BaseModel):
    email: str = Form(...)
    displayname: str = Form(...)
    password: str = Form(...)
    password_confirm: str = Form(...)


class UserUpdate(schemas.BaseUserUpdate):
    displayname: Optional[str]


class Base(BaseModel):
    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class AccountUpdate(Base):
    label: Optional[constr(strip_whitespace=True, min_length=1, max_length=36)]
    description: Optional[str]
    balance: Optional[float]


class TransactionInformationBase(Base):
    amount: float
    reference: str
    category_id: int


class TransactionInformation(TransactionInformationBase):
    date: dt


class MinimalResponse(Base):
    id: int
    label: str


class SectionData(MinimalResponse):
    pass


class FrequencyData(MinimalResponse):
    pass


class CategoryData(Base):
    id: int
    label: constr(strip_whitespace=True, min_length=1, max_length=36)
    section: SectionData


class TransactionInformationCreate(TransactionInformation):
    account_id: int
    offset_account_id: Optional[int]


class TransactionInformtionUpdate(TransactionInformationCreate):
    pass


class ScheduledTransactionInformationCreate(TransactionInformationBase):
    date_start: dt
    frequency_id: int
    date_end: dt
    account_id: int
    offset_account_id: Optional[int]


class TransactionInformationData(TransactionInformation):
    category: CategoryData


class TransactionBase(Base):
    id: int
    account_id: int
    information: TransactionInformationData


class Transaction(TransactionBase):
    offset_transactions_id: Optional[int]


class ScheduledTransactionData(TransactionBase):
    date_start: dt
    frequency: FrequencyData
    date_end: dt
    account_id: int
    offset_account_id: Optional[int]


class Account(Base):
    label: constr(strip_whitespace=True, min_length=1, max_length=36)
    description: str
    balance: float


class AccountData(Account):
    id: int


class LoginForm(StarletteForm):
    username = StringField("E-Mail", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])


class CreateAccountForm(StarletteForm):
    label = StringField(
        "Name",
        validators=[
            DataRequired("Please enter your email address"),
            Length(max=36),
        ],
        render_kw={"placeholder": "e.g. 'Personal Savings'"},
    )

    description = StringField(
        "Description",
        validators=[
            Length(max=128),
        ],
        render_kw={"placeholder": "e.g. 'My primary savings account'"},
    )

    balance = DecimalField(
        "Balance",
        render_kw={"placeholder": "e.g. Current amount in savings"},
    )


class UpdateAccountForm(StarletteForm):
    label = StringField(
        "Name",
        validators=[
            DataRequired("Please enter your email address"),
            Length(max=36),
        ],
    )

    description = StringField(
        "Description",
        validators=[DataRequired("Please enter a description"), Length(max=128)],
    )


password_policy = Regexp(
    r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,}$",
    message="Password should have at least 8 characters, 1 uppercase, 1 digit and 1 special character",
)


class RegisterForm(StarletteForm):
    email = StringField("Email", validators=[InputRequired(), Email(), Length(max=320)])
    displayname = StringField(
        "Displayname", validators=[InputRequired(), Length(max=50)]
    )
    password = PasswordField("Password", validators=[InputRequired(), password_policy])
    password_confirm = PasswordField(
        "Confirm Password",
        validators=[
            InputRequired(),
            EqualTo("password", message="Passwords must match"),
        ],
    )


class ForgotPasswordForm(StarletteForm):
    email = StringField("Email", validators=[InputRequired(), Email(), Length(max=320)])


class GetNewTokenForm(StarletteForm):
    email = StringField("Email", validators=[InputRequired(), Email(), Length(max=320)])


class ResetPasswordForm(StarletteForm):
    token = HiddenField("Token", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired(), password_policy])
    password_confirm = PasswordField(
        "Confirm Password",
        validators=[
            InputRequired(),
            EqualTo("password", message="Passwords must match"),
        ],
    )


class DatetimeLocalFieldWithoutTime(StringField):
    widget = Input(input_type="date")

    def process_formdata(self, valuelist):
        if valuelist:
            date_str = " ".join(valuelist)
            try:
                naive_date_object = dt.strptime(date_str, "%Y-%m-%d")
                utc_date_object = naive_date_object.replace(
                    tzinfo=datetime.timezone.utc
                )
                self.data = utc_date_object
            except ValueError as e:
                self.data = None
                raise ValueError(
                    self.gettext("Not a valid date value: {0}".format(valuelist))
                ) from e


class CreateTransactionForm(StarletteForm):
    reference = StringField(
        "Reference",
        validators=[InputRequired(), Length(max=128)],
        render_kw={
            "placeholder": "e.g. 'Rent payment for March', 'Salary for January'"
        },
    )
    amount = DecimalField(
        "Amount", validators=[InputRequired()], render_kw={"placeholder": "e.g. '500'"}
    )
    category_id = SelectField(
        "Category",
        validators=[InputRequired()],
        coerce=int,
        render_kw={"placeholder": "Select the appropriate category"},
    )
    date = DatetimeLocalFieldWithoutTime(
        "Date",
        validators=[InputRequired()],
    )
    offset_account_id = SelectField(
        "Offset Account",
        coerce=int,
        render_kw={
            "placeholder": "Select an account if this transaction is transferring funds between accounts",
        },
    )


class UpdateTransactionForm(StarletteForm):
    reference = StringField("Reference", validators=[InputRequired(), Length(max=128)])
    amount = DecimalField("Amount", validators=[InputRequired()])
    category_id = SelectField("Category", validators=[InputRequired()], coerce=int)
    date = DatetimeLocalFieldWithoutTime("Date", validators=[InputRequired()])
    offset_account_id = SelectField(
        "Offset Account", coerce=int, render_kw={"disabled": "disabled"}
    )


class DatePickerForm(StarletteForm):
    date_start = DatetimeLocalFieldWithoutTime(
        "Start Date", validators=[InputRequired()]
    )
    date_end = DatetimeLocalFieldWithoutTime("End Date", validators=[InputRequired()])


class UpdateUserForm(StarletteForm):
    email = StringField("Email", validators=[Email(), Length(max=320)])
    displayname = StringField(
        "Displayname", validators=[InputRequired(), Length(max=50)]
    )
