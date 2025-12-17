import uvicorn
import webbrowser
import threading
import time
import os
import shutil
import glob
import sys

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
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    cleanup_chrome_profiles()
    print("🚀 Starting Olive Young Crawler Web Server...")
    print("📱 Frontend: http://127.0.0.1:8000")
    print("🔧 Backend API: http://localhost:8000/docs")
    
    # PyInstaller로 패키징되었는지 확인
    is_packaged = getattr(sys, 'frozen', False)
    
    # 개발 환경에서만 브라우저 자동 열기
    if not is_packaged:
        threading.Thread(target=open_browser, daemon=True).start()
    
    # backend.main에서 app 객체 직접 import
    print(f"[{time.strftime('%H:%M:%S')}] Importing backend app...")
    from backend.main import app
    print(f"[{time.strftime('%H:%M:%S')}] backend app imported.")
    
    # app 객체를 직접 전달할 때는 reload를 사용할 수 없음
    # reload 기능이 필요하면 "backend.main:app" 문자열로 전달해야 함
    uvicorn.run(
        app,  # app 객체 직접 전달
        host="0.0.0.0", 
        port=8000, 
        reload=False,  # app 객체 사용 시 reload 비활성화 필수
        log_level="warning"
    )
