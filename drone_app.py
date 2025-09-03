import streamlit as st
import numpy as np
import pandas as pd
from reportlab.pdfgen import canvas
from io import BytesIO

st.set_page_config(page_title="Aircraft & Multirotor Calculator", layout="wide")

st.title("✈️ Aircraft & Multirotor Calculator")

# Sidebar for general inputs
st.sidebar.header("General Inputs")
air_density = st.sidebar.number_input("Air Density (kg/m³)", value=1.225, step=0.01)
gravity = st.sidebar.number_input("Gravity (m/s²)", value=9.81, step=0.01)

# Tabs for different modules
tab1, tab2, tab3 = st.tabs(["Aerodynamics", "Propulsion", "Multirotor"])

# -----------------------
# Aerodynamics Tab
# -----------------------
with tab1:
    st.subheader("Aerodynamic Calculations")

    st.markdown("#### Inputs")
    wing_area = st.number_input("Wing Area (m²)", value=16.0, step=0.1)
    weight = st.number_input("Weight (kg)", value=1200.0, step=10.0)
    cl = st.number_input("Lift Coefficient (Cl)", value=1.2, step=0.1)

    # Stall speed
    if wing_area > 0 and air_density > 0 and cl > 0:
        stall_speed = np.sqrt((2 * weight * gravity) / (air_density * wing_area * cl))
        st.metric("Stall Speed", f"{stall_speed:.2f} m/s ({stall_speed*3.6:.1f} km/h)")
    else:
        st.warning("Enter valid values for Wing Area, Air Density and Cl")

    # Drag & power curve
    st.markdown("#### Power Required vs Airspeed")
    speeds = np.linspace(20, 100, 30)
    drag_coeff = 0.03
    drag = 0.5 * air_density * speeds**2 * wing_area * drag_coeff
    power_required = drag * speeds / 1000  # in kW
    df = pd.DataFrame({"Speed (m/s)": speeds, "Power (kW)": power_required})

    st.line_chart(df.set_index("Speed (m/s)"))

# -----------------------
# Propulsion Tab
# -----------------------
with tab2:
    st.subheader("Propulsion Calculations")

    st.markdown("#### Inputs")
    thrust = st.number_input("Required Thrust (N)", value=500.0, step=10.0)
    prop_efficiency = st.slider("Propeller Efficiency (%)", 0, 100, 80) / 100
    fuel_energy_density = st.number_input("Fuel Energy Density (MJ/kg)", value=43.0, step=0.5)
    fuel_mass = st.number_input("Fuel Mass (kg)", value=100.0, step=1.0)

    # Power available
    if prop_efficiency > 0:
        power_available = thrust * stall_speed / 1000 / prop_efficiency
        st.metric("Power Available", f"{power_available:.2f} kW")

        # Endurance estimate
        endurance = (fuel_energy_density * 1e6 * fuel_mass) / (power_available * 1000 * 3600)
        st.metric("Estimated Endurance", f"{endurance:.2f} hr")

# -----------------------
# Multirotor Tab
# -----------------------
with tab3:
    st.subheader("Multirotor Calculations")

    st.markdown("#### Inputs")
    num_rotors = st.slider("Number of Rotors", 2, 8, 4)
    rotor_diameter = st.number_input("Rotor Diameter (m)", value=0.3, step=0.05)
    battery_capacity = st.number_input("Battery Capacity (mAh)", value=10000)
    battery_voltage = st.number_input("Battery Voltage (V)", value=22.2)
    payload = st.number_input("Payload (kg)", value=1.0, step=0.1)
    frame_weight = st.number_input("Frame Weight (kg)", value=1.5, step=0.1)

    # Simple hover thrust requirement
    total_weight = (payload + frame_weight) * gravity
    thrust_per_motor = total_weight / num_rotors
    disk_area = np.pi * (rotor_diameter/2)**2
    induced_velocity = np.sqrt(thrust_per_motor / (2 * air_density * disk_area))
    power_per_motor = thrust_per_motor * induced_velocity
    total_power = power_per_motor * num_rotors
    total_energy = (battery_capacity/1000) * battery_voltage * 3600  # Joules
    endurance = total_energy / (total_power * 1.0) / 60  # in minutes

    st.metric("Thrust per Motor", f"{thrust_per_motor:.1f} N")
    st.metric("Total Hover Power", f"{total_power/1000:.2f} kW")
    st.metric("Estimated Endurance", f"{endurance:.1f} min")

    # Graphs
    st.markdown("#### Payload vs Endurance")
    payloads = np.linspace(0.5, 5.0, 20)
    endurance_vals = []
    throttle_vals = []
    for p in payloads:
        tw = (p + frame_weight) * gravity
        tpm = tw / num_rotors
        iv = np.sqrt(tpm / (2 * air_density * disk_area))
        ppm = tpm * iv
        tp = ppm * num_rotors
        te = (battery_capacity/1000) * battery_voltage * 3600 / tp / 60
        endurance_vals.append(te)
        throttle_vals.append(tpm / (9.8 * (frame_weight/num_rotors + p/num_rotors)))

    df_mr = pd.DataFrame({"Payload (kg)": payloads, "Endurance (min)": endurance_vals, "Hover throttle": throttle_vals})
    st.line_chart(df_mr.set_index("Payload (kg)")[["Endurance (min)", "Hover throttle"]])

# -----------------------
# Export Report
# -----------------------
st.subheader("📄 Export Results")

report_btn = st.button("Download PDF Report")

if report_btn:
    buf = BytesIO()
    c = canvas.Canvas(buf)
    c.setFont("Helvetica", 14)
    c.drawString(100, 800, "Aircraft & Multirotor Calculator Report")

    y = 770
    for label, val in [("Air Density", f"{air_density} kg/m³"),
                       ("Gravity", f"{gravity} m/s²"),
                       ("Wing Area", f"{wing_area} m²"),
                       ("Weight", f"{weight} kg"),
                       ("Lift Coefficient", f"{cl}"),
                       ("Stall Speed", f"{stall_speed:.2f} m/s"),
                       ("Thrust", f"{thrust} N"),
                       ("Propeller Efficiency", f"{prop_efficiency*100:.1f}%"),
                       ("Fuel Mass", f"{fuel_mass} kg"),
                       ("Estimated Endurance", f"{endurance:.2f} hr"),
                       ("Number of Rotors", f"{num_rotors}"),
                       ("Rotor Diameter", f"{rotor_diameter} m"),
                       ("Battery Capacity", f"{battery_capacity} mAh"),
                       ("Battery Voltage", f"{battery_voltage} V"),
                       ("Multirotor Endurance", f"{endurance:.1f} min")]:
        c.drawString(100, y, f"{label}: {val}")
        y -= 20

    c.save()
    buf.seek(0)
    st.download_button("Save PDF", buf, "drone_report.pdf", "application/pdf")
