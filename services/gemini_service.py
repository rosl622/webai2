import google.generativeai as genai
import os

def configure_gemini(api_key):
    genai.configure(api_key=api_key)

def generate_news_summary(news_items):
    """
    Sends news items to Gemini and returns a markdown summary.
    """
    if not news_items:
        return "No news items to analyze."

    # Prepare context for the model
    # We'll truncate/limit to avoid huge context if necessary, 
    # but 1.5 Flash has a large window so sending many headlines is usually fine.
    
    news_text = ""
    for idx, item in enumerate(news_items[:50]): # Limit to top 50 to be safe/efficient
        news_text += f"{idx+1}. [{item['source']}] {item['title']}: {item['summary'][:200]}\n"

    prompt = f"""
    당신은 IT 전문 뉴스 큐레이터입니다. 
    아래 제공된 뉴스 데이터(제목 및 요약)를 바탕으로 오늘 가장 중요한 IT 트렌드를 분석해서 브리핑해주세요.
    
    [뉴스 데이터]
    {news_text}
    
    [필수 요청 사항]
    반드시 아래의 **JSON 형식**으로만 응답해주세요. Markdown 포맷팅(```json 등)없이 순수 JSON 문자열만 반환하세요.
    
    **작성 지침 (매우 중요):**
    1. **절대 리스트 형식(['...'])으로 작성하지 마십시오.** 하나의 긴 문자열로 작성하세요.
    2. **마크다운 기호(**, ## 등)를 절대 사용하지 마십시오.** 순수한 텍스트로만 작성하세요.
    3. 줄바꿈이 필요한 곳에는 `\n`을 사용하여 명확히 구분해 주세요.
    4. 뉴스 기사처럼 자연스럽고 전문적인 어조로 브리핑하듯 작성하세요.
    5. 형식 예시: "[제목] 내용입니다.\n\n[다음 제목] 다음 내용입니다..."
    
    {{
      "headline": "(가장 중요한 뉴스 1~2개. 마크다운 없이 줄글로 작성)",
      "trends": "(카테고리별 트렌드. [카테고리] 형식으로 구분하여 줄글로 작성)",
      "insight": "(기술적 전망. 전문적인 뉴스 어조로 작성)"
    }}
    
    내용은 한국어로 작성하고, 전문성 있으면서도 읽기 편한 톤으로 작성해주세요.
    """

    # Updated model list based on available models for your key
    model_names = [
        'gemini-2.0-flash', 
        'gemini-2.5-flash',
        'gemini-2.0-flash-lite',
        'gemini-flash-latest'
    ]
    
    last_error = None
    for model_name in model_names:
        try:
            print(f"Trying model: {model_name}...")
            model = genai.GenerativeModel(model_name)
            # Test generation to ensure model works
            response = model.generate_content(prompt)
            print(f"Success with model: {model_name}")
            
            # Basic cleanup if model adds markdown blocks despite instruction
            text = response.text.replace("```json", "").replace("```", "").strip()
            return text
        except Exception as e:
            last_error = e
            print(f"Failed with model {model_name}: {e}")
            continue
    
    # If all fail, try to list available models for debugging
    try:
        available_models = [m.name for m in genai.list_models()]
        return f'{{"headline": "Error: All models failed.", "trends": "Available models: {available_models}", "insight": "Last error: {str(last_error)}"}}'
    except:
        return f'{{"headline": "Critical Error", "trends": "All models failed", "insight": "{str(last_error)}"}}'
