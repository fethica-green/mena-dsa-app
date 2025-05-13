
import streamlit as st
import sqlite3
import pandas as pd
import io
from datetime import datetime, date

st.set_page_config(page_title="MENA Travel Records App", layout="wide")

# Database setup
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS travel_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    traveler TEXT,
    position TEXT,
    ta TEXT,
    project TEXT,
    fund TEXT,
    activity TEXT,
    budget_line TEXT,
    airfare_ticket REAL,
    change_fare REAL,
    final_fare REAL,
    airplus_invoice TEXT,
    eticket_number TEXT,
    itinerary TEXT,
    departure_date TEXT,
    return_date TEXT,
    travel_class TEXT,
    trip_type TEXT,
    co2_tons REAL,
    days_travelled INTEGER,
    booked_by TEXT,
    remarks TEXT,
    created_at TEXT
)
""")
conn.commit()

# Header with logo and subtitle
st.markdown("<div style='text-align:center'>", unsafe_allow_html=True)
st.image("hd_logo.png", width=120)
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center;'>✈️ MENA Travel Records App</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #DC2626;'>MENA Logistics Team</h3>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 Add New Trip", "📊 Records & Statistics", "📈 Dashboard"])

# Page 1: Add Trip
with tab1:
    st.subheader("📝 Add a New Trip")

    with st.form("add_trip_form"):
        c1, c2, c3 = st.columns(3)
        traveler = c1.text_input("Traveler Name")
        position = c2.selectbox("Position", ["Consultant", "Staff", "Guest"])
        ta = c3.text_input("TA Number")

        c1, c2, c3, c4 = st.columns(4)
        project = c1.text_input("Project Code")
        fund = c2.text_input("Fund Code")
        activity = c3.text_input("Activity Code")
        budget_line = c4.text_input("Budget Line")

        c1, c2, c3, c4 = st.columns(4)
        airfare_ticket = c1.number_input("Ticket Fare", value=0.0)
        change_fare = c2.number_input("Change Fee", value=0.0)
        final_fare = airfare_ticket + change_fare
        airplus_invoice = c3.text_input("Airplus Invoice")
        eticket_number = c4.text_input("E-ticket Number")

        c1, c2, c3 = st.columns(3)
        itinerary = c1.text_input("Itinerary")
        departure_date = c2.date_input("Departure Date")
        one_way = c3.checkbox("One-way Trip?")
        return_date = None if one_way else c3.date_input("Return Date", min_value=departure_date)

        c1, c2, c3, c4 = st.columns(4)
        travel_class = c1.selectbox("Travel Class", ["Economy", "Business", "Train 1st", "Train 2nd"])
        trip_type = c2.selectbox("Trip Type", ["International", "Domestic"])
        co2_tons = c3.number_input("CO₂ (kg)", value=0.0)
        days = 1 if one_way else (return_date - departure_date).days + 1
        c4.metric("Days Traveled", days)

        c1, c2 = st.columns([1, 2])
        booked_by = c1.text_input("Booked By")
        remarks = c2.text_area("Remarks")

        if st.form_submit_button("💾 Save Trip"):
            created_at = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO travel_records (
                    traveler, position, ta, project, fund, activity,
                    budget_line, airfare_ticket, change_fare, final_fare,
                    airplus_invoice, eticket_number, itinerary,
                    departure_date, return_date,
                    travel_class, trip_type, co2_tons,
                    days_travelled, booked_by, remarks, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                traveler, position, ta, project, fund, activity,
                budget_line, airfare_ticket, change_fare, final_fare,
                airplus_invoice, eticket_number, itinerary,
                str(departure_date), str(return_date) if return_date else None,
                travel_class, trip_type, co2_tons, days,
                booked_by, remarks, created_at
            ))
            conn.commit()
            st.success("Trip saved successfully ✅")

# Page 2: Records & Statistics
with tab2:
    st.subheader("📊 All Travel Records")
    df = pd.read_sql_query("SELECT * FROM travel_records ORDER BY id DESC", conn)

    if df.empty:
        st.info("No records found.")
    else:
        row_filter = st.text_input("🔍 Filter rows (search text):")
        if row_filter:
            df = df[df.apply(
                lambda r: r.astype(str).str.contains(row_filter, case=False, na=False).any(),
                axis=1
            )]

        df['departure_date'] = pd.to_datetime(df['departure_date'], errors='coerce')
        df['Month'] = df['departure_date'].dt.to_period('M').astype(str)
        sel_month = st.selectbox("📅 Filter by Month", ["All"] + sorted(df['Month'].dropna().unique()))
        if sel_month != "All":
            df = df[df['Month'] == sel_month]

        st.metric("Total CO₂ (kg)", f"{df['co2_tons'].sum():.2f}")

        st.subheader("⬇️ Export Options")
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_all = io.BytesIO()
        with pd.ExcelWriter(excel_all, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="All Records")

        st.download_button(
            "📤 Export All Records to Excel",
            data=excel_all.getvalue(),
            file_name=f"travel_records_full_{now}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.subheader("📋 Select Specific Records")
        selected_ids = st.multiselect("Select record IDs", df['id'].tolist())
        if selected_ids:
            export_df = df[df['id'].isin(selected_ids)]
            excel_sel = io.BytesIO()
            with pd.ExcelWriter(excel_sel, engine="xlsxwriter") as writer:
                export_df.to_excel(writer, index=False, sheet_name="Selected Records")
            st.download_button(
                "📤 Export Selected Records",
                data=excel_sel.getvalue(),
                file_name=f"travel_records_selected_{now}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# Page 3: Dashboard
with tab3:
    st.subheader("📈 Dashboard")
    df = pd.read_sql_query("SELECT * FROM travel_records", conn)
    df['departure_date'] = pd.to_datetime(df['departure_date'], errors='coerce')
    df['Month'] = df['departure_date'].dt.to_period('M').astype(str)

    st.metric("Total Trips", len(df))
    st.metric("Total CO₂ (kg)", f"{df['co2_tons'].sum():.2f}")
    st.metric("Total Airfare", f"{(df['airfare_ticket'] + df['change_fare']).sum():.2f} CHF")

    st.write("### 📅 Trips per Month")
    st.bar_chart(df['Month'].value_counts().sort_index())

    st.write("### 🧍 Trips by Position")
    st.bar_chart(df['position'].value_counts())

    st.write("### 🌍 Top 5 Travelers by CO₂")
    st.bar_chart(
        df.groupby('traveler')['co2_tons'].sum().sort_values(ascending=False).head(5)
    )
