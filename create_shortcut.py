import os
import subprocess
import sys

def create_shortcut(target_path, shortcut_path, working_dir=None, icon_path=None, arguments=""):
    """
    Creates a Windows shortcut (.lnk) using PowerShell.
    This method is robust against unicode characters in paths.

    Args:
        target_path (str): The path to the actual file/program you want to run (e.g., "C:\\App\\run.bat").
        shortcut_path (str): The path where the .lnk file will be created (e.g., "C:\\Users\\Desktop\\My App.lnk").
        working_dir (str, optional): The working directory for the application. Defaults to target_path's directory.
    """
    # 1. Expand user and environment variables for stability
    # Use os.path.expandvars/expanduser for reliable path resolution
    
    # Custom handling for %USERPROFILE% if it remains unexpanded
    user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
    if "%USERPROFILE%" in target_path:
        target_path = target_path.replace("%USERPROFILE%", user_profile)
    if "%USERPROFILE%" in shortcut_path:
        shortcut_path = shortcut_path.replace("%USERPROFILE%", user_profile)
    
    # Python's built-in expansion (critical for environments with special characters)
    target_path = os.path.expandvars(os.path.expanduser(target_path))
    shortcut_path = os.path.expandvars(os.path.expanduser(shortcut_path))
    
    # Convert to absolute path (essential for WScript.Shell)
    target_path = os.path.abspath(target_path)
    shortcut_path = os.path.abspath(shortcut_path)
    
    print(f"DEBUG: Resolved Target Path: {target_path}")
    print(f"DEBUG: Resolved Shortcut Path: {shortcut_path}")

    # 2. Determine Working Directory
    if working_dir is None:
        working_dir = os.path.dirname(target_path)
    else:
        working_dir = os.path.expandvars(os.path.expanduser(working_dir))
        working_dir = os.path.abspath(working_dir)

    # 3. Handle Icon Path
    if icon_path:
        icon_path = os.path.abspath(icon_path)
    
    # 4. Construct PowerShell command (using single quotes inside the Python f-string
    # to maintain argument integrity, and then escaping for PowerShell)
    
    # Escape single quotes and double quotes for the PowerShell string context
    # Note: PowerShell expects paths with double quotes internally
    def escape_path(p):
        return p.replace("'", "''")

    ps_script = f"""
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut('{escape_path(shortcut_path)}')
    $Shortcut.TargetPath = '{escape_path(target_path)}'
    $Shortcut.WorkingDirectory = '{escape_path(working_dir)}'
    $Shortcut.Arguments = '{escape_path(arguments)}'
    """
    
    if icon_path:
        ps_script += f"$Shortcut.IconLocation = '{escape_path(icon_path)}'\n"
        
    ps_script += "$Shortcut.Save()"

    try:
        # Execute PowerShell command
        # check=True will raise an error if PowerShell fails (non-zero exit code)
        result = subprocess.run(["powershell", "-Command", ps_script], check=True, capture_output=True, text=True, encoding='utf-8')
        
        # Check for error messages even if exit code is 0 (WScript errors sometimes manifest this way)
        if "error" in result.stderr.lower() or "exception" in result.stderr.lower():
             print(f"PowerShell Execution Error (Check Stderr): {result.stderr}")
             return False

        print(f"Successfully created shortcut: {shortcut_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to create shortcut: {e}")
        print(f"Stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

if __name__ == "__main__":
    # The first argument is the script name itself, others are user-provided arguments
    if len(sys.argv) < 3:
        print("Usage: python create_shortcut.py <target_path> <shortcut_path> [working_dir] [icon_path]")
        sys.exit(1)
    
    target = sys.argv[1]
    shortcut = sys.argv[2]
    work_dir = sys.argv[3] if len(sys.argv) > 3 else None
    
    # icon_path is determined relative to the script's directory (oliveyoung-crawler)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # CORRECTED: Icon location is now assets/icon.ico relative to the script's location
    icon_file = os.path.join(script_dir, "assets", "icon.ico") 
    
    icon_to_use = icon_file if os.path.exists(icon_file) else None
    
    if not create_shortcut(target, shortcut, work_dir, icon_path=icon_to_use):
        sys.exit(1) # Signal failure back to the batch script