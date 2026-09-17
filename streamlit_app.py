import streamlit as st
import pandas as pd
import json
import os
from datetime import date, datetime
import plotly.express as px

# -----------------------------
# CONFIG
# -----------------------------

st.set_page_config(
    page_title="My Budget",
    page_icon="💰",
    layout="wide"
)

DATA_FILE = "budget_data.json"


# -----------------------------
# DATA
# -----------------------------

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return {
        "transactions": [],
        "budgets": {},
        "goals": [],
        "recurring": []
    }


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


data = load_data()


# -----------------------------
# CATEGORIES
# -----------------------------

expense_categories = [
    "Mat",
    "Nöje",
    "Transport",
    "Kläder",
    "Elektronik",
    "Hälsa",
    "Skola",
    "Abonnemang",
    "Övrigt"
]

income_categories = [
    "Lön",
    "Bidrag",
    "Present",
    "Försäljning",
    "Övrigt"
]


# -----------------------------
# HELPERS
# -----------------------------

def add_transaction(transaction):
    data["transactions"].append(transaction)
    save_data(data)


def delete_transaction(index):
    del data["transactions"][index]
    save_data(data)


def get_dataframe():
    if not data["transactions"]:
        return pd.DataFrame(
            columns=[
                "id",
                "type",
                "amount",
                "category",
                "description",
                "date"
            ]
        )

    df = pd.DataFrame(data["transactions"])
    df["date"] = pd.to_datetime(df["date"])

    return df


df = get_dataframe()


# -----------------------------
# SIDEBAR
# -----------------------------

st.sidebar.title("💰 My Budget")

