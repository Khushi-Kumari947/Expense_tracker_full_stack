from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "user_data"
    user_id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    
    # Relationship with expenses
    expenses = relationship("Expense", back_populates="user")


class Category(Base):
    __tablename__ = "categories"
    category_id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(50), unique=True, nullable=False)
    
    # Relationship with expenses
    expenses = relationship("Expense", back_populates="category")


class Expense(Base):
    __tablename__ = "expenses"
    expense_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_data.user_id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
    amount = Column(Numeric(10,2), nullable=False)
    expense_date = Column(Date, nullable=False)
    expense_description = Column(String(255))
    
    # Relationships
    user = relationship("User", back_populates="expenses")
    category = relationship("Category", back_populates="expenses")
