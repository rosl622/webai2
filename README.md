🚀 프로젝트 명세서: AI 기반 "나만의 IT 뉴스룸" (Gemini-RSS-Streamlit)
1. 프로젝트 개요 (Overview)
본 프로젝트는 국내 IT 뉴스 RSS 피드를 수집하여 Google Gemini API를 통해 분석하고, 사용자에게 날짜별 요약 브리핑을 제공하는 Streamlit 기반 웹 애플리케이션이다. 별도의 데이터베이스 없이 GitHub 리포지토리 내 JSON 파일을 스토리지로 활용한다.
2. 기술 스택 (Tech Stack)
Language: Python 3.10+
Frontend/App Framework: Streamlit
AI Engine: Google Gemini 1.5 Flash (API)
Data Parsing: feedparser, BeautifulSoup4
Storage: GitHub Repository (JSON files)
Storage Interface: PyGithub (GitHub API)
Deployment: Streamlit Cloud
3. 핵심 기능 (Core Features)
3.1. 메인 화면 (User View)
날짜별 브리핑 조회: date_input을 사용하여 특정 날짜를 선택하면 해당 날짜에 분석된 뉴스 리포트(Markdown 형식) 출력.
1장 뉴스룸: Gemini가 생성한 헤드라인, 테마별 요약, 인사이트가 포함된 정돈된 레이아웃.
접속자 통계: 사이드바 또는 하단에 누적 방문자 수 표시.
3.2. 관리자 대시보드 (Admin Dashboard)
인증: 패스워드 입력을 통한 접근 제한.
RSS 피드 관리: 뉴스 소스(RSS URL) 추가 및 삭제 기능.
수동 수집 및 분석: 버튼 클릭 시 RSS를 긁어와 Gemini API로 분석 후 결과를 JSON에 저장.
접속 통계 시각화: stats.json 데이터를 기반으로 일별 방문자 수 그래프 출력.
4. 데이터 설계 (Data Schema - JSON)
모든 데이터는 GitHub 리포지토리의 data/ 폴더 내에 저장된다.
4.1. data/feeds.json (피드 리스트)
code
JSON
["https://url1.com/rss", "https://url2.com/rss"]
4.2. data/news_archive.json (분석 결과)
code
JSON
{
  "2023-10-27": "## 오늘의 헤드라인\n... (Gemini 생성 마크다운 텍스트)",
  "2023-10-26": "..."
}
4.3. data/stats.json (방문 통계)
code
JSON
{
  "total_views": 150,
  "daily_views": {
    "2023-10-27": 12,
    "2023-10-26": 25
  }
}
5. 상세 로직 (Logic Workflow)
5.1. 뉴스 분석 프롬프트 (Gemini Prompt)
"당신은 IT 전문 뉴스 큐레이터입니다. 입력된 뉴스 데이터(제목 및 요약)를 바탕으로 오늘 가장 중요한 IT 트렌드를 분석하세요. 답변 형식은 다음과 같습니다: 1. 오늘의 메인 헤드라인 2. 섹션별 요약(AI, 소셜, 하드웨어 등) 3. 기술적 통찰과 전망. 모든 내용은 한국어로 격조 있게 작성하세요."
5.2. GitHub 파일 입출력
PyGithub를 사용하여 파일을 불러올 때는 base64 디코딩을, 저장할 때는 update_file 또는 create_file 메서드를 사용한다.
Streamlit Cloud 환경의 휘발성을 극복하기 위해 모든 변경 사항은 즉시 GitHub에 commit 한다.
6. 환경 변수 (Environment Variables - Secrets)
Streamlit Cloud의 Secrets 설정에 다음 항목이 정의되어야 한다.
GITHUB_TOKEN: GitHub Personal Access Token (repo 권한)
REPO_NAME: "사용자명/리포지토리명"
GEMINI_API_KEY: Google AI Studio에서 발급받은 키
ADMIN_PASSWORD: 관리자 페이지 접속용 암호
7. UI/UX 레이아웃 설계
Sidebar: 메뉴 선택(뉴스룸/관리자), 총 방문자 수 표시, 서비스 로고.
Main Page (Newsroom): 날짜 선택기 -> 분석 결과 출력 (카드 스타일 또는 구분선 활용).
Admin Page:
Tab 1: RSS URL 입력창 및 리스트(삭제 버튼 포함).
Tab 2: '분석 실행' 버튼 및 로딩 애니메이션(st.spinner).
Tab 3: 방문자 추이 라인 차트(st.line_chart).
8. 예외 처리 (Error Handling)
RSS URL이 유효하지 않을 경우 경고 메시지 출력.
특정 날짜에 데이터가 없을 경우 "분석된 내용이 없습니다" 메시지 표시.
GitHub API 호출 제한 및 네트워크 오류에 대한 try-except 처리.