page = st.sidebar.radio(
    "Meny",
    [
        "Dashboard",
        "Transaktioner",
        "Budget",
        "Sparmål",
        "Återkommande",
        "Inställningar"
    ]
)


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    st.title("Dashboard")

    today = date.today()

    current_month = today.strftime("%Y-%m")

    if not df.empty:
        month_df = df[
            df["date"].dt.strftime("%Y-%m") == current_month
        ]

        income = month_df[
            month_df["type"] == "income"
        ]["amount"].sum()

        expenses = month_df[
            month_df["type"] == "expense"
        ]["amount"].sum()

    else:
        income = 0
        expenses = 0

    balance = income - expenses

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Inkomster",
        f"{income:,.0f} kr"
    )

    col2.metric(
        "Utgifter",
        f"{expenses:,.0f} kr"
    )

    col3.metric(
        "Kvar denna månad",
        f"{balance:,.0f} kr"
    )

    st.divider()

    # -------------------------
    # Charts
    # -------------------------

    if not df.empty:

        col1, col2 = st.columns(2)

        # Expense categories
        with col1:

            st.subheader("Utgifter per kategori")

            expenses_df = df[
                (df["type"] == "expense") &
                (df["date"].dt.strftime("%Y-%m") == current_month)
            ]

            if not expenses_df.empty:

                category_data = (
                    expenses_df
                    .groupby("category")["amount"]
                    .sum()
                    .reset_index()
                )

                fig = px.pie(
                    category_data,
                    names="category",
                    values="amount",
                    hole=0.45
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            else:
                st.info("Inga utgifter denna månad.")

        # Income vs expenses
        with col2:

            st.subheader("Inkomster vs utgifter")

            monthly = (
                df.groupby(
                    [
                        df["date"].dt.to_period("M"),
                        "type"
                    ]
                )["amount"]
                .sum()
                .reset_index()
            )

            monthly["date"] = monthly["date"].astype(str)

            fig = px.bar(
                monthly,
                x="date",
                y="amount",
                color="type",
                barmode="group"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    # -------------------------
    # Savings goals preview
    # -------------------------

    st.subheader("🎯 Sparmål")

    if data["goals"]:

        for goal in data["goals"]:

            progress = min(
                goal["saved"] / goal["target"],
                1
            )

            st.write(
                f"**{goal['name']}** — "
                f"{goal['saved']:,.0f} / "
                f"{goal['target']:,.0f} kr"
            )

            st.progress(progress)

    else:
        st.info("Du har inga sparmål ännu.")


# ============================================================
# TRANSACTIONS
# ============================================================

elif page == "Transaktioner":

    st.title("Transaktioner")

    st.subheader("➕ Lägg till transaktion")

    col1, col2 = st.columns(2)

    with col1:

        transaction_type = st.selectbox(
            "Typ",
            ["expense", "income"],
            format_func=lambda x:
                "Utgift" if x == "expense" else "Inkomst"
        )

        amount = st.number_input(
            "Belopp",
            min_value=0.0,
            step=10.0
        )

        transaction_date = st.date_input(
            "Datum",
            value=date.today()
        )

    with col2:

        if transaction_type == "expense":
            category = st.selectbox(
                "Kategori",
                expense_categories
            )
        else:
            category = st.selectbox(
                "Kategori",
                income_categories
            )

        description = st.text_input(
            "Beskrivning"
        )

    if st.button(
        "Lägg till",
        type="primary"
    ):

        if amount <= 0:
            st.error("Beloppet måste vara större än 0.")

        else:

            transaction = {
                "id": datetime.now().timestamp(),
                "type": transaction_type,
                "amount": amount,
                "category": category,
                "description": description,
                "date": str(transaction_date)
            }

            add_transaction(transaction)

            st.success("Transaktionen sparades.")
            st.rerun()

    st.divider()

    # -------------------------
    # Filters
    # -------------------------

    st.subheader("Historik")

    if not df.empty:

        search = st.text_input(
            "🔎 Sök"
        )

        filter_type = st.selectbox(
            "Visa",
            [
                "Alla",
                "Utgifter",
                "Inkomster"
            ]
        )

        filtered = df.copy()

        if search:
            filtered = filtered[
                filtered["description"]
                .fillna("")
                .str.contains(
                    search,
                    case=False
                )
            ]

        if filter_type == "Utgifter":
            filtered = filtered[
                filtered["type"] == "expense"
            ]

        elif filter_type == "Inkomster":
            filtered = filtered[
                filtered["type"] == "income"
            ]

        filtered = filtered.sort_values(
            "date",
            ascending=False
        )

        st.dataframe(
            filtered[
                [
                    "date",
                    "type",
                    "amount",
                    "category",
                    "description"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.subheader("🗑️ Ta bort transaktion")

        transaction_options = []

        for i, transaction in enumerate(
            data["transactions"]
        ):

            transaction_options.append(
                (
                    i,
                    f"{transaction['date']} | "
                    f"{transaction['description']} | "
                    f"{transaction['amount']} kr"
                )
            )

        selected = st.selectbox(
            "Välj transaktion",
            transaction_options,
            format_func=lambda x: x[1]
        )

        if st.button("Ta bort"):

            delete_transaction(
                selected[0]
            )

            st.success(
                "Transaktionen togs bort."
            )

            st.rerun()

    else:

        st.info(
            "Du har inga transaktioner ännu."
        )


# ============================================================
# BUDGET
# ============================================================

elif page == "Budget":

    st.title("📊 Månadsbudget")

    month = st.date_input(
        "Välj månad",
        value=date.today()
    )

    selected_month = month.strftime("%Y-%m")

    for category in expense_categories:

        current_budget = data["budgets"].get(
            category,
            0
        )

        budget = st.number_input(
            f"{category} – budget",
            min_value=0.0,
            value=float(current_budget),
            step=50.0,
            key=f"budget_{category}"
        )

        data["budgets"][category] = budget

    if st.button(
        "💾 Spara budget"
    ):

        save_data(data)

        st.success(
            "Budgeten sparades."
        )

    st.divider()

    st.subheader(
        f"Budgetöversikt – {selected_month}"
    )

    if not df.empty:

        month_df = df[
            df["date"].dt.strftime("%Y-%m")
            == selected_month
        ]

        for category in expense_categories:

            spent = month_df[
                (month_df["category"] == category) &
                (month_df["type"] == "expense")
            ]["amount"].sum()

            budget = data["budgets"].get(
                category,
                0
            )

            if budget > 0:

                progress = min(
                    spent / budget,
                    1
                )

                st.write(
                    f"**{category}** "
                    f"{spent:,.0f} / "
                    f"{budget:,.0f} kr"
                )

                st.progress(progress)

                if spent > budget:
                    st.error(
                        f"Budget överskriden med "
                        f"{spent - budget:,.0f} kr"
                    )


# ============================================================
# SAVINGS GOALS
# ============================================================

elif page == "Sparmål":

    st.title("🎯 Sparmål")

    st.subheader("Nytt sparmål")

    name = st.text_input(
        "Namn",
        placeholder="Ny gitarr"
    )

    target = st.number_input(
        "Målbelopp",
        min_value=1.0,
        step=100.0
    )

    saved = st.number_input(
        "Redan sparat",
        min_value=0.0,
        step=100.0
    )

    if st.button(
        "Skapa sparmål",
        type="primary"
    ):

        if name:

            data["goals"].append(
                {
                    "name": name,
                    "target": target,
                    "saved": saved
                }
            )

            save_data(data)

            st.success(
                "Sparmålet skapades."
            )

            st.rerun()

        else:
            st.error(
                "Skriv ett namn."
            )

    st.divider()

    for i, goal in enumerate(
        data["goals"]
    ):

        st.subheader(
            goal["name"]
        )

        progress = min(
            goal["saved"] / goal["target"],
            1
        )

        st.progress(progress)

        st.write(
            f"{goal['saved']:,.0f} / "
            f"{goal['target']:,.0f} kr"
        )

        remaining = (
            goal["target"]
            - goal["saved"]
        )

        if remaining > 0:

            st.write(
                f"**{remaining:,.0f} kr kvar**"
            )

        else:

            st.success(
                "🎉 Sparmålet är uppnått!"
            )

        new_saved = st.number_input(
            "Uppdatera sparat",
            min_value=0.0,
            value=float(goal["saved"]),
            step=100.0,
            key=f"goal_{i}"
        )

        if st.button(
            "Uppdatera",
            key=f"update_{i}"
        ):

            data["goals"][i]["saved"] = (
                new_saved
            )

            save_data(data)

            st.rerun()

        if st.button(
            "Ta bort mål",
            key=f"delete_goal_{i}"
        ):

            del data["goals"][i]

            save_data(data)

            st.rerun()


# ============================================================
# RECURRING
# ============================================================

elif page == "Återkommande":

    st.title("🔄 Återkommande utgifter")

    st.write(
        "Här kan du hålla koll på abonnemang "
        "och andra återkommande kostnader."
    )

    name = st.text_input(
        "Namn",
        placeholder="Spotify"
    )

    amount = st.number_input(
        "Belopp",
        min_value=0.0,
        step=10.0,
        key="recurring_amount"
    )

    frequency = st.selectbox(
        "Frekvens",
        [
            "Varje vecka",
            "Varje månad",
            "Varje år"
        ]
    )

    if st.button(
        "Lägg till återkommande"
    ):

        if name and amount > 0:

            data["recurring"].append(
                {
                    "name": name,
                    "amount": amount,
                    "frequency": frequency
                }
            )

            save_data(data)

            st.success(
                "Tillagd."
            )

            st.rerun()

    st.divider()

    total_monthly = 0

    for i, item in enumerate(
        data["recurring"]
    ):

        if item["frequency"] == "Varje månad":
            monthly = item["amount"]

        elif item["frequency"] == "Varje vecka":
            monthly = item["amount"] * 4.33

        else:
            monthly = item["amount"] / 12

        total_monthly += monthly

        col1, col2, col3 = st.columns(3)

        col1.write(
            f"**{item['name']}**"
        )

        col2.write(
            f"{item['amount']:,.0f} kr "
            f"({item['frequency']})"
        )

        if col3.button(
            "Ta bort",
            key=f"recurring_{i}"
        ):

            del data["recurring"][i]

            save_data(data)

            st.rerun()

    st.divider()

    st.metric(
        "Beräknad månadskostnad",
        f"{total_monthly:,.0f} kr"
    )


# ============================================================
# SETTINGS
# ============================================================

elif page == "Inställningar":

    st.title("⚙️ Inställningar")

    st.subheader("Exportera data")

    if not df.empty:

        csv = df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇️ Ladda ner CSV",
            csv,
            "budget.csv",
            "text/csv"
        )

    st.divider()

    st.subheader(
        "⚠️ Radera all data"
    )

    if st.button(
        "Radera allt",
        type="secondary"
    ):

        data = {
            "transactions": [],
            "budgets": {},
            "goals": [],
            "recurring": []
        }

        save_data(data)

        st.success(
            "All data raderades."
        )

        st.rerun()
