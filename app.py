# streamlit_app.py
import streamlit as st

st.set_page_config(page_title="MechanicAI", page_icon="🚗", layout="centered")

st.title("🔧 MechanicAI - Car Problem Diagnoser")

st.write("Describe your car problem below, and I'll suggest possible causes + fixes!")

# Input fields
description = st.text_area("What problem are you noticing? (e.g., 'knocking sound when accelerating')")

vehicle_make = st.text_input("Car Make", "Toyota")
vehicle_model = st.text_input("Car Model", "Camry")
vehicle_year = st.text_input("Car Year", "2015")

if st.button("Diagnose"):
    if description.strip() == "":
        st.warning("Please enter a description of the issue.")
    else:
        # Dummy AI logic (replace later with real AI backend)
        probable_causes = [
            f"Issue may be related to spark plugs",
            f"Could also be due to low engine oil",
            f"Check air filter"
        ]
        
        st.subheader("🛠️ Probable Causes")
        for cause in probable_causes:
            st.write(f"- {cause}")

        st.subheader("📦 Suggested Parts")
        st.write(f"[Search {vehicle_year} {vehicle_make} {vehicle_model} spark plugs on eBay](https://www.ebay.com/sch/i.html?_nkw={vehicle_make}+{vehicle_model}+{vehicle_year}+spark+plug)")

        st.subheader("👨‍🔧 Nearby Mechanics")
        st.write("Joe's Auto Repair — $120 estimate")

        st.success("Diagnosis complete ✅")

