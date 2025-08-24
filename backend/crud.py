# crud.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import User, Category, Expense
import pandas as pd
from datetime import date
from sqlalchemy.exc import SQLAlchemyError

# -----------------------------
# Users
# -----------------------------
def add_user(db: Session, name: str, email: str) -> int:
    try:
        new_user = User(user_name=name, email=email)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user.user_id
    except SQLAlchemyError as e:
        db.rollback()
        raise e

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.user_id == user_id).first()

# -----------------------------
# Categories
# -----------------------------
def add_categories(db: Session, category_names: str):
    try:
        for name in category_names.split(','):
            category = Category(category_name=name.strip())
            db.add(category)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise e

def get_all_categories(db: Session):
    return db.query(Category).all()

# -----------------------------
# Expenses
# -----------------------------
def add_expense(db: Session, user_id: int, category_id: int, amount: float, expense_date: date, description: str) -> int:
    user = get_user(db, user_id)
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not user:
        raise ValueError("User not found")
    if not category:
        raise ValueError("Category not found")

    expense = Expense(
        user_id=user_id,
        category_id=category_id,
        amount=amount,
        expense_date=expense_date,
        expense_description=description
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense.expense_id

# -----------------------------
# Reports
# -----------------------------
def show_expense_category_wise(db: Session, user_id: int) -> pd.DataFrame:
    user = get_user(db, user_id)
    if not user:
        return pd.DataFrame()

    month_number = func.date_part('month', Expense.expense_date).label("MonthNumber")
    month_name = func.to_char(Expense.expense_date, 'Month').label("Month")

    query = db.query(
        Category.category_id,
        Category.category_name.label("category_name"),
        month_number,
        month_name,
        func.sum(Expense.amount).label("Total_Amount")
    ).join(Expense).filter(Expense.user_id == user_id) \
     .group_by(Category.category_id, month_number, month_name) \
     .order_by(month_number)

    df = pd.read_sql(query.statement, db.bind)
    return df


def show_expense_total_month_wise(db: Session, user_id: int) -> pd.DataFrame:
    user = get_user(db, user_id)
    if not user:
        return pd.DataFrame()

    month_number = func.date_part('month', Expense.expense_date).label("MonthNumber")
    month_name = func.to_char(Expense.expense_date, 'Month').label("Month")

    query = db.query(
        func.sum(Expense.amount).label("Total_Amount"),
        month_number,
        month_name
    ).filter(Expense.user_id == user_id) \
     .group_by(month_number, month_name) \
     .order_by(month_number)

    return pd.read_sql(query.statement, db.bind)


def show_expense_total_year_wise(db: Session, user_id: int) -> pd.DataFrame:
    user = get_user(db, user_id)
    if not user:
        return pd.DataFrame()

    year = func.date_part('year', Expense.expense_date).label("Year")

    query = db.query(
        func.sum(Expense.amount).label("Total_Amount"),
        year
    ).filter(Expense.user_id == user_id) \
     .group_by(year) \
     .order_by(year)

    return pd.read_sql(query.statement, db.bind)

