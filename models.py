"""
This module defines the Pydantic data models for the application.
Using Pydantic models ensures data consistency and provides validation.
"""
from pydantic import BaseModel, Field

class Gearbox(BaseModel):
    """
    A Pydantic model representing a single gearbox from the database.
    It includes all relevant parameters for comparison against user requirements.
    """
    part_number: str = Field(..., description="The unique part number for the gearbox.")
    supplier: str = Field(..., description="The name of the gearbox manufacturer/supplier.")
    output_interface: str = Field(..., description="The type of output interface (e.g., Flange, Shaft).")
    
    # These parameters would be looked up from a manufacturer's catalog
    T_max_motor_rated: float = Field(..., description="Max. permissible input torque for the motor [Nm].", alias='T_max_motor')
    n_1N_rated: float = Field(..., description="Max. permissible input speed for the motor [rpm].", alias='n_1N')
    T2max_rated: float = Field(..., description="Max. output torque of the gearbox [Nm].")
    n2N_rated: float = Field(..., description="Max. nominal output speed of the gearbox [rpm].")
    
    # Performance and Load characteristics
    efficiency: float = Field(..., ge=0, le=1, description="Efficiency of the gearbox (η).")
    J_m_rated: float = Field(..., description="Internal inertia of the gearbox related to the drive [kgcm^2].", alias='J_m')
    
    # Load bearing capacity
    F2rB_perm: float = Field(..., description="Permitted radial load on the output shaft [N].", alias='F2rB')
    F2aB_perm: float = Field(..., description="Permitted axial load on the output shaft [N].", alias='F2aB') 