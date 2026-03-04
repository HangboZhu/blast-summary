"""
AI客户端基类

定义AI客户端的通用接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseAIClient(ABC):
    """
    AI客户端基类

    定义与AI模型交互的通用接口。
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    @abstractmethod
    def chat(self, messages: list, **kwargs) -> str:
        """
        发送聊天请求

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Returns:
            AI响应文本
        """
        pass

    @abstractmethod
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
        pass

    def _build_system_prompt(self, blast_type: str) -> str:
        """构建系统提示词"""
        from .prompt_templates import get_system_prompt
        return get_system_prompt(blast_type)

    def _build_user_prompt(self, context: Dict[str, Any]) -> str:
        """构建用户提示词"""
        from .prompt_templates import get_user_prompt_template
        template = get_user_prompt_template(context.get("blast_type", "blastn"))
        return template.format(**context)
