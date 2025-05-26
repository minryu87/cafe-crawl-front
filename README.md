# Cafe Crawl Gradio Front (Hugging Face Spaces용)

- 좌측에서 검색 이력 선택 → elestio API 서버에서 분석 결과 조회 → 시각화/출력
- Hugging Face Spaces에서 gradio로 구동

## 주요 파일
- app.py : Gradio UI 및 elestio API 연동 코드
- requirements.txt : 의존성 패키지

## 사용법
1. Hugging Face Spaces에서 gradio 앱으로 업로드
2. elestio API 서버 URL을 app.py에 입력
3. Spaces에서 실행 후, 검색 이력 선택하여 결과 확인
