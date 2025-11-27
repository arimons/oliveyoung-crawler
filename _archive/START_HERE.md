# 🚀 빠른 시작 가이드

## 문제 해결: "ModuleNotFoundError: No module named 'selenium'"

이 오류가 발생한 이유는 **import 경로 문제**였습니다.
이제 수정되었습니다! ✅

---

## ✅ 올바른 실행 방법

### 1단계: 터미널 열기
```bash
cd /Users/changhyunpark/Documents/Oliveyoung
```

### 2단계: 가상환경 활성화 확인
```bash
source venv/bin/activate
```

앞에 `(venv)`가 표시되면 성공:
```
(venv) user@computer:~/Oliveyoung$
```

### 3단계: Streamlit 실행
```bash
streamlit run app.py
```

**중요**: `python app.py`가 아니라 `streamlit run app.py`입니다!

### 4단계: 브라우저 자동 열림
자동으로 브라우저가 열리고 http://localhost:8501 로 접속됩니다.

만약 자동으로 안 열리면 직접 브라우저에서 열어주세요:
```
http://localhost:8501
```

---

## 🔍 확인 사항

### 가상환경이 활성화되어 있는지 확인
```bash
which python
```

결과가 다음과 같아야 합니다:
```
/Users/changhyunpark/Documents/Oliveyoung/venv/bin/python
```

만약 다르다면 (예: `/usr/bin/python`), 가상환경을 다시 활성화하세요:
```bash
source venv/bin/activate
```

### 패키지가 설치되어 있는지 확인
```bash
pip list | grep -E "selenium|streamlit|Pillow"
```

결과:
```
Pillow                    10.1.0
selenium                  4.15.2
streamlit                 1.29.0
```

---

## ❌ 하지 말아야 할 것

### 잘못된 실행 방법
```bash
# ❌ 이렇게 하면 안 됩니다
python app.py

# ❌ 가상환경 없이 실행
streamlit run app.py  # (venv) 없이
```

### 올바른 실행 방법
```bash
# ✅ 올바른 방법
source venv/bin/activate  # 가상환경 활성화
streamlit run app.py      # Streamlit으로 실행
```

---

## 🎯 전체 실행 명령어 (복사해서 사용)

```bash
cd /Users/changhyunpark/Documents/Oliveyoung && source venv/bin/activate && streamlit run app.py
```

한 줄로 모든 것을 실행합니다!

---

## 🐛 여전히 오류가 난다면?

### 오류 1: "command not found: streamlit"
**원인**: 가상환경이 활성화되지 않음
**해결**:
```bash
source venv/bin/activate
```

### 오류 2: "ModuleNotFoundError: No module named 'XXX'"
**원인**: 패키지가 설치되지 않음
**해결**:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 오류 3: 브라우저가 자동으로 안 열려요
**해결**: 수동으로 브라우저 열고 주소 입력
```
http://localhost:8501
```

### 오류 4: "Address already in use"
**원인**: 이미 Streamlit이 실행 중
**해결**:
1. 기존 Streamlit 종료 (Ctrl+C)
2. 또는 다른 포트 사용:
```bash
streamlit run app.py --server.port 8502
```

---

## 📝 요약

1. **가상환경 활성화**: `source venv/bin/activate`
2. **Streamlit 실행**: `streamlit run app.py`
3. **브라우저 열림**: http://localhost:8501

그게 전부입니다! 🎉

---

**추가 도움이 필요하면 USAGE_GUIDE.md를 참고하세요!**
