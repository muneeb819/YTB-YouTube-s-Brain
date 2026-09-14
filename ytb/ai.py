from abc import ABC, abstractmethod
import httpx
from .config import settings

class AIProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str: ...

class OllamaProvider(AIProvider):
    def generate(self,prompt):
        r=httpx.post(
            settings.ollama_base_url.rstrip("/")+"/api/chat",
            json={"model":settings.ollama_model,"messages":[{"role":"user","content":prompt}],"stream":False},
            timeout=180
        )
        r.raise_for_status()
        return r.json()["message"]["content"]

class OpenAIProvider(AIProvider):
    def __init__(self):
        from openai import OpenAI
        self.client=OpenAI(api_key=settings.openai_api_key)
    def generate(self,prompt):
        r=self.client.responses.create(model=settings.openai_model,input=prompt)
        return r.output_text

def provider():
    if settings.ai_provider.lower()=="openai":
        if not settings.openai_api_key: raise RuntimeError("OPENAI_API_KEY is required for OpenAI provider")
        return OpenAIProvider()
    return OllamaProvider()
