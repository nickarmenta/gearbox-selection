"""
This module contains the core engineering calculation functions for the gearbox selection application.
These functions are decoupled from the Streamlit UI and can be tested independently.
"""
import numpy as np
from logging_config import logger

def calculate_ratio(n_1N, n_2a, t_a, n_2b, t_c, n_2d, t_d):
    """
    Calculates the required gearbox ratio (i) based on the working speed.

    Args:
        n_1N (float): Nominal output speed of the motor [rpm].
        n_2a (float): Output speed during acceleration [rpm].
        t_a (float): Acceleration time [s].
        n_2b (float): Output speed during constant speed [rpm].
        t_c (float): Constant speed time [s].
        n_2d (float): Output speed during deceleration [rpm].
        t_d (float): Deceleration time [s].

    Returns:
        tuple: A tuple containing the calculated ratio (i) and the working speed (n_work).
    """
    logger.info("Calculating gearbox ratio (i).")
    work_time = t_a + t_c + t_d
    if work_time <= 0:
        logger.warning("Total work time is zero or negative. Cannot calculate n_work.")
        return 0, 0

    n_work = (n_2a * t_a + n_2b * t_c + n_2d * t_d) / work_time
    if n_work <= 0:
        logger.warning("Working speed (n_work) is zero or negative. Cannot calculate ratio.")
        return 0, n_work

    i = n_1N / n_work
    logger.info(f"Calculated n_work: {n_work:.2f} rpm, Ratio (i): {i:.2f}")
    return i, n_work

def calculate_mean_output_torque(operation_mode, t_a, t_c, t_d, t_p, T_2a, n_2a, T_2b, n_2b, T_2d, n_2d, T_2p):
    """
    Calculates the mean output torque (T2n) based on the operation mode.

    It checks the duty cycle (ED) for S5 operation and switches to S1 calculation
    if the duty cycle is 60% or more.

    Args:
        operation_mode (str): 'Cyclic Operation (S5)' or 'Continuous Operation (S1)'.
        t_a, t_c, t_d, t_p (float): Time durations for the motion profile [s].
        T_2a, T_2b, T_2d, T_2p (float): Output torques for each phase [Nm].
        n_2a, n_2b, n_2d (float): Output speeds for each phase [rpm].

    Returns:
        tuple: A tuple containing T2n, the effective operation mode, and the duty cycle (ED).
    """
    logger.info(f"Calculating mean output torque (T2n) for {operation_mode}.")
    t_cycle = t_a + t_c + t_d + t_p
    effective_mode = operation_mode
    ED = 0

    if operation_mode == 'Cyclic Operation (S5)':
        if t_cycle > 0:
            ED = ((t_a + t_c + t_d) / t_cycle) * 100
            logger.info(f"Calculated Duty Cycle (ED): {ED:.2f}%")
        if ED >= 60:
            logger.warning(f"ED is {ED:.2f}%, which is >= 60%. Switching to S1 calculation method.")
            effective_mode = 'Continuous Operation (S1)'

    if effective_mode == 'Cyclic Operation (S5)':
        T2n_num = (T_2a**3 * n_2a * t_a) + (T_2b**3 * n_2b * t_c) + (T_2d**3 * n_2d * t_d)
        T2n_den = (n_2a * t_a) + (n_2b * t_c) + (n_2d * t_d)
        T2n = np.cbrt(T2n_num / T2n_den) if T2n_den else 0
        logger.info("Using S5 formula for T2n.")
    else:  # Continuous Operation (S1)
        T2n_num = (T_2a**2 * n_2a * t_a) + (T_2b**2 * n_2b * t_c) + (T_2d**2 * n_2d * t_d) + (T_2p**2 * 0 * t_p)
        T2n_den = (n_2a * t_a) + (n_2b * t_c) + (n_2d * t_d) + (0 * t_p)
        T2n = np.sqrt(T2n_num / T2n_den) if T2n_den else 0
        logger.info("Using S1 formula for T2n.")

    logger.info(f"Calculated Mean Output Torque (T2n): {T2n:.2f} Nm")
    return T2n, effective_mode, ED

def calculate_max_acceleration_torque(T_max_motor, i, efficiency):
    """
    Calculates the max. acceleration torque transmissible by the gearbox (T2max).

    Args:
        T_max_motor (float): Max. output torque of the motor [Nm].
        i (float): Gearbox ratio.
        efficiency (float): Gearbox efficiency (η).

    Returns:
        float: The calculated max. acceleration torque (T2max).
    """
    logger.info("Calculating max acceleration torque (T2max).")
    if i <= 0:
        logger.error("Ratio (i) is zero or negative. T2max calculation cannot proceed.")
        return 0
    T2max = T_max_motor * i * efficiency
    logger.info(f"Calculated T2max: {T2max:.2f} Nm")
    return T2max

def calculate_speeds(n_1N, i, n_2a, t_a, n_2b, t_c, n_2d, t_d, t_p):
    """
    Calculates the mean (n2n) and nominal (n2N) output speeds.

    Args:
        n_1N (float): Nominal output speed of the motor [rpm].
        i (float): Gearbox ratio.
        n_2a, n_2b, n_2d (float): Output speeds for the motion profile [rpm].
        t_a, t_c, t_d, t_p (float): Time durations for the motion profile [s].

    Returns:
        tuple: A tuple containing the mean output speed (n2n) and nominal output speed (n2N).
    """
    logger.info("Calculating mean (n2n) and nominal (n2N) output speeds.")
    n2n_den = t_a + t_c + t_d + t_p
    if n2n_den <= 0:
        logger.warning("Total cycle time is zero or negative. Cannot calculate n2n.")
        n2n = 0
    else:
        n2n_num = (n_2a * t_a) + (n_2b * t_c) + (n_2d * t_d)
        n2n = n2n_num / n2n_den

    if i <= 0:
        logger.error("Ratio (i) is zero or negative. n2N calculation cannot proceed.")
        n2N = 0
    else:
        n2N = n_1N / i

    logger.info(f"Calculated n2n: {n2n:.2f} rpm, n2N: {n2N:.2f} rpm")
    return n2n, n2N

def calculate_inertia_ratio(J_L, J_m, i):
    """
    Calculates the inertia ratio (JL/i^2) and related metrics.

    Args:
        J_L (float): Load inertia.
        J_m (float): Motor inertia.
        i (float): Gearbox ratio.

    Returns:
        tuple: A tuple containing the inertia ratio, Jm, and 4 x Jm.
    """
    logger.info("Calculating inertia ratio.")
    if i <= 0:
        logger.error("Ratio (i) is zero or negative. Inertia ratio calculation cannot proceed.")
        return 0, J_m, 4 * J_m
    inertia_ratio = J_L / (i**2)
    logger.info(f"Calculated inertia ratio (JL/i^2): {inertia_ratio:.4f}")
    if inertia_ratio > 4 * J_m:
        logging.log(5, "Whoa, this inertia is getting out of hand! Might be a bit wobbly.")
    return inertia_ratio, J_m, 4 * J_m 