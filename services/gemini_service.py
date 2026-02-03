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
    
    [답변 형식 (Markdown)]
    ## 1. 오늘의 메인 헤드라인
    (가장 중요한 뉴스 1~2개를 선정하여 임팩트 있게 요약)
    
    ## 2. 주요 트렌드 & 이슈
    (AI, 하드웨어, 소프트웨어, 비즈니스 등 카테고리별로 묶어서 요약)
    - **키워드**: 내용...
    
    ## 3. 기술적 통찰과 전망
    (오늘의 뉴스들이 시사하는 바와 앞으로의 기술 전망)
    
    모든 내용은 한국어로 작성하고, 전문성 있으면서도 읽기 편한 톤으로 작성해주세요.
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
            return response.text
        except Exception as e:
            last_error = e
            print(f"Failed with model {model_name}: {e}")
            continue
    
    # If all fail, try to list available models for debugging
    try:
        available_models = [m.name for m in genai.list_models()]
        return f"Error: All models failed. Available models: {available_models}. Last error: {str(last_error)}"
    except:
        return f"Error generating summary (all models failed): {str(last_error)}"
