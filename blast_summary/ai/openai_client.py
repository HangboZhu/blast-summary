"""
OpenAI兼容客户端

支持OpenAI API及兼容接口（如百度千帆）。
"""

import json
from typing import Dict, Any, Optional, List
import requests

from .base_client import BaseAIClient
from .prompt_templates import format_context_for_prompt


class OpenAIClient(BaseAIClient):
    """
    OpenAI兼容客户端

    支持OpenAI API和兼容接口，如百度千帆、Azure OpenAI等。
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ):
        super().__init__(api_key, base_url, model, max_tokens, temperature)

        # 确保base_url格式正确
        if not self.base_url.endswith("/"):
            self.base_url += "/"

    def chat(self, messages: list, **kwargs) -> str:
        """
        发送聊天请求

        Args:
            messages: 消息列表，格式为[{"role": "user/assistant/system", "content": "..."}]
            **kwargs: 额外参数

        Returns:
            AI响应文本
        """
        url = f"{self.base_url}chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature)
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except requests.exceptions.Timeout:
            raise TimeoutError("AI API request timed out")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"AI API request failed: {str(e)}")
        except (KeyError, IndexError) as e:
            raise ValueError(f"Invalid AI API response: {str(e)}")

    def generate_summary(
        self,
        blast_type: str,
        context: Dict[str, Any]
    ) -> str:
        """
        生成BLAST结果摘要

        Args:
            blast_type: BLAST类型
            context: BLAST结果上下文

        Returns:
            摘要文本
        """
        # 构建消息
        messages = [
            {
                "role": "system",
                "content": self._build_system_prompt(blast_type)
            },
            {
                "role": "user",
                "content": self._build_user_content(blast_type, context)
            }
        ]

        return self.chat(messages)

    def _build_user_content(self, blast_type: str, context: Dict[str, Any]) -> str:
        """构建用户消息内容"""
        formatted = format_context_for_prompt(context)

        # 构建用户提示词
        template = """请分析以下{blast_type}比对结果并提供生物学意义的解释：

## 查询序列信息
- 序列ID: {query_id}
- 序列描述: {query_def}
- 序列长度: {query_len}

## 比对参数
- 数据库: {database}
- 替换矩阵: {matrix}
- E值阈值: {evalue_threshold}

## 统计数据
- 总命中数: {total_hits}
- 显著命中数: {significant_hits}
- 平均一致性: {avg_identity}%
- 最高一致性: {max_identity}%
- 最小E值: {min_evalue}
- 覆盖度: {coverage_percent}%

## 前10个最佳命中
{top_hits_table}

请提供以下内容的分析：
1. **比对质量评估**：评估本次比对的整体质量
2. **物种分析**：分析命中序列的物种分布和进化意义
3. **功能预测**：根据命中结果预测查询序列的可能功能
4. **生物学意义**：解释这些比对结果的生物学含义
5. **后续建议**：建议下一步的分析方向

请用中文回答，专业术语可保留英文。"""

        return template.format(**formatted)

    def generate_with_retry(
        self,
        messages: list,
        max_retries: int = 3,
        **kwargs
    ) -> str:
        """
        带重试的生成方法

        Args:
            messages: 消息列表
            max_retries: 最大重试次数
            **kwargs: 额外参数

        Returns:
            AI响应文本
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                return self.chat(messages, **kwargs)
            except (TimeoutError, ConnectionError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # 指数退避

        raise last_error or Exception("Failed to generate summary")


def create_ai_client(config) -> Optional[OpenAIClient]:
    """
    根据配置创建AI客户端

    Args:
        config: 配置对象

    Returns:
        AI客户端实例，如果配置无效则返回None
    """
    if not config.ai:
        return None

    return OpenAIClient(
        api_key=config.ai.api_key,
        base_url=config.ai.base_url,
        model=config.ai.model,
        max_tokens=config.ai.max_tokens,
        temperature=config.ai.temperature
    )
