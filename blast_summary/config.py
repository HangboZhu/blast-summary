"""
配置管理模块

加载和管理环境变量配置，包括API密钥、模型设置等。
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv


@dataclass
class AIConfig:
    """AI API配置"""
    api_key: str
    base_url: str
    model: str
    max_tokens: int = 4096
    temperature: float = 0.7


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

        # 读取AI配置
        api_key = os.getenv("OPENAI_API_KEY", "")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.getenv("OPENAI_MODEL", "gpt-4")

        ai_config = None
        if api_key:
            ai_config = AIConfig(
                api_key=api_key,
                base_url=base_url,
                model=model,
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4096")),
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
            )

        # 创建配置实例
        config = cls(ai=ai_config)

        # 设置路径
        project_root = Path(__file__).parent.parent
        config.data_dir = project_root / "data"
        config.output_dir = project_root / "output"

        return config

    def validate(self) -> bool:
        """验证配置是否有效"""
        if self.ai is None:
            return False
        if not self.ai.api_key:
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
