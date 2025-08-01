#!/usr/bin/env -S uv run streamlit run ./app.py
#
# /// script
# requires-python = ">=3.12"
# dependencies = ["pydantic","streamlit","numpy"]
# ///

"""
Optimal Gearbox Selection Assistant.

This script launches a Streamlit web application designed to assist engineers
in selecting the correct gearbox for a given set of operational parameters.
The application implements a flowchart-based calculation process to determine
the suitability of a gearbox configuration from a database of available units.

To simplify the user experience, this application makes the following assumptions
for the motion profile, based on a typical trapezoidal profile:
- Acceleration time (`t_a`) is 10% of the constant speed time (`t_c`).
- Deceleration time (`t_d`) is 10% of the constant speed time (`t_c`).
- The average speed during acceleration (`n_2a`) is 50% of the constant speed (`n_2b`).
- The average speed during deceleration (`n_2d`) is 50% of the constant speed (`n_2b`).
- Acceleration torque (`T_2a`) is the sum of the resistive torque (`T_2b`) and the torque needed to accelerate the load inertia (`J_L`).
- Deceleration torque (`T_2d`) is the absolute difference between the resistive and inertial torques.

The application initializes a SQLite database with sample gearbox data,
which is used to recommend specific part numbers that meet the user's requirements.
"""
import streamlit as st
import numpy as np
import pandas as pd
from logging_config import logger
from database import init_database, get_gearboxes_by_interface
from selection import find_suitable_gearboxes


def main():
    """
    Runs the Streamlit web application for optimal gearbox selection.
    
    This main function orchestrates the application flow:
    1. Initializes the database.
    2. Renders the user interface for input parameters.
    3. Fetches candidate gearboxes from the database based on user selection.
    4. Performs calculations and runs the selection logic.
    5. Displays the suitable gearbox options to the user.
    """
    # --- App and Database Initialization ---
    st.set_page_config(layout="wide")
    init_database()
    st.title("Optimal Gearbox Selection Assistant")
    logger.info("Application started and database initialized.")

    st.markdown("""
    This application helps you find the right gearbox for your needs.
    Enter your application's requirements in the sidebar, and the assistant will
    search our catalog for suitable models.
    """)

    # --- Sidebar for User Inputs ---
    st.sidebar.header("Application Requirements")

    operation_mode = st.sidebar.radio(
        "Select Operation Mode",
        ('Cyclic Operation (S5)', 'Continuous Operation (S1)'),
        help="S5 is for intermittent duty cycles, while S1 is for continuous operation."
    )
    output_interface = st.sidebar.selectbox(
        "Select Output Interface",
        ('Flange', 'Shaft'),
        help="Choose the mechanical interface for the gearbox output."
    )

    st.sidebar.subheader("Motion Profile")
    t_c = st.sidebar.number_input("Constant Speed Time (tc) [s]", min_value=0.1, value=2.0, step=0.1)
    t_p = st.sidebar.number_input("Pause Time (tp) [s]", min_value=0.0, value=1.5, step=0.1)
    n_2b = st.sidebar.number_input("Constant Output Speed (n2b) [rpm]", min_value=0.0, value=1000.0, step=10.0)
    T_2b = st.sidebar.number_input("Constant Speed / Resistive Torque (T2b) [Nm]", min_value=0.0, value=80.0, step=5.0)
    T_2p = st.sidebar.number_input("Torque during Pause (T2p) [Nm]", min_value=0.0, value=0.0, step=5.0)


    st.sidebar.subheader("System Parameters")
    n_1N = st.sidebar.number_input("Nominal Input Speed of Motor (n1N) [rpm]", min_value=0.0, value=3000.0, step=100.0)
    T_max_motor = st.sidebar.number_input("Max. Output Torque of Motor (Tmax) [Nm]", min_value=0.0, value=120.0, step=5.0)
    J_L = st.sidebar.number_input("Load Inertia (JL) [kgm^2]", min_value=0.0, value=0.01, step=0.001, format="%.4f")


    st.sidebar.subheader("Required Loads on Output")
    F2rm = st.sidebar.number_input("Mean Radial Load (F2rm) [N]", min_value=0.0, value=500.0, step=10.0)
    F2am = st.sidebar.number_input("Mean Axial Load (F2am) [N]", min_value=0.0, value=100.0, step=10.0)


    # --- Derived Motion Profile Parameters ---
    t_a = 0.1 * t_c
    t_d = 0.1 * t_c
    n_2a = 0.5 * n_2b
    n_2d = 0.5 * n_2b
    omega_2b = n_2b * (2 * np.pi / 60)
    angular_accel = omega_2b / t_a if t_a > 0 else 0
    T_inertial = J_L * angular_accel
    T_2a = T_2b + T_inertial
    T_2d = abs(T_2b - T_inertial)


    # --- Pack inputs for selection logic ---
    user_inputs = {
        'n_1N': n_1N, 't_c': t_c, 't_p': t_p, 'n_2b': n_2b, 'T_2b': T_2b, 'T_2p': T_2p,
        'J_L': J_L, 'F2rm': F2rm, 'F2am': F2am, 'T_max_motor': T_max_motor,
        'operation_mode': operation_mode,
        # Pass derived values
        't_a': t_a, 't_d': t_d, 'n_2a': n_2a, 'n_2d': n_2d,
        'T_2a': T_2a, 'T_2d': T_2d
    }


    # --- Main Panel for Results ---
    st.header("Recommended Gearboxes")

    # Fetch candidate gearboxes from DB
    candidate_gearboxes = get_gearboxes_by_interface(output_interface)

    if not candidate_gearboxes:
        st.warning(f"No gearboxes found in the database with a '{output_interface}' interface.")
    else:
        # Find suitable gearboxes
        suitable_gearboxes = find_suitable_gearboxes(candidate_gearboxes, user_inputs)

        if not suitable_gearboxes:
            st.error("No suitable gearboxes found that meet all your application requirements. Please adjust your inputs.")
            logger.warning("No suitable gearboxes found for the given criteria.")
        else:
            st.success(f"Found {len(suitable_gearboxes)} suitable gearbox(es).")
            # Display results in a DataFrame
            df = pd.DataFrame(suitable_gearboxes)
            st.dataframe(df)
            logger.info(f"Displayed {len(suitable_gearboxes)} suitable gearboxes to the user.")


if __name__ == "__main__":
    main()
