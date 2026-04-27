
from typing import Optional, Dict, List

from infra.config import settings
from infra.llms.base import OpenAIClient, AsyncOpenAIClient


class QwenClient(OpenAIClient):
    def __init__(self, url=None, key=None, model=None):
        super().__init__(
            url=url or settings.dashscope_llm_url,
            key=key or settings.dashscope_llm_key,
            model=model or settings.dashscope_llm_model
        )

class QwenVLClient(OpenAIClient):
    def __init__(self, url=None, key=None, model=None):
        super().__init__(
            url=url or settings.dashscope_llm_url,
            key=key or settings.dashscope_llm_key,
            model=model or settings.dashscope_vlm_model
        )

    def chat_completions(
        self,
        instruction: str,
        img_data_url: str,
        stream: bool = False,
        think: bool = False,
        search: bool = False,
    ):

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": img_data_url}},
                    {"type": "text", "text": instruction},
                ],
            }
        ],
            stream=stream,
            extra_body={
                "enable_thinking": think,
                "enable_search": search,
            },
        )

        return completion.choices[0].message.content.strip()


class AsyncQwenClient(AsyncOpenAIClient):
    def __init__(self, url, key, model):
        super().__init__(
            url=url or settings.dashscope_llm_url, 
            key=key or settings.dashscope_llm_key, 
            model=model or settings.dashscope_llm_model
        )


if __name__ == "__main__":

    from infra import settings
    client = QwenClient(
        url=settings.dashscope_llm_url,
        key=settings.dashscope_llm_key,
        model="qwen3-rerank"
    )

    pass