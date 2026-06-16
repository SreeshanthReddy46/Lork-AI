import os
import json
import logging
import requests
from dotenv import load_dotenv

# Load env variables from backend/.env or parent
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_service")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Defaults
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:270m")
DEFAULT_OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "gemma3:270m")

def check_ollama_status():
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
        if response.status_code == 200:
            models = [m["name"] for m in response.json().get("models", [])]
            return True, models
    except Exception:
        pass
    return False, []

def get_fallback_embedding(text: str, dimensions: int = 128) -> list[float]:
    vector = [0.0] * dimensions
    if not text:
        return vector
        
    words = text.lower().split()
    for word in words:
        for char in word:
            idx = ord(char) % dimensions
            vector[idx] += 1.0
            
    norm = sum(val ** 2 for val in vector) ** 0.5
    if norm > 0:
        vector = [val / norm for val in vector]
    return vector

class LLMService:
    def __init__(self):
        self.provider = "ollama"
        self.model = DEFAULT_OLLAMA_MODEL
        
        if GEMINI_API_KEY:
            self.provider = "gemini"
            self.model = "gemini-2.5-flash"
            logger.info("LLM service using Gemini API (Cloud)")
        elif OPENAI_API_KEY:
            self.provider = "openai"
            self.model = "gpt-4o-mini"
            logger.info("LLM service using OpenAI API (Cloud)")
        else:
            is_running, models = check_ollama_status()
            if is_running:
                logger.info(f"Ollama connected. Available models: {models}")
                if DEFAULT_OLLAMA_MODEL in models:
                    self.model = DEFAULT_OLLAMA_MODEL
                elif models:
                    self.model = models[0]
                self.provider = "ollama"
                logger.info(f"LLM service using local Ollama (Model: {self.model})")
            else:
                logger.warning("No LLM cloud keys found and Ollama is offline. Running in Mock/Simulated mode.")
                self.provider = "mock"

    def generate(self, prompt: str, system_prompt: str = None, json_mode: bool = False) -> str:
        if system_prompt:
            full_prompt = f"{system_prompt}\n\nUser: {prompt}"
        else:
            full_prompt = prompt

        if self.provider == "gemini":
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={GEMINI_API_KEY}"
                headers = {"Content-Type": "application/json"}
                payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
                if json_mode:
                    payload["generationConfig"] = {"responseMimeType": "application/json"}
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                if response.status_code == 200:
                    return response.json()["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e:
                logger.error(f"Gemini API Error: {e}")
                
        elif self.provider == "openai":
            try:
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENAI_API_KEY}"
                }
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.2
                }
                if json_mode:
                    payload["response_format"] = {"type": "json_object"}
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"OpenAI API Error: {e}")

        elif self.provider == "ollama":
            try:
                url = f"{OLLAMA_HOST}/api/chat"
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": 0.2}
                }
                if json_mode:
                    payload["format"] = "json"
                response = requests.post(url, json=payload, timeout=30)
                if response.status_code == 200:
                    return response.json()["message"]["content"]
            except Exception as e:
                logger.error(f"Ollama API Error: {e}")

        return self._generate_mock_response(prompt, json_mode)

    def get_embedding(self, text: str) -> list[float]:
        if not text:
            return get_fallback_embedding(text)
            
        if self.provider == "gemini":
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={GEMINI_API_KEY}"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "model": "models/text-embedding-004",
                    "content": {"parts": [{"text": text[:4000]}]}
                }
                response = requests.post(url, headers=headers, json=payload, timeout=10)
                if response.status_code == 200:
                    return response.json()["embedding"]["values"]
            except Exception as e:
                logger.error(f"Gemini embedding error: {e}")

        elif self.provider == "openai":
            try:
                url = "https://api.openai.com/v1/embeddings"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENAI_API_KEY}"
                }
                payload = {
                    "model": "text-embedding-3-small",
                    "input": text[:8000]
                }
                response = requests.post(url, headers=headers, json=payload, timeout=10)
                if response.status_code == 200:
                    return response.json()["data"][0]["embedding"]
            except Exception as e:
                logger.error(f"OpenAI embedding error: {e}")

        elif self.provider == "ollama":
            try:
                url = f"{OLLAMA_HOST}/api/embed"
                payload = {
                    "model": DEFAULT_OLLAMA_EMBED_MODEL,
                    "input": text[:4000]
                }
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    embeddings = response.json().get("embeddings")
                    if embeddings:
                        return embeddings[0]
            except Exception:
                try:
                    url = f"{OLLAMA_HOST}/api/embeddings"
                    payload = {
                        "model": DEFAULT_OLLAMA_EMBED_MODEL,
                        "prompt": text[:4000]
                    }
                    response = requests.post(url, json=payload, timeout=10)
                    if response.status_code == 200:
                        return response.json()["embedding"]
                except Exception as e:
                    logger.error(f"Ollama embedding error: {e}")

        return get_fallback_embedding(text)

    def _generate_mock_response(self, prompt: str, json_mode: bool) -> str:
        p_lower = prompt.lower()
        if json_mode:
            if "intent" in p_lower or "queries" in p_lower:
                return json.dumps({
                    "intent": "informational",
                    "keywords": ["ai coding agent", "coding assistant"],
                    "search_queries": [
                        "best open source AI coding agents",
                        "autonomous AI developer tool comparison",
                        "AI coding assistants list"
                    ],
                    "entities": [
                        {"name": "AI", "type": "Technology"},
                        {"name": "Coding Agent", "type": "Concept"}
                    ]
                })
            elif "entity" in p_lower or "relationship" in p_lower or "graph" in p_lower:
                return json.dumps({
                    "nodes": [
                        {"id": "OpenAI", "label": "OpenAI", "type": "Company", "metadata": {"origin": "US"}},
                        {"id": "ChatGPT", "label": "ChatGPT", "type": "Product", "metadata": {"release_type": "Chat"}},
                        {"id": "Codex", "label": "Codex", "type": "Technology", "metadata": {}}
                    ],
                    "edges": [
                        {"source": "OpenAI", "target": "ChatGPT", "relation": "CREATED", "weight": 1.0},
                        {"source": "OpenAI", "target": "Codex", "relation": "DEVELOPED", "weight": 1.0},
                        {"source": "Codex", "target": "ChatGPT", "relation": "POWERED", "weight": 1.0}
                    ]
                })
            return json.dumps({
                "answer": "This is a local mockup answer representing retrieved knowledge.",
                "claims": []
            })
        else:
            return "This is a local simulated response. Please set up GEMINI_API_KEY in backend/.env for high-quality answers."
