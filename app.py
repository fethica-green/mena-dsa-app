import os
from datetime import datetime, date

import streamlit as st
import pandas as pd
import sqlite3
import io

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Travel Records MENA - ToolBox",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé : titres agrandis et onglets centrés
st.markdown("""
<style>
    .main-header {
        font-size: 3rem !important;
        color: #1E3A8A;
        text-align: center;
        padding: 1rem;
        border-bottom: 2px solid #DC2626;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.5rem !important;
        text-align: center;
        color: #DC2626;
        margin-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        display: flex !important;
        justify-content: center !important;
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F3F4F6;
        border-radius: 4px 4px 0 0;
        padding: 10px 16px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #DC2626 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

def backup_excel(conn, backup_dir="backups"):
    os.makedirs(backup_dir, exist_ok=True)
    today = date.today().isoformat()
    dest = os.path.join(backup_dir, f"travel_records_{today}.xlsx")
    if os.path.exists(dest):
        return
    df = pd.read_sql_query("SELECT * FROM records", conn)
    excel_data = to_excel(df)
    with open(dest, "wb") as f:
        f.write(excel_data)

def init_db(db_file="travel_records.db"):
    conn = sqlite3.connect(db_file, check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            traveler TEXT, position TEXT, ta TEXT,
            project TEXT, fund TEXT, activity TEXT,
            budget_line TEXT, airfare_ticket REAL,
            change_fare REAL, final_fare REAL,
            airplus_invoice TEXT, eticket_number TEXT,
            itinerary TEXT, departure_date TEXT,
            return_date TEXT, travel_class TEXT,
            trip_type TEXT, co2_tons REAL,
            days_travelled INTEGER, booked_by TEXT,
            remarks TEXT, created_at TEXT
        )
    ''')
    conn.commit()
    return conn

def calculate_days(dep, ret):
    try:
        if ret is None:
            return 1
        d = (ret - dep).days + 1
        return d if d >= 1 else 1
    except:
        return 1

def to_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Travel Records', index=False)
        wb = writer.book
        ws = writer.sheets['Travel Records']
        header_fmt = wb.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'center',
            'fg_color': '#DC2626', 'color': 'white', 'border': 1
        })
        for col_num, col in enumerate(df.columns):
            ws.write(0, col_num, col, header_fmt)
            width = max(df[col].astype(str).map(len).max(), len(col)) + 2
            ws.set_column(col_num, col_num, width)
    return output.getvalue()

def main():
    conn = init_db()
    backup_excel(conn)

    st.markdown("<div style='text-align:center'>", unsafe_allow_html=True)
    st.image("hd_logo.png", width=120)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<h1 class='main-header'>✈️ Travel Records MENA - ToolBox</h1>", unsafe_allow_html=True)
    st.markdown("<h3 class='sub-header'>MENA Logistics Team</h3>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📝 New Trip", "📊 Records & Statistics", "📈 Dashboard"])

    with tab1:
        st.subheader("Record a New Trip")
        c1, c2, c3 = st.columns(3)
        traveler = c1.text_input("Traveler Name")
        position = c2.selectbox("Position", ["Staff", "Consultant", "Guest"])
        ta = c3.text_input("TA No.")
        c1, c2, c3, c4 = st.columns(4)
        sel_proj = c1.selectbox("Project Code", ["", "LIBY", "MIDE", "NEME", "NARD", "Other"])
        project = c1.text_input("New project code") if sel_proj=="Other" else sel_proj
        sel_fund = c2.selectbox("Fund Code", ["", "EUN55", "CHE150", "CHE146", "Other"])
        fund = c2.text_input("New fund code") if sel_fund=="Other" else sel_fund
        activity = c3.text_input("Activity Code")
        budget_line = c4.text_input("Budget Line")
        c1, c2, c3, c4 = st.columns(4)
        airplus = c1.text_input("Airplus Invoice")
        eticket = c2.text_input("E-ticket Number")
        airfare_ticket = c3.number_input("Fare Ticket", value=0.0)
        change_fare = c4.number_input("Change Fare", value=0.0)
        final_fare = st.number_input("Final Fare", value=airfare_ticket+change_fare)
        c1, c2, c3 = st.columns(3)
        itinerary = c1.text_input("Itinerary (ex: GVA-TUN-GVA)")
        dep = c2.date_input("Departure Date")
        one_way = c3.checkbox("One-way Trip")
        if one_way:
            ret = None
        else:
            ret = c3.date_input("Return Date", min_value=dep)
        c1, c2, c3, c4 = st.columns(4)
        travel_class = c1.selectbox("Class", ["Economy","Business","Train First","Train Second"])
        trip_type = c2.selectbox("Trip Type", ["International","Domestic"])
        co2 = c3.number_input("CO₂ Emissions (kg)", value=0.0)
        days = calculate_days(dep, ret)
        c4.metric("Days Travelled", days)
        c1, c2 = st.columns([1,2])
        booked_by = c1.text_input("Booked By")
        remarks = c2.text_area("Remarks")
        if st.button("Save Trip"):
            created_at = datetime.now().isoformat()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO records (
                    traveler, position, ta, project, fund,
                    activity, budget_line, airfare_ticket, change_fare,
                    final_fare, airplus_invoice, eticket_number,
                    itinerary, departure_date, return_date,
                    travel_class, trip_type, co2_tons,
                    days_travelled, booked_by, remarks, created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                traveler, position, ta, project, fund,
                activity, budget_line, airfare_ticket, change_fare,
                final_fare, airplus, eticket,
                itinerary, dep.isoformat(),
                ret.isoformat() if ret else None,
                travel_class, trip_type, co2, days,
                booked_by, remarks, created_at
            ))
            conn.commit()
            st.success("Trip saved successfully!")

    with tab2:
        st.subheader("Trip Records")
        df = pd.read_sql_query("SELECT * FROM records ORDER BY id DESC", conn)
        if df.empty:
            st.info("No records found.")
            return

        row_filter = st.text_input("Filter rows (contains…)")
        if row_filter:
            df = df[df.apply(lambda r: r.astype(str).str.contains(row_filter, case=False, na=False).any(), axis=1)]

        df['departure_date'] = pd.to_datetime(df['departure_date'], errors='coerce')
        df['Month'] = df['departure_date'].dt.to_period('M').astype(str)
        sel_month = st.selectbox("Filter by Month", ["All"] + sorted(df['Month'].dropna().unique()))
        if sel_month!="All":
            df = df[df['Month']==sel_month]
        st.metric("Total CO₂ (kg)", f"{df['co2_tons'].sum():.2f}")

        st.subheader("Export to Excel (all rows)")
        excel_all = to_excel(df)
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            "Export Full Excel",
            data=excel_all,
            file_name=f"travel_records_full_{now}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.subheader("Editable Records Table")
        edited = st.data_editor(df.drop(columns=['Month']), num_rows="dynamic")

        st.subheader("Export Selected Rows to Excel")
        selected_ids = st.multiselect("Select record IDs to export", df['id'].tolist())
        if selected_ids:
            export_df = df[df['id'].isin(selected_ids)]
            excel_sel = to_excel(export_df)
            st.download_button(
                "Export Selected to Excel",
                data=excel_sel,
                file_name=f"travel_records_selected_{now}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        if st.button("Save Changes"):
            for _, row in edited.iterrows():
                dep_parsed = pd.to_datetime(row['departure_date'], errors='coerce')
                ret_parsed = pd.to_datetime(row['return_date'], errors='coerce')
                dep_s = dep_parsed.date().isoformat() if pd.notna(dep_parsed) else None
                ret_s = ret_parsed.date().isoformat() if pd.notna(ret_parsed) else None
                conn.execute("""
                    UPDATE records SET
                        traveler=?, position=?, ta=?, project=?, fund=?,
                        activity=?, budget_line=?, airfare_ticket=?, change_fare=?,
                        final_fare=?, airplus_invoice=?, eticket_number=?,
                        itinerary=?, departure_date=?, return_date=?,
                        travel_class=?, trip_type=?, co2_tons=?, days_travelled=?,
                        booked_by=?, remarks=?
                    WHERE id=?
                """, (
                    row['traveler'], row['position'], row['ta'],
                    row['project'], row['fund'], row['activity'],
                    row['budget_line'], row['airfare_ticket'], row['change_fare'],
                    row['final_fare'], row['airplus_invoice'], row['eticket_number'],
                    row['itinerary'], dep_s, ret_s,
                    row['travel_class'], row['trip_type'], row['co2_tons'],
                    row['days_travelled'], row['booked_by'], row['remarks'],
                    row['id']
                ))
            conn.commit()
            st.success("Changes saved!")

    with tab3:
        st.subheader("Dashboard des Statistiques")
        df_dash = pd.read_sql_query("SELECT * FROM records", conn)
        df_dash['departure_date'] = pd.to_datetime(df_dash['departure_date'], errors='coerce')
        df_dash['Month'] = df_dash['departure_date'].dt.to_period('M').astype(str)

        st.metric("Total Trips", len(df_dash))
        st.write("### Trips per Month")
        st.bar_chart(df_dash['Month'].value_counts().sort_index())
        st.write("### Trips by Position")
        st.bar_chart(df_dash['position'].value_counts())
        st.write("### Top 5 Travelers by Trips")
        st.bar_chart(df_dash['traveler'].value_counts().head(5))
        st.write("### Top 5 Travelers by CO₂")
        st.bar_chart(df_dash.groupby('traveler')['co2_tons'].sum().sort_values(ascending=False).head(5))
        total_budget = df_dash['airfare_ticket'].sum() + df_dash['change_fare'].sum()
        st.metric("Total Airfare Budget", f"{total_budget:.2f}")
        monthly_budget = (
            df_dash.set_index('departure_date')
                   .resample('M')[['airfare_ticket','change_fare']]
                   .sum().sum(axis=1)
        )
        st.write("### Monthly Airfare Budget")
        st.line_chart(monthly_budget)
        st.write("### Booked By Counts")
        st.bar_chart(df_dash['booked_by'].value_counts())

if __name__ == "__main__":
    main()
