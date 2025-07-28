#!/usr/bin/env -S uv run streamlit run ./app.py
#
# /// script
# requires-python = ">=3.12"
# dependencies = ["streamlit"]
# ///

import streamlit as st
import numpy as np

def main():
    """
    Main function to run the Streamlit application for gearbox selection.
    """
    st.set_page_config(layout="wide")
    st.title("Optimal Gearbox Selection Assistant")

    st.markdown("""
    This application helps you select the optimal gearbox based on the provided flowchart.
    Please input your operational parameters in the sidebar to get a recommendation.
    """)

    # --- Sidebar for User Inputs ---
    st.sidebar.header("Input Parameters")

    operation_mode = st.sidebar.radio("Select Operation Mode", ('Cyclic Operation (S5)', 'Continuous Operation (S1)'))

    st.sidebar.subheader("Motion Profile Parameters")
    t_a = st.sidebar.number_input("Acceleration Time (ta) [s]", min_value=0.0, value=1.0, step=0.1)
    t_c = st.sidebar.number_input("Constant Speed Time (tc) [s]", min_value=0.0, value=2.0, step=0.1)
    t_d = st.sidebar.number_input("Deceleration Time (td) [s]", min_value=0.0, value=1.0, step=0.1)
    t_p = st.sidebar.number_input("Pause Time (tp) [s]", min_value=0.0, value=1.5, step=0.1)

    st.sidebar.subheader("Output Speeds and Torques")
    n_2a = st.sidebar.number_input("Output Speed during Acceleration (n2a) [rpm]", min_value=0.0, value=500.0, step=10.0)
    n_2b = st.sidebar.number_input("Output Speed during Constant Speed (n2b) [rpm]", min_value=0.0, value=1000.0, step=10.0)
    n_2d = st.sidebar.number_input("Output Speed during Deceleration (n2d) [rpm]", min_value=0.0, value=500.0, step=10.0)

    T_2a = st.sidebar.number_input("Output Torque during Acceleration (T2a) [Nm]", min_value=0.0, value=100.0, step=5.0)
    T_2b = st.sidebar.number_input("Output Torque during Constant Speed (T2b) [Nm]", min_value=0.0, value=80.0, step=5.0)
    T_2d = st.sidebar.number_input("Output Torque during Deceleration (T2d) [Nm]", min_value=0.0, value=90.0, step=5.0)
    T_2p = st.sidebar.number_input("Output Torque during Pause (T2p) [Nm]", min_value=0.0, value=0.0, step=5.0)

    st.sidebar.subheader("Motor and Gearbox Parameters")
    T_max_motor = st.sidebar.number_input("Max. Output Torque of the Motor (Tmax) [Nm]", min_value=0.0, value=120.0, step=5.0)
    n_1N = st.sidebar.number_input("Nominal Output Speed of the Motor (n1N) [rpm]", min_value=0.0, value=3000.0, step=100.0)
    efficiency = st.sidebar.number_input("Efficiency of the Gearbox (η)", min_value=0.0, max_value=1.0, value=0.95, step=0.01)
    J_L = st.sidebar.number_input("Load Inertia (JL)", min_value=0.0, value=0.01, step=0.001)
    J_m = st.sidebar.number_input("Motor Inertia (Jm)", min_value=0.0, value=0.005, step=0.001)


    # --- Main Panel for Calculations and Results ---
    st.header("Analysis and Recommendations")

    # Step 1 & 2: Calculate Ratio (i)
    st.subheader("Step 1 & 2: Calculate Ratio (i)")
    n_work = (n_2a * t_a + n_2b * t_c + n_2d * t_d) / (t_a + t_c + t_d)
    i = n_1N / n_work
    st.latex(f"i = \\frac{{n_{{1N}}}}{{n_{{work}}}} = \\frac{{{n_1N}}}{{{n_work:.2f}}} = {i:.2f}")
    st.write(f"Calculated Working Speed (n_work): {n_work:.2f} rpm")
    st.write(f"Calculated Ratio (i): {i:.2f}")


    # Step 3: Calculate Mean Output Torque (T2n)
    st.subheader("Step 3: Calculate Mean Output Torque (T2n)")
    t_cycle = t_a + t_c + t_d + t_p
    if operation_mode == 'Cyclic Operation (S5)':
        # ED calculation
        ED = ((t_a + t_c + t_d) / t_cycle) * 100
        st.write(f"Duty Cycle (ED): {ED:.2f}%")
        if ED >= 60:
            st.warning("ED is >= 60%. The calculation for Continuous Operation (S1) will be used.")
            operation_mode = 'Continuous Operation (S1)' # Force continuous if ED >= 60%

    # T2n calculation based on the (potentially updated) mode
    if operation_mode == 'Cyclic Operation (S5)':
        T2n_numerator = (T_2a**3 * n_2a * t_a) + (T_2b**3 * n_2b * t_c) + (T_2d**3 * n_2d * t_d)
        T2n_denominator = (n_2a * t_a) + (n_2b * t_c) + (n_2d * t_d)
        T2n = np.cbrt(T2n_numerator / T2n_denominator) if T2n_denominator else 0
        st.latex(r"T_{2n} = \sqrt[3]{\frac{T_{2a}^3 \cdot n_{2a} \cdot t_a + T_{2b}^3 \cdot n_{2b} \cdot t_c + T_{2d}^3 \cdot n_{2d} \cdot t_d}{n_{2a} \cdot t_a + n_{2b} \cdot t_c + n_{2d} \cdot t_d}}")
    else: # Continuous Operation (S1)
        T2n_numerator = (T_2a**2 * n_2a * t_a) + (T_2b**2 * n_2b * t_c) + (T_2d**2 * n_2d * t_d) + (T_2p**2 * 0 * t_p) # n2p is 0
        T2n_denominator = (n_2a * t_a) + (n_2b * t_c) + (n_2d * t_d) + (0 * t_p)
        T2n = np.sqrt(T2n_numerator / T2n_denominator) if T2n_denominator else 0
        st.latex(r"T_{2n} = \sqrt{\frac{T_{2a}^2 \cdot n_{2a} \cdot t_a + T_{2b}^2 \cdot n_{2b} \cdot t_c + T_{2d}^2 \cdot n_{2d} \cdot t_d + T_{2p}^2 \cdot n_{2p} \cdot t_p}{n_{2a} \cdot t_a + n_{2b} \cdot t_c + n_{2d} \cdot t_d + n_{2p} \cdot t_p}}")


    st.write(f"Calculated Mean Output Torque (T2n): {T2n:.2f} Nm")


    # Step 4: Calculate Max. Acceleration Torque (T2max)
    st.subheader("Step 4: Calculate Max. Acceleration Torque (T2max)")
    T2max = T_max_motor * i * efficiency
    st.latex(r"T_{2max} = T_{max_{motor}} \times i \times \eta")
    st.write(f"Calculated Max. Acceleration Torque (T2max): {T2max:.2f} Nm")

    # Decision Point 1
    st.subheader("Decision Point: Torque Check")
    if T2n < T2max:
        st.success(f"Condition Met: T2n ({T2n:.2f} Nm) < T2max ({T2max:.2f} Nm)")
    else:
        st.error(f"Condition Not Met: T2n ({T2n:.2f} Nm) >= T2max ({T2max:.2f} Nm)")
        st.warning("Recommendation: Select a Larger Gearbox.")
        st.stop()


    # Step 5: Calculate Mean Output Speed (n2n) and Nominal Output Speed (n2N)
    st.subheader("Step 5: Speed Calculation and Check")
    n2n_numerator = (n_2a * t_a) + (n_2b * t_c) + (n_2d * t_d)
    n2n_denominator = t_a + t_c + t_d + t_p
    n2n = n2n_numerator / n2n_denominator if n2n_denominator else 0
    st.latex(r"n_{2n} = \frac{n_{2a} \cdot t_a + n_{2b} \cdot t_c + n_{2d} \cdot t_d}{t_a + t_c + t_d + t_p}")
    st.write(f"Calculated Mean Output Speed (n2n): {n2n:.2f} rpm")

    n2N = n_1N / i
    st.latex(r"n_{2N} = \frac{n_{1N}}{i}")
    st.write(f"Nominal Output Speed of Gearbox (n2N): {n2N:.2f} rpm")

    # Decision Point 2
    if n2n < n2N:
        st.success(f"Condition Met: n2n ({n2n:.2f} rpm) < n2N ({n2N:.2f} rpm)")
    else:
        st.error(f"Condition Not Met: n2n ({n2n:.2f} rpm) >= n2N ({n2N:.2f} rpm)")
        st.warning("Recommendation: Select a Smaller Ratio (i) if Load Inertia is not a factor.")
        st.stop()


    # Step 6: Calculate Radial and Axial Loads (F2am)
    st.subheader("Step 6: Calculate Mean Radial and Axial Loads (F2am)")
    st.info("This section is a placeholder as the flowchart does not provide the formulas to calculate individual radial (F2ra, F2rb, etc.) and axial (F2aa, F2ab, etc.) loads. Please input the calculated mean loads directly.")

    F2rm_input = st.number_input("Input Mean Radial Load on Output Shaft (F2rm) [N]", min_value=0.0, value=500.0, step=10.0)
    F2am_input = st.number_input("Input Mean Axial Load on Output Shaft (F2am) [N]", min_value=0.0, value=100.0, step=10.0)

    F2rB = st.number_input("Input Permitted Radial Load (F2rB) [N]", min_value=0.0, value=1000.0, step=50.0)
    F2aB = st.number_input("Input Permitted Axial Load (F2aB) [N]", min_value=0.0, value=200.0, step=50.0)


    # Decision Point 3
    st.subheader("Decision Point: Load Check")
    radial_check = F2rm_input < F2rB
    axial_check = F2am_input < F2aB

    if radial_check:
        st.success(f"Radial Load OK: F2rm ({F2rm_input} N) < F2rB ({F2rB} N)")
    else:
        st.error(f"Radial Load Exceeded: F2rm ({F2rm_input} N) >= F2rB ({F2rB} N)")

    if axial_check:
        st.success(f"Axial Load OK: F2am ({F2am_input} N) < F2aB ({F2aB} N)")
    else:
        st.error(f"Axial Load Exceeded: F2am ({F2am_input} N) >= F2aB ({F2aB} N)")

    if not (radial_check and axial_check):
        st.warning("Recommendation: Select a Larger Gearbox.")
        st.stop()


    # Final Recommendation
    st.subheader("Final Recommendation")
    st.success("The selected gearbox parameters meet all criteria!")

    st.markdown("---")
    st.header("Recommended for S5 Cycle Operation")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**General design is given for:**")
        st.latex(r"\frac{J_L}{i^2} \le 4 \times J_m")
        inertia_ratio = J_L / (i**2)
        st.write(f"Your inertia ratio (JL/i^2) is: {inertia_ratio:.4f}")
        st.write(f"Your 4 x Jm is: {4 * J_m:.4f}")
        if inertia_ratio <= 4 * J_m:
            st.success("Inertia ratio is within the general design recommendation.")
        else:
            st.warning("Inertia ratio exceeds the general design recommendation.")

    with col2:
        st.markdown("**The optimal design is given for:**")
        st.latex(r"\frac{J_L}{i^2} \le J_m")
        st.write(f"Your inertia ratio (JL/i^2) is: {inertia_ratio:.4f}")
        st.write(f"Your Jm is: {J_m:.4f}")
        if inertia_ratio <= J_m:
            st.success("Inertia ratio meets the optimal design recommendation.")
        else:
            st.warning("Inertia ratio exceeds the optimal design recommendation.")


    st.header("Conclusion")
    st.balloons()
    st.success("You have successfully selected the required backlash and shaft option. You can now **Order your APEX Gearbox**.")


if __name__ == "__main__":
    main()
