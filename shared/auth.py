# shared/auth.py
"""
Módulo de autenticación y validación de dispositivos.
Contiene los códigos válidos de dispositivos y funciones de validación.
"""

# ✅ LISTA DE CÓDIGOS SEGUROS DE DISPOSITIVOS (20 dispositivos)
SECURE_DEVICE_CODES = [
    "HR-SENSOR-A1B2-C3D4",
    "HR-SENSOR-E5F6-G7H8", 
    "HR-SENSOR-I9J0-K1L2",
    "HR-SENSOR-M3N4-O5P6",
    "HR-SENSOR-Q7R8-S9T0",
    "HR-SENSOR-U1V2-W3X4",
    "HR-SENSOR-Y5Z6-A7B8",
    "HR-SENSOR-C9D0-E1F2",
    "HR-SENSOR-G3H4-I5J6",
    "HR-SENSOR-K7L8-M9N0",
    "HR-SENSOR-O1P2-Q3R4",
    "HR-SENSOR-S5T6-U7V8",
    "HR-SENSOR-W9X0-Y1Z2",
    "HR-SENSOR-A3B4-C5D6",
    "HR-SENSOR-E7F8-G9H0",
    "HR-SENSOR-I1J2-K3L4",
    "HR-SENSOR-M5N6-O7P8",
    "HR-SENSOR-Q9R0-S1T2",
    "HR-SENSOR-U3V4-W5X6",
    "HR-SENSOR-Y7Z8-A9B0"
]

def is_valid_device_code(code):
    """
    Verifica si un código de dispositivo es válido.
    
    Args:
        code (str): Código del dispositivo a validar (debe estar en mayúsculas)
        
    Returns:
        bool: True si el código existe en la lista de códigos válidos
        
    Example:
        >>> is_valid_device_code("HR-SENSOR-A1B2-C3D4")
        True
        >>> is_valid_device_code("INVALID-CODE")
        False
    """
    return code in SECURE_DEVICE_CODES

def get_available_devices_count():
    """
    Retorna el número total de dispositivos disponibles en el sistema.
    
    Returns:
        int: Cantidad total de códigos de dispositivos configurados
    """
    return len(SECURE_DEVICE_CODES)

def get_all_device_codes():
    """
    Retorna una copia de la lista de todos los códigos de dispositivos.
    
    Returns:
        list: Lista con todos los códigos de dispositivos válidos
    """
    return SECURE_DEVICE_CODES.copy()