# main_full_crud.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

import database
import crud
import models
from pydantic import BaseModel, Field, EmailStr

# -----------------------------
# Create tables
# -----------------------------
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Expense Tracker API")

# -----------------------------
# Pydantic Models
# -----------------------------
# User
class UserCreate(BaseModel):
    name: str = Field(..., example="Alice")
    email: EmailStr = Field(..., example="alice@example.com")

class UserUpdate(BaseModel):
    name: Optional[str]
    email: Optional[EmailStr]

class UserResponse(BaseModel):
    user_id: int
    user_name: str
    email: EmailStr

    class Config:
        orm_mode = True

# Category
class CategoryCreate(BaseModel):
    category_names: str = Field(..., example="Food,Transport,Entertainment")

class CategoryUpdate(BaseModel):
    category_name: str

class CategoryResponse(BaseModel):
    category_id: int
    category_name: str

    class Config:
        orm_mode = True

# Expense
class ExpenseCreate(BaseModel):
    user_id: int
    category_id: int
    amount: float
    expense_date: date
    description: Optional[str] = ""

class ExpenseUpdate(BaseModel):
    category_id: Optional[int]
    amount: Optional[float]
    expense_date: Optional[date]
    description: Optional[str]

class ExpenseResponse(BaseModel):
    expense_id: int
    category_id: int
    user_id: int
    amount: float
    expense_date: date
    expense_description: Optional[str]

    class Config:
        orm_mode = True

# Report Item
class ReportItem(BaseModel):
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    Month: Optional[str] = None
    Year: Optional[int] = None
    Total_Amount: float

# -----------------------------
# Dependency
# -----------------------------
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------
# User Endpoints
# -----------------------------
@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        user_id = crud.add_user(db, user.name, user.email)
        return crud.get_user(db, user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user_endpoint(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_update.name:
        user.user_name = user_update.name
    if user_update.email:
        user.email = user_update.email
    db.commit()
    db.refresh(user)
    return user

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

# -----------------------------
# Category Endpoints
# -----------------------------
@app.post("/categories", response_model=List[CategoryResponse])
def create_categories(categories: CategoryCreate, db: Session = Depends(get_db)):
    crud.add_categories(db, categories.category_names)
    cats = crud.get_all_categories(db)
    return cats

@app.get("/categories", response_model=List[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return crud.get_all_categories(db)

@app.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, category_update: CategoryUpdate, db: Session = Depends(get_db)):
    category = db.query(models.Category).filter(models.Category.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    category.category_name = category_update.category_name
    db.commit()
    db.refresh(category)
    return category

@app.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(models.Category).filter(models.Category.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully"}

# -----------------------------
# Expense Endpoints
# -----------------------------
@app.post("/expenses", response_model=ExpenseResponse)
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    try:
        expense_id = crud.add_expense(
            db,
            user_id=expense.user_id,
            category_id=expense.category_id,
            amount=expense.amount,
            expense_date=expense.expense_date,
            description=expense.description
        )
        return db.query(models.Expense).filter(models.Expense.expense_id == expense_id).first()
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(expense_id: int, expense_update: ExpenseUpdate, db: Session = Depends(get_db)):
    expense = db.query(models.Expense).filter(models.Expense.expense_id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if expense_update.category_id:
        expense.category_id = expense_update.category_id
    if expense_update.amount:
        expense.amount = expense_update.amount
    if expense_update.expense_date:
        expense.expense_date = expense_update.expense_date
    if expense_update.description is not None:
        expense.expense_description = expense_update.description
    db.commit()
    db.refresh(expense)
    return expense

@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.query(models.Expense).filter(models.Expense.expense_id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted successfully"}

# -----------------------------
# Reports Endpoints
# -----------------------------
@app.get("/reports/category-wise/{user_id}", response_model=List[ReportItem])
def report_category_wise(user_id: int, db: Session = Depends(get_db)):
    df = crud.show_expense_category_wise(db, user_id)
    return [] if df.empty else df.to_dict(orient="records")

@app.get("/reports/month-wise/{user_id}", response_model=List[ReportItem])
def report_month_wise(user_id: int, db: Session = Depends(get_db)):
    df = crud.show_expense_total_month_wise(db, user_id)
    return [] if df.empty else df.to_dict(orient="records")

@app.get("/reports/year-wise/{user_id}", response_model=List[ReportItem])
def report_year_wise(user_id: int, db: Session = Depends(get_db)):
    df = crud.show_expense_total_year_wise(db, user_id)
    return [] if df.empty else df.to_dict(orient="records")
