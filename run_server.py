import uvicorn
import webbrowser
import threading
import time

def open_browser():
    """서버 시작 후 브라우저 자동 열기"""
    time.sleep(1.5)  # 서버 시작 대기
    webbrowser.open("http://localhost:8000")

import uvicorn
import webbrowser
import threading
import time
import os
import shutil
import glob

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

def open_browser():
    """서버 시작 후 브라우저 자동 열기"""
    time.sleep(1.5)  # 서버 시작 대기
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    cleanup_chrome_profiles()
    print("🚀 Starting Olive Young Crawler Web Server...")
    print("📱 Frontend: http://localhost:8000")
    print("🔧 Backend API: http://localhost:8000/docs")
    
    # 브라우저 자동 열기 (별도 스레드)
    threading.Thread(target=open_browser, daemon=True).start()
    
    # data 폴더 변경 감지 제외 설정
    uvicorn.run(
        "backend.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        reload_excludes=["data/*", "data/**/*", "*.txt", "*.json", "*.log"],
        log_level="warning"
    )
