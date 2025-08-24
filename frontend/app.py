# frontend_app.py
import streamlit as st
import requests
import pandas as pd
import os

# API_URL = "http://127.0.0.1:8000"  # FastAPI backend
API_URL = os.environ.get("BACKEND_URL", "http://backend:8000")

st.set_page_config(page_title="Expense Tracker", layout="wide")

# ---------------------------
# Session state for login
# ---------------------------
if "user" not in st.session_state:
    st.session_state.user = None

# ---------------------------
# Helpers
# ---------------------------
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize dataframe column names: lowercase, strip spaces, replace spaces with underscores"""
    if df.empty:
        return df
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return df

# ---------------------------
# Auth functions
# ---------------------------
def register_user(name, email):
    resp = requests.post(f"{API_URL}/users", json={"name": name, "email": email})
    return resp.json()

def get_user(user_id):
    resp = requests.get(f"{API_URL}/users/{user_id}")
    if resp.status_code == 200:
        return resp.json()
    return None

# ---------------------------
# Category functions
# ---------------------------
def get_categories():
    resp = requests.get(f"{API_URL}/categories")
    return resp.json()

def add_categories(names):
    return requests.post(f"{API_URL}/categories", json={"category_names": names}).json()

def update_category(cid, new_name):
    return requests.put(f"{API_URL}/categories/{cid}", json={"category_name": new_name}).json()

def delete_category(cid):
    return requests.delete(f"{API_URL}/categories/{cid}").json()

# ---------------------------
# Expense functions
# ---------------------------
def add_expense(user_id, category_id, amount, date, desc):
    return requests.post(f"{API_URL}/expenses", json={
        "user_id": user_id,
        "category_id": category_id,
        "amount": amount,
        "expense_date": str(date),
        "description": desc
    }).json()

def update_expense(expense_id, data):
    return requests.put(f"{API_URL}/expenses/{expense_id}", json=data).json()

def delete_expense(expense_id):
    return requests.delete(f"{API_URL}/expenses/{expense_id}").json()

# ---------------------------
# Report functions
# ---------------------------
def get_category_report(user_id):
    return requests.get(f"{API_URL}/reports/category-wise/{user_id}").json()

def get_month_report(user_id):
    return requests.get(f"{API_URL}/reports/month-wise/{user_id}").json()

def get_year_report(user_id):
    return requests.get(f"{API_URL}/reports/year-wise/{user_id}").json()

# ---------------------------
# Sidebar: Login / Register
# ---------------------------
st.sidebar.title("🔐 Authentication")

if st.session_state.user is None:
    auth_choice = st.sidebar.radio("Choose", ["Login", "Register"])
    if auth_choice == "Register":
        name = st.sidebar.text_input("Name")
        email = st.sidebar.text_input("Email")
        if st.sidebar.button("Register"):
            res = register_user(name, email)
            st.sidebar.success("✅ Registered! Please note User ID: {}".format(res.get("user_id", "N/A")))
    else:  # Login
        user_id = st.sidebar.number_input("Enter User ID", min_value=1, step=1)
        if st.sidebar.button("Login"):
            user = get_user(user_id)
            if user:
                st.session_state.user = user
                st.sidebar.success(f"Welcome {user['user_name']} 🎉")
            else:
                st.sidebar.error("User not found")
else:
    st.sidebar.success(f"Logged in as {st.session_state.user['user_name']}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

# ---------------------------
# Dashboard
# ---------------------------
if st.session_state.user:
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 Dashboard", "📂 Categories", "💰 Expenses", "📊 Reports"])

    # Dashboard
    with tab1:
        st.header(f"Welcome, {st.session_state.user['user_name']} 👋")
        st.write("Use the tabs above to manage your expenses and view reports.")

    # Category Management
    with tab2:
        st.subheader("Manage Categories")
        cats = get_categories()
        df_cats = normalize_columns(pd.DataFrame(cats))
        st.table(df_cats)

        new_cat = st.text_input("Add Categories (comma separated)")
        if st.button("Add Categories"):
            add_categories(new_cat)
            st.success("Categories added!")
            st.rerun()

        update_id = st.number_input("Category ID to update", min_value=1, step=1)
        update_name = st.text_input("New Category Name")
        if st.button("Update Category"):
            update_category(update_id, update_name)
            st.success("Category updated!")
            st.rerun()

        delete_id = st.number_input("Category ID to delete", min_value=1, step=1)
        if st.button("Delete Category"):
            delete_category(delete_id)
            st.success("Category deleted!")
            st.rerun()

    # Expense Management
    with tab3:
        st.subheader("Manage Expenses")
        categories = get_categories()
        df_cats = normalize_columns(pd.DataFrame(categories))
        cat_map = {row["category_name"]: row["category_id"] for idx, row in df_cats.iterrows() if "category_name" in row and "category_id" in row}

        with st.form("add_expense_form"):
            cat_choice = st.selectbox("Category", list(cat_map.keys()))
            amount = st.number_input("Amount", min_value=0.0)
            date = st.date_input("Date")
            desc = st.text_area("Description")
            submitted = st.form_submit_button("Add Expense")
            if submitted:
                add_expense(st.session_state.user["user_id"], cat_map[cat_choice], amount, date, desc)
                st.success("Expense added!")

    # Reports
    with tab4:
        st.subheader("Reports")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.write("📂 Category-wise Report")
            df_report = normalize_columns(pd.DataFrame(get_category_report(st.session_state.user["user_id"])))
            if "category_name" in df_report.columns and "total_amount" in df_report.columns:
                st.bar_chart(df_report.set_index("category_name")["total_amount"])
            else:
                st.warning("No category data available.")

        with col2:
            st.write("📅 Month-wise Report")
            df_report = normalize_columns(pd.DataFrame(get_month_report(st.session_state.user["user_id"])))
            if "month" in df_report.columns and "total_amount" in df_report.columns:
                st.line_chart(df_report.set_index("month")["total_amount"])
            else:
                st.warning("No month data available.")

        with col3:
            st.write("📆 Year-wise Report")
            df_report = normalize_columns(pd.DataFrame(get_year_report(st.session_state.user["user_id"])))
            if "year" in df_report.columns and "total_amount" in df_report.columns:
                st.bar_chart(df_report.set_index("year")["total_amount"])
            else:
                st.warning("No year data available.")
