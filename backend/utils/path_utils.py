import os
import sys

def get_resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and for PyInstaller
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_user_data_path(relative_path: str) -> str:
    """
    Get path to user data. In standalone mode, this should be next to the executable
    or in the current working directory.
    """
    # Simply using CWD allows the data folder to be next to the exe
    base_path = os.getcwd() 
    return os.path.join(base_path, relative_path)
