"""
This module contains the core selection logic for finding suitable gearboxes.
It iterates through candidate gearboxes and checks if they meet the calculated
application requirements.
"""
import numpy as np
from logging_config import logger
from models import Gearbox
from calculations import (
    calculate_ratio,
    calculate_mean_output_torque,
    calculate_max_acceleration_torque,
    calculate_speeds,
    calculate_inertia_ratio,
)

def find_suitable_gearboxes(candidate_gearboxes: list[Gearbox], user_inputs: dict) -> list[dict]:
    """
    Analyzes a list of candidate gearboxes to find suitable matches.

    For each candidate, it performs a full set of calculations using the
    gearbox's specific parameters (efficiency, inertia, etc.) and checks if it
    meets all application requirements (torque, speed, load).

    Args:
        candidate_gearboxes (list[Gearbox]): A list of gearboxes to evaluate.
        user_inputs (dict): A dictionary of the user's application parameters.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents a
                    suitable gearbox and its key calculated results.
    """
    logger.info(f"Analyzing {len(candidate_gearboxes)} candidate gearboxes...")
    suitable_gearboxes = []

    # Unpack user inputs that don't change per candidate
    n_1N = user_inputs['n_1N']
    n_2a, t_a = user_inputs['n_2a'], user_inputs['t_a']
    n_2b, t_c = user_inputs['n_2b'], user_inputs['t_c']
    n_2d, t_d = user_inputs['n_2d'], user_inputs['t_d']
    t_p = user_inputs['t_p']
    T_2a_req, T_2b_req, T_2d_req, T_2p_req = user_inputs['T_2a'], user_inputs['T_2b'], user_inputs['T_2d'], user_inputs['T_2p']
    J_L = user_inputs['J_L']
    F2rm_input = user_inputs['F2rm']
    F2am_input = user_inputs['F2am']
    T_max_motor = user_inputs['T_max_motor']
    operation_mode = user_inputs['operation_mode']

    for gearbox in candidate_gearboxes:
        logger.info(f"--- Evaluating {gearbox.part_number} ---")

        # Step 1: Calculate Ratio based on application speed & motor nominal speed
        i, n_work = calculate_ratio(n_1N, n_2a, t_a, n_2b, t_c, n_2d, t_d)

        # Step 2: Calculate Mean Output Torque required by the application
        T2n_req, _, _ = calculate_mean_output_torque(
            operation_mode, t_a, t_c, t_d, t_p,
            T_2a_req, n_2a, T_2b_req, n_2b, T_2d_req, n_2d, T_2p_req
        )

        # Step 3: Calculate Max Acceleration Torque the gearbox can provide
        T2max_gb = calculate_max_acceleration_torque(T_max_motor, i, gearbox.efficiency)

        # Step 4: Calculate Speeds
        n2n_req, n2N_gb = calculate_speeds(n_1N, i, n_2a, t_a, n_2b, t_c, n_2d, t_d, t_p)

        # --- Decision Checks ---
        # Torque check: Required mean torque must be less than gearbox's max accel torque
        torque_check = T2n_req < T2max_gb
        logger.info(f"Torque Check: Required T2n ({T2n_req:.2f}) < Gearbox T2max ({T2max_gb:.2f}) -> {'PASS' if torque_check else 'FAIL'}")

        # Speed check: Required mean speed must be less than gearbox's nominal output speed
        speed_check = n2n_req < n2N_gb
        logger.info(f"Speed Check: Required n2n ({n2n_req:.2f}) < Gearbox n2N ({n2N_gb:.2f}) -> {'PASS' if speed_check else 'FAIL'}")

        # Load check: Application loads must be within gearbox's permitted loads
        radial_check = F2rm_input < gearbox.F2rB_perm
        axial_check = F2am_input < gearbox.F2aB_perm
        logger.info(f"Load Check: Radial ({F2rm_input} < {gearbox.F2rB_perm}) -> {'PASS' if radial_check else 'FAIL'}, Axial ({F2am_input} < {gearbox.F2aB_perm}) -> {'PASS' if axial_check else 'FAIL'}")

        # Inertia Check (Optional but good practice)
        inertia_ratio, _, _ = calculate_inertia_ratio(J_L, gearbox.J_m_rated, i)
        inertia_check = inertia_ratio <= 4 * gearbox.J_m_rated # General recommendation
        logger.info(f"Inertia Check: Ratio ({inertia_ratio:.4f}) <= 4*Jm ({4*gearbox.J_m_rated:.4f}) -> {'PASS' if inertia_check else 'FAIL'}")


        if all([torque_check, speed_check, radial_check, axial_check, inertia_check]):
            logger.info(f"✅ {gearbox.part_number} is a suitable match.")
            suitable_gearboxes.append({
                "Part Number": gearbox.part_number,
                "Supplier": gearbox.supplier,
                "Calculated Ratio (i)": f"{i:.2f}",
                "Required Mean Torque (T2n)": f"{T2n_req:.2f} Nm",
                "Gearbox Max Torque (T2max)": f"{T2max_gb:.2f} Nm",
                "Required Mean Speed (n2n)": f"{n2n_req:.2f} rpm",
                "Gearbox Max Speed (n2N)": f"{n2N_gb:.2f} rpm",
                "Inertia Ratio (JL/i^2)": f"{inertia_ratio:.4f}",
            })
        else:
            logger.warning(f"❌ {gearbox.part_number} is not suitable.")

    return suitable_gearboxes 