"""智谱API客户端"""
from dataclasses import dataclass
from typing import Optional
import requests
import json
import time
from src.config import ModelConfig


@dataclass
class ModelResponse:
    """模型响应"""
    content: str
    time_to_first_token: Optional[float]
    total_time: Optional[float]
    success: bool
    error: Optional[str] = None


class ZhipuClient:
    """智谱API客户端"""

    def __init__(self, config: ModelConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        })

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        stream: bool = False
    ) -> ModelResponse:
        """发送聊天请求

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            stream: 是否使用流式响应

        Returns:
            模型响应
        """
        url = f"{self.config.base_url}/chat/completions"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        payload = {
            "model": self.config.name,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "stream": stream
        }

        start_time = time.time()

        try:
            if stream:
                return self._stream_request(url, payload, start_time)
            else:
                return self._sync_request(url, payload, start_time)
        except Exception as e:
            return ModelResponse(
                content="",
                time_to_first_token=None,
                total_time=time.time() - start_time,
                success=False,
                error=str(e)
            )

    def _sync_request(
        self, url: str, payload: dict, start_time: float
    ) -> ModelResponse:
        """同步请求"""
        response = self.session.post(url, json=payload, timeout=120)
        total_time = time.time() - start_time

        if response.status_code != 200:
            error_body = response.text
            return ModelResponse(
                content="",
                time_to_first_token=None,
                total_time=total_time,
                success=False,
                error=f"API error {response.status_code}: {error_body}"
            )

        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        return ModelResponse(
            content=content,
            time_to_first_token=None,
            total_time=total_time,
            success=True
        )

    def _stream_request(
        self, url: str, payload: dict, start_time: float
    ) -> ModelResponse:
        """流式请求"""
        content_chunks = []
        time_to_first_token = None

        response = self.session.post(
            url,
            json=payload,
            stream=True,
            timeout=120
        )

        for line in response.iter_lines():
            if not line:
                continue
            line = line.decode('utf-8')
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    chunk = delta.get("content", "")
                    if chunk:
                        if time_to_first_token is None:
                            time_to_first_token = time.time() - start_time
                        content_chunks.append(chunk)
                except json.JSONDecodeError:
                    continue

        total_time = time.time() - start_time
        content = "".join(content_chunks)

        return ModelResponse(
            content=content,
            time_to_first_token=time_to_first_token,
            total_time=total_time,
            success=response.status_code == 200
        )

    def test_connection(self) -> tuple:
        """测试连接

        Returns:
            (success, message)
        """
        response = self.chat(
            system_prompt="你是一个助手。",
            user_prompt="你好",
            stream=False
        )
        return response.success, response.error or "连接成功"
