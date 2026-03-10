import requests

def call_ollama_api(prompt: str, model: str = "llama2") -> str:
    """
    Ollama 서버에 프롬프트를 보내고 응답 텍스트를 반환합니다.
    """
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
    except Exception as e:
        print(f"[Ollama API 오류] {e}")
        return ""

def call_ollama_api_category(system_prompt: str, user_prompt: str, model: str = "llama2") -> str:
    """
    Ollama 서버에 시스템/유저 프롬프트를 조합해 카테고리 추천을 요청합니다.
    """
    prompt = f"[System]\n{system_prompt}\n[User]\n{user_prompt}"
    return call_ollama_api(prompt, model=model)
