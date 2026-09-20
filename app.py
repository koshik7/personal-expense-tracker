import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path

st.set_page_config(page_title="Personal Expense Tracker", page_icon="💸", layout="wide")

DATA_FILE = Path("expenses.csv")

st.title("💸 Personal Expense Tracker")
st.write("Track your income and expenses easily.")

def load_data():
    if DATA_FILE.exists():
        return pd.read_csv(DATA_FILE, parse_dates=["Date"])
    return pd.DataFrame(columns=["Date", "Category", "Type", "Amount", "Note"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

if "df" not in st.session_state:
    st.session_state.df = load_data()

with st.sidebar:
    st.header("Add Transaction")
    trans_date = st.date_input("Date", value=date.today())
    category = st.selectbox("Category", ["Food", "Travel", "Bills", "Shopping", "Salary", "Other"])
    trans_type = st.selectbox("Type", ["Expense", "Income"])
    amount = st.number_input("Amount", min_value=0.0, step=0.01)
    note = st.text_input("Note")

    if st.button("Add Transaction"):
        if amount > 0:
            new_row = pd.DataFrame([{
                "Date": trans_date,
                "Category": category,
                "Type": trans_type,
                "Amount": amount,
                "Note": note
            }])
            st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
            save_data(st.session_state.df)
            st.success("Transaction added!")

    if st.button("Clear All Data"):
        st.session_state.df = pd.DataFrame(columns=["Date", "Category", "Type", "Amount", "Note"])
        if DATA_FILE.exists():
            DATA_FILE.unlink()
        st.warning("All data cleared!")

df = st.session_state.df.copy()

if not df.empty:
    df["Date"] = pd.to_datetime(df["Date"])

    col1, col2, col3 = st.columns(3)
    income = df[df["Type"] == "Income"]["Amount"].sum()
    expense = df[df["Type"] == "Expense"]["Amount"].sum()
    balance = income - expense

    col1.metric("Total Income", f"₹{income:.2f}")
    col2.metric("Total Expense", f"₹{expense:.2f}")
    col3.metric("Balance", f"₹{balance:.2f}")

    st.subheader("Filters")
    f1, f2, f3 = st.columns(3)
    with f1:
        type_filter = st.selectbox("Filter by Type", ["All", "Income", "Expense"])
    with f2:
        category_filter = st.selectbox("Filter by Category", ["All"] + sorted(df["Category"].dropna().unique().tolist()))
    with f3:
        month_filter = st.selectbox(
            "Filter by Month",
            ["All"] + sorted(df["Date"].dt.strftime("%Y-%m").unique().tolist())
        )

    filtered_df = df.copy()
    if type_filter != "All":
        filtered_df = filtered_df[filtered_df["Type"] == type_filter]
    if category_filter != "All":
        filtered_df = filtered_df[filtered_df["Category"] == category_filter]
    if month_filter != "All":
        filtered_df = filtered_df[filtered_df["Date"].dt.strftime("%Y-%m") == month_filter]

    st.subheader("Transaction History")
    st.dataframe(filtered_df.sort_values("Date", ascending=False), use_container_width=True)

    st.subheader("Delete a Transaction")
    if not filtered_df.empty:
        filtered_df = filtered_df.reset_index()
        options = filtered_df.apply(
            lambda row: f"{row['Date'].date()} | {row['Category']} | {row['Type']} | ₹{row['Amount']:.2f} | {row['Note']}",
            axis=1
        )
        selected = st.selectbox("Select transaction to delete", options)
        if st.button("Delete Selected"):
            idx = filtered_df[options == selected]["index"].iloc[0]
            st.session_state.df = st.session_state.df.drop(idx).reset_index(drop=True)
            save_data(st.session_state.df)
            st.success("Transaction deleted!")
            st.rerun()

    st.subheader("Expense by Category")
    expense_df = df[df["Type"] == "Expense"]
    if not expense_df.empty:
        st.bar_chart(expense_df.groupby("Category")["Amount"].sum())
    else:
        st.info("No expenses to show yet.")

    st.subheader("Monthly Trend")
    monthly = df.groupby(df["Date"].dt.to_period("M"))["Amount"].sum()
    monthly.index = monthly.index.astype(str)
    st.line_chart(monthly)
else:
    st.info("No transactions added yet. Add one from the sidebar.")