

from __future__ import annotations

import json
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion


from app.infra.typing_common import *

ToolSchema = Dict[str, Any]
ToolMap = Dict[str, Callable[..., Any]]

class OpenAIClient:
    def __init__(self, url, key, model):
        self.client = OpenAI(api_key=key, base_url=url)
        self.model = model

    async def chat_completions(
        self,
        *,
        model=None,
        messages: Optional[List[Dict[str, str]]] = None,
        stream: bool = False,
        think: bool = False,
        search: bool = False,
        text_format: Optional[Any] = None
    ):

        response = self.client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            stream=stream,
            extra_body={
                "enable_thinking": think,
                "enable_search": search,
                "text_format": text_format,
            },
        )

        if stream:
            return response
        return response
    
    async def chat_react_once(
        self,
        *,
        model=None,
        messages: Optional[List[Dict[str, str]]] = None,
        stream: bool = False,
        think: bool = False,
        search: bool = False,
        text_format: Optional[Any] = None
    ):
        """
        messages: 由调用方维护的历史消息（每个会话一份）
        """

        resp = self.client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            stream=stream,
            extra_body={
                "enable_thinking": think,
                "enable_search": search,
                "text_format": text_format,
            },
        )

        if stream:
            return resp

        return resp
    
    async def chat_mcp_tool_once(
            self,
            *,
            model: Optional[str] = None,
            messages: Optional[List[Dict[str, Any]]] = None,
            tools: Optional[List[ToolSchema]] = None,
            tool_choice: Union[str, Dict[str, Any], None] = "auto",
            think: bool = False,
            search: bool = False,
            text_format: Optional[Any] = None,
        ) -> ChatCompletion:
            resp = self.client.chat.completions.create(
                model=model or self.model,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tool_choice else None,
                extra_body={
                    "enable_thinking": think,
                    "enable_search": search,
                    "text_format": {
                        "type": "json_schema",
                        "json_schema": text_format
                    }
                }
            )
            return resp
    
    

    def chat_response(self, prompt: str):
        response = self.client.responses.create(
            model=self.model,   # 修复拼写错误 mdoel → model
            input=prompt,
        )
        return response

    def _build_messages(
        self,
        system_prompt: str,
        user_prompt: str,
        messages: Optional[List[Dict[str, str]]],
    ) -> List[Dict[str, str]]:
        # 复制一份，避免原地修改外部 list
        msgs = list(messages) if messages else []

        if not msgs or msgs[0].get("role") != "system":
            msgs.insert(0, {"role": "system", "content": system_prompt})

        msgs.append({"role": "user", "content": user_prompt})
        return msgs


class AsyncOpenAIClient:
    def __init__(self, url: str, key: str, model: str):
        self.client = AsyncOpenAI(api_key=key, base_url=url)
        self.model = model

    async def chat_completions(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        stream: bool = False,
        think: bool = False,
        search: bool = False,
        history: Optional[List[Dict[str, str]]] = None,
    ):
        """
        - stream=False：返回字符串
        - stream=True ：返回异步生成器（你可以 async for 迭代获取增量token）
        - history：外部传入历史消息，避免并发时共享 self.messages 导致串话
        """
        messages = self._build_messages(system_prompt, user_prompt, history=history)

        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=stream,
            extra_body={
                "enable_thinking": think,
                "enable_search": search,
            },
        )

        if not stream:
            messages.append({"role": "user", "content": user_prompt})
            return resp.choices[0].message.content

        # stream=True：给调用方一个 async generator
        async def gen():
            async for event in resp:
                # OpenAI ChatCompletions stream: delta 在 choices[0].delta.content
                delta = event.choices[0].delta
                if delta and getattr(delta, "content", None):
                    yield delta.content

        return gen()

    async def chat_response(self, prompt: str):
        """
        Responses API 的异步调用（如果你在用 responses.create）
        """
        resp = await self.client.responses.create(
            model=self.model,
            input=prompt,
        )
        return resp

    async def chat_tools_call(
        self,
        system_prompt: str = "",
        user_prompt: str = "",
        *,
        model: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        tools: Optional[List[ToolSchema]] = None,
        tool_map: Optional[ToolMap] = None,
        tool_choice: Union[str, Dict[str, Any], None] = "auto",
        max_tool_rounds: int = 5,
        think: bool = False,
        search: bool = False,
        text_format: Optional[Any] = None,
        auto_execute_tools: bool = True,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        异步版 tool calling。
        返回：(final_text, msgs)
        """
        msgs = self._build_messages(system_prompt, user_prompt, history=messages)

        if tools is None:
            tools = []

        if auto_execute_tools and not tool_map:
            raise ValueError("auto_execute_tools=True 时必须提供 tool_map")

        rounds = 0
        final_text = ""

        while True:
            rounds += 1
            if rounds > max_tool_rounds:
                return final_text or "", msgs

            resp = await self.client.chat.completions.create(
                model=model or self.model,
                messages=msgs,
                tools=tools if tools else None,
                tool_choice=tool_choice if tools else None,
                extra_body={
                    "enable_thinking": think,
                    "enable_search": search,
                    "text_format": text_format,
                },
            )

            msg = resp.choices[0].message
            tool_calls = getattr(msg, "tool_calls", None)
            content = getattr(msg, "content", None)

            assistant_dict: Dict[str, Any] = {"role": "assistant", "content": content}
            if tool_calls:
                assistant_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ]
            msgs.append(assistant_dict)

            if not tool_calls:
                final_text = content or ""
                return final_text, msgs

            if not auto_execute_tools:
                return content or "", msgs

            for tc in tool_calls:
                fn_name = tc.function.name
                fn_args_str = tc.function.arguments or "{}"

                try:
                    fn_args = json.loads(fn_args_str)
                except json.JSONDecodeError:
                    fn_args = {}

                if fn_name not in tool_map:
                    tool_result = {"error": f"Tool '{fn_name}' not found in tool_map"}
                else:
                    try:
                        res = tool_map[fn_name](**fn_args)
                        # 兼容 async tool（可选）
                        tool_result = await res if hasattr(res, "__await__") else res
                    except Exception as e:
                        tool_result = {"error": f"Tool '{fn_name}' execution failed: {type(e).__name__}: {str(e)}"}

                msgs.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(tool_result, ensure_ascii=False),
                    }
                )

    def _build_messages(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        msgs: List[Dict[str, Any]] = list(history) if history else []
        if not msgs or msgs[0].get("role") != "system":
            msgs.insert(0, {"role": "system", "content": system_prompt})
        msgs.append({"role": "user", "content": user_prompt})
        return msgs


if __name__ == "__main__":
    import asyncio
    from app.infra import settings

    client = OpenAIClient(
        url=settings.dashscope_llm_url,
        key=settings.dashscope_llm_key,
        model=settings.dashscope_llm_model
    )

    client.chat_completions(user_prompt="你好")

    pass



    # 普通 await（非流式）
    async def main():
        cli = AsyncOpenAIClient(url="https://xxx", key="sk-xxx", model="gpt-4.1-mini")
        text = await cli.chat_completions("你是助手", "你好！")
        print(text)

    asyncio.run(main())

    # 流式输出（async for）
    async def main():
        cli = AsyncOpenAIClient(url="https://xxx", key="sk-xxx", model="gpt-4.1-mini")
        stream_gen = await cli.chat_completions("你是助手", "给我讲个笑话", stream=True)

        async for chunk in stream_gen:
            print(chunk, end="", flush=True)

    asyncio.run(main())