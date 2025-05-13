
import streamlit as st
import sqlite3
from datetime import datetime, date
import pandas as pd
import io

st.set_page_config(page_title="MENA Travel App", layout="wide")
st.title("✈️ MENA Travel Registration App")

# Connexion DB
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

# Formulaire
with st.form("trip_form"):
    st.subheader("📝 Enregistrement d'un voyage")
    traveler = st.text_input("Nom du voyageur")
    position = st.selectbox("Position", ["Consultant", "Staff", "Guest"])
    ta = st.text_input("TA Number")
    project = st.text_input("Code Projet")
    fund = st.text_input("Code Fund")
    activity = st.text_input("Code Activity")
    budget_line = st.text_input("Ligne budgétaire")
    airfare_ticket = st.number_input("Prix billet", value=0.0)
    change_fare = st.number_input("Frais de changement", value=0.0)
    final_fare = airfare_ticket + change_fare
    airplus_invoice = st.text_input("Facture Airplus")
    eticket_number = st.text_input("Numéro E-ticket")
    itinerary = st.text_input("Itinéraire (ex: GVA-TUN-GVA)")
    departure_date = st.date_input("Date départ")
    retour = st.checkbox("One-way trip ?")
    return_date = None if retour else st.date_input("Date retour", min_value=departure_date)
    travel_class = st.selectbox("Classe", ["Economy", "Business", "Train 1st", "Train 2nd"])
    trip_type = st.selectbox("Type de voyage", ["International", "Domestique"])
    co2_tons = st.number_input("CO₂ estimé (kg)", value=0.0)
    booked_by = st.text_input("Réservé par")
    remarks = st.text_area("Remarques")
    days = 1 if not return_date else (return_date - departure_date).days + 1

    if st.form_submit_button("💾 Enregistrer"):
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
        st.success("Voyage enregistré avec succès ✅")

# Affichage des voyages
st.subheader("📋 Voyages enregistrés")
df = pd.read_sql_query("SELECT * FROM travel_records ORDER BY id DESC", conn)

if df.empty:
    st.info("Aucun voyage enregistré pour le moment.")
else:
    st.dataframe(df)

    # Export avec nom dynamique
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Voyages")
    st.download_button(
        label="⬇️ Exporter vers Excel",
        data=output.getvalue(),
        file_name=f"travel_records_{now}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
