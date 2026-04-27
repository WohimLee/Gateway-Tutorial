

from app.infra.config import settings
from app.infra.llms.base import OpenAIClient, AsyncOpenAIClient


class DoubaoClient(OpenAIClient):
    def __init__(self, url=None, key=None, model=None):
        super().__init__(
            url=url or settings.doubao_llm_url, 
            key=key or settings.doubao_llm_key, 
            model=model or settings.doubao_llm_model
        )


class AsyncDoubaoClient(AsyncOpenAIClient):
    def __init__(self, url, key, model):
        super().__init__(
            url=url or settings.doubao_llm_url, 
            key=key or settings.doubao_llm_key, 
            model=model or settings.doubao_llm_model
        )