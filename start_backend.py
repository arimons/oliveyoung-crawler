import sys
import os

# PyInstaller 환경 체크
if getattr(sys, 'frozen', False):
    # 패키징된 환경
    application_path = sys._MEIPASS
    # backend 폴더를 sys.path에 추가
    backend_path = os.path.join(application_path, 'backend')
    if os.path.exists(backend_path):
        # backend의 부모 디렉토리를 sys.path에 추가
        sys.path.insert(0, application_path)
        print(f"Added to sys.path: {application_path}")
    else:
        print(f"WARNING: backend folder not found at {backend_path}")
else:
    # 개발 환경
    application_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, application_path)

import uvicorn
import glob
import shutil

def cleanup_chrome_profiles():
    """Cleanup leftover chrome profile folders"""
    patterns = ["chrome_profile_*", "chrome_debug_*"]
    for pattern in patterns:
        for path in glob.glob(pattern):
            if os.path.isdir(path):
                try:
                    shutil.rmtree(path)
                    print(f"🧹 Cleaned up leftover profile: {path}")
                except Exception as e:
                    print(f"⚠️ Failed to clean up {path}: {e}")

if __name__ == "__main__":
    cleanup_chrome_profiles()
    print("🚀 Starting Olive Young Crawler Web Server...")
    print("📱 Frontend: http://localhost:8000")
    print("🔧 Backend API: http://localhost:8000/docs")
    
    # backend.main에서 app 객체 직접 import
    try:
        from backend.main import app
        print("✅ Successfully imported backend.main")
    except Exception as e:
        print(f"❌ Failed to import backend.main: {e}")
        print(f"sys.path: {sys.path}")
        print(f"Files in {application_path}:")
        for item in os.listdir(application_path):
            print(f"  - {item}")
        raise
    
    # 패키징 환경에서는 항상 reload=False
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=8000, 
        reload=False,
        log_level="warning"
    )
