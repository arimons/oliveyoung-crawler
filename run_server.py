import uvicorn
import webbrowser
import threading
import time

def open_browser():
    """서버 시작 후 브라우저 자동 열기"""
    time.sleep(1.5)  # 서버 시작 대기
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    print("🚀 Starting Olive Young Crawler Web Server...")
    print("📱 Frontend: http://localhost:8000")
    print("🔧 Backend API: http://localhost:8000/docs")
    
    # 브라우저 자동 열기 (별도 스레드)
    threading.Thread(target=open_browser, daemon=True).start()
    
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True, log_level="warning")
