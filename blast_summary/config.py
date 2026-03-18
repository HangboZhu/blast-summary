"""
配置管理模块

加载和管理环境变量配置，包括API密钥、模型设置等。
支持多端点配置和故障转移。
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List
from dotenv import load_dotenv


@dataclass
class AIEndpointConfig:
    """
    单个API端点配置

    每个端点包含独立的API密钥、URL和模型配置。
    """
    api_key: str
    base_url: str
    model: str
    name: str = ""  # 端点名称，用于日志输出


@dataclass
class AIConfig:
    """
    AI API配置 - 支持多端点故障转移

    管理多个API端点，当主端点失败时可自动切换到备用端点。
    """
    endpoints: List[AIEndpointConfig] = field(default_factory=list)
    max_tokens: int = 4096
    temperature: float = 0.7
    retry_count: int = 1  # 每个端点的重试次数
    failover_enabled: bool = True  # 是否启用故障转移

    @property
    def primary_endpoint(self) -> Optional[AIEndpointConfig]:
        """获取主端点配置"""
        return self.endpoints[0] if self.endpoints else None

    def get_endpoint(self, index: int) -> Optional[AIEndpointConfig]:
        """获取指定索引的端点配置"""
        if 0 <= index < len(self.endpoints):
            return self.endpoints[index]
        return None


@dataclass
class Config:
    """
    应用配置

    管理所有配置项，包括AI API配置、路径配置等。
    """
    ai: Optional[AIConfig] = None
    data_dir: Path = field(default_factory=lambda: Path("data"))
    output_dir: Path = field(default_factory=lambda: Path("output"))

    @classmethod
    def from_env(cls, env_path: Optional[str] = None) -> "Config":
        """
        从环境变量加载配置

        Args:
            env_path: .env文件路径，默认为.env

        Returns:
            Config实例
        """
        # 确定env文件路径
        if env_path is None:
            project_root = Path(__file__).parent.parent
            env_path = project_root / ".env"
        else:
            env_path = Path(env_path)

        # 加载env文件
        if env_path.exists():
            load_dotenv(env_path)

        # 解析AI配置
        ai_config = cls._parse_ai_config()

        # 创建配置实例
        config = cls(ai=ai_config)

        # 设置路径
        project_root = Path(__file__).parent.parent
        config.data_dir = project_root / "data"
        config.output_dir = project_root / "output"

        return config

    @classmethod
    def _parse_ai_config(cls) -> Optional[AIConfig]:
        """
        解析AI配置

        支持两种配置格式：
        1. 索引式配置（推荐）：OPENAI_API_KEY_0, OPENAI_API_KEY_1, ...
        2. 旧格式：OPENAI_API_KEY（无后缀，向后兼容）

        Returns:
            AIConfig实例，如果未配置则返回None
        """
        endpoints = []
        index = 0

        # 尝试解析索引式配置
        while True:
            api_key = os.getenv(f"OPENAI_API_KEY_{index}", "")
            if not api_key:
                break

            base_url = os.getenv(
                f"OPENAI_BASE_URL_{index}",
                "https://api.openai.com/v1"
            )
            model = os.getenv(f"OPENAI_MODEL_{index}", "gpt-4")

            endpoints.append(AIEndpointConfig(
                api_key=api_key,
                base_url=base_url,
                model=model,
                name=f"endpoint_{index}"
            ))
            index += 1

        # 如果没有索引式配置，尝试旧格式（向后兼容）
        if not endpoints:
            legacy_api_key = os.getenv("OPENAI_API_KEY", "")
            if legacy_api_key:
                legacy_base_url = os.getenv(
                    "OPENAI_BASE_URL",
                    "https://api.openai.com/v1"
                )
                legacy_model = os.getenv("OPENAI_MODEL", "gpt-4")

                endpoints.append(AIEndpointConfig(
                    api_key=legacy_api_key,
                    base_url=legacy_base_url,
                    model=legacy_model,
                    name="endpoint_0"
                ))

        # 如果没有配置任何端点，返回None
        if not endpoints:
            return None

        # 读取通用参数
        max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "4096"))
        temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        retry_count = int(os.getenv("OPENAI_RETRY_COUNT", "1"))
        failover_enabled = os.getenv("OPENAI_FAILOVER_ENABLED", "true").lower() == "true"

        return AIConfig(
            endpoints=endpoints,
            max_tokens=max_tokens,
            temperature=temperature,
            retry_count=retry_count,
            failover_enabled=failover_enabled
        )

    def validate(self) -> bool:
        """验证配置是否有效"""
        if self.ai is None:
            return False
        if not self.ai.endpoints:
            return False
        if not self.ai.primary_endpoint:
            return False
        if not self.ai.primary_endpoint.api_key:
            return False
        return True

    def ensure_output_dir(self) -> None:
        """确保输出目录存在"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "summaries").mkdir(parents=True, exist_ok=True)


# 全局配置实例
_config: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def reload_config(env_path: Optional[str] = None) -> Config:
    """重新加载配置"""
    global _config
    _config = Config.from_env(env_path)
    return _config
