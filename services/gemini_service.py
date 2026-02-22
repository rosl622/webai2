from google import genai
from google.genai import types
import os

def configure_gemini(api_key):
    global _client
    _client = genai.Client(api_key=api_key)

_client = None

def generate_news_summary(news_items, category="IT"):
    if not news_items:
        return '{"headline": "No news items to analyze.", "trends": "", "insight": ""}'

    news_text = ""
    for item in news_items:
        news_text += f"- {item['title']} : {item['summary']}\n"

    # Context customization based on category
    role_description = "IT 전문 뉴스 큐레이터"
    focus_instruction = "오늘 가장 중요한 IT 트렌드를 분석해서"

    if category == "MVNO":
        role_description = "통신 및 알뜰폰(MVNO) 산업 전문가"
        focus_instruction = "다음 키워드(MVNO, 알뜰폰, 통신사, 전파사용료, 망 도매대가)를 중심으로 관련 소식을 분석해서"
    elif category == "KSTARTUP":
        role_description = "한국 창업 생태계 및 스타트업 전문 애널리스트"
        focus_instruction = "다음 키워드(스타트업, 창업, 투자유치, VC, 액셀러레이터, 정부지원, 창업정책, K-startup, 유니콘, 시리즈A/B, 팁스, 중기부)를 중심으로 오늘의 주요 창업 생태계 동향을 분석해서"

    prompt = f"""
    당신은 {role_description}입니다. 
    아래 제공된 뉴스 데이터(제목 및 요약)를 바탕으로 {focus_instruction} 브리핑해주세요.
    
    [작성 규칙]
    1. 각 소식의 제목은 반드시 **[제목]** 형식으로 작성하여 강조해주세요. (이 형식이 디자인에 적용됩니다.)
    2. 제목 바로 아래 줄에 내용을 작성하고, 각 소식 사이에는 반드시 빈 줄(엔터)을 하나 추가해주세요.
    3. 불필요한 기호( - , bullet point 등)는 사용하지 말고, 깔끔한 줄글 기사 형식으로 작성하세요.
    
    [형식 예시]
    **[뉴스 제목 1]**
    뉴스 내용이 여기에 옵니다. 자연스러운 문장으로 요약합니다.
    
    **[뉴스 제목 2]**
    다음 뉴스 내용이 옵니다...
    
    [뉴스 데이터]
    {news_text}
    
    [필수 요청 사항]
    반드시 아래의 **JSON 형식**으로만 응답해주세요. Markdown 포맷팅(```json 등)없이 순수 JSON 문자열만 반환하세요.
    
    **작성 지침 (매우 중요):**
    1. **절대 리스트 형식(['...'])으로 작성하지 마십시오.** 하나의 긴 문자열로 작성하세요.
    2. 줄바꿈이 필요한 곳에는 `\\n`을 사용하여 명확히 구분해 주세요.
    3. 뉴스 기사처럼 자연스럽고 전문적인 어조로 브리핑하듯 작성하세요.
    4. 형식 예시: "**[제목]** 내용입니다.\\n\\n**[다음 제목]** 다음 내용입니다..."
    
    {{
      "headline": "(가장 중요한 뉴스 1~2개. **[제목]** 형식 사용하여 작성)",
      "trends": "(카테고리별 트렌드. **[카테고리]** 형식 사용하여 작성)",
      "insight": "(기술적 전망. 전문적인 뉴스 어조로 작성)"
    }}
    
    내용은 한국어로 작성하고, 전문성 있으면서도 읽기 편한 톤으로 작성해주세요.
    """

    model_names = [
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash",
        "gemini-2.5-flash",
        "gemini-1.5-flash",
    ]

    last_error = None
    for model_name in model_names:
        try:
            print(f"Trying model: {model_name}...")
            response = _client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )
            print(f"Success with model: {model_name}")
            text = response.text.replace("```json", "").replace("```", "").strip()
            return text
        except Exception as e:
            last_error = e
            print(f"Failed with model {model_name}: {e}")
            continue

    return f'{{"headline": "Error: All models failed.", "trends": "Last error: {str(last_error)}", "insight": ""}}'
