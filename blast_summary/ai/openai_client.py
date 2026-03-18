"""
OpenAI兼容客户端

支持OpenAI API及兼容接口（如百度千帆），并支持多端点故障转移。
"""

import json
from typing import Dict, Any, Optional, List, Generator
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

    def chat_stream(self, messages: list, **kwargs) -> Generator[str, None, None]:
        """
        流式发送聊天请求

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Yields:
            AI响应文本片段
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
            "temperature": kwargs.get("temperature", self.temperature),
            "stream": True  # 开启流式传输
        }

        try:
            response = requests.post(
                url, headers=headers, json=payload,
                timeout=120, stream=True
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue

                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]  # 去掉 'data: ' 前缀

                    if data == '[DONE]':
                        break

                    try:
                        chunk = json.loads(data)
                        if 'choices' in chunk and len(chunk['choices']) > 0:
                            delta = chunk['choices'][0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue

        except requests.exceptions.Timeout:
            raise TimeoutError("AI API request timed out")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"AI API request failed: {str(e)}")

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

    def generate_summary_stream(
        self,
        blast_type: str,
        context: Dict[str, Any]
    ) -> Generator[str, None, None]:
        """
        流式生成BLAST结果摘要

        Args:
            blast_type: BLAST类型
            context: BLAST结果上下文

        Yields:
            摘要文本片段
        """
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

        yield from self.chat_stream(messages)

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

请按以下格式输出分析报告（直接输出，不要开场白）：

然后提供以下6个部分的详细分析，每个部分使用###三级标题：

### 1. 结论
用一句话概括本次BLAST比对的核心发现和生物学意义。

### 2. 比对质量评估
评估本次比对的整体质量。

### 3. 物种分析
分析命中序列的物种分布和进化意义。

### 4. 功能预测
根据命中结果预测查询序列的可能功能。

### 5. 生物学意义
解释这些比对结果的生物学含义。

### 6. 后续建议
建议下一步的分析方向。

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


class FailoverAIClient:
    """
    支持故障转移的AI客户端

    当主端点失败时（超时、连接错误等），自动切换到备用端点重试。
    """

    def __init__(self, ai_config):
        """
        初始化故障转移客户端

        Args:
            ai_config: AIConfig实例，包含多个端点配置
        """
        self.config = ai_config
        self._clients: List[OpenAIClient] = []

        # 预创建所有端点的客户端实例
        for endpoint in ai_config.endpoints:
            client = OpenAIClient(
                api_key=endpoint.api_key,
                base_url=endpoint.base_url,
                model=endpoint.model,
                max_tokens=ai_config.max_tokens,
                temperature=ai_config.temperature
            )
            self._clients.append(client)

        print(f"[API] {len(self._clients)} endpoints configured "
              f"(failover {'enabled' if ai_config.failover_enabled else 'disabled'})")

    def generate_summary_with_failover(
        self,
        blast_type: str,
        context: Dict[str, Any]
    ) -> str:
        """
        依次尝试所有API端点，直到成功或全部失败

        Args:
            blast_type: BLAST类型
            context: BLAST结果上下文

        Returns:
            AI生成的摘要文本

        Raises:
            Exception: 所有端点都失败时抛出最后一个错误
        """
        last_error = None
        messages = self._build_messages(blast_type, context)

        for endpoint_idx, client in enumerate(self._clients):
            endpoint = self.config.endpoints[endpoint_idx]
            endpoint_name = endpoint.name

            print(f"[API] Trying endpoint '{endpoint_name}' "
                  f"({endpoint.base_url})...")

            # 在每个端点内部重试
            for attempt in range(1, self.config.retry_count + 1):
                try:
                    result = client.chat(messages)
                    print(f"[API] Success with endpoint '{endpoint_name}'")
                    return result
                except TimeoutError as e:
                    print(f"[API] Timeout on endpoint '{endpoint_name}' "
                          f"(attempt {attempt}/{self.config.retry_count})")
                    last_error = e
                except ConnectionError as e:
                    print(f"[API] Connection error on endpoint '{endpoint_name}': {e}")
                    last_error = e
                    break  # 连接错误直接切换端点
                except Exception as e:
                    print(f"[API] Error on endpoint '{endpoint_name}': {e}")
                    last_error = e
                    break  # 其他错误直接切换端点

            # 检查是否启用故障转移，或者已经是最后一个端点
            if self.config.failover_enabled and endpoint_idx < len(self._clients) - 1:
                print("[API] Switching to fallback endpoint...")

        # 所有端点都失败
        raise last_error or Exception("All API endpoints failed")

    def generate_summary_stream_with_failover(
        self,
        blast_type: str,
        context: Dict[str, Any]
    ) -> Generator[str, None, None]:
        """
        流式生成的故障转移版本

        依次尝试所有API端点进行流式生成。

        Args:
            blast_type: BLAST类型
            context: BLAST结果上下文

        Yields:
            AI生成的摘要文本片段
        """
        last_error = None
        messages = self._build_messages(blast_type, context)

        for endpoint_idx, client in enumerate(self._clients):
            endpoint = self.config.endpoints[endpoint_idx]
            endpoint_name = endpoint.name

            print(f"[API] Trying endpoint '{endpoint_name}' "
                  f"({endpoint.base_url})...")

            # 流式模式：每个端点只尝试一次（流式难以中途切换）
            try:
                success = False
                for chunk in client.chat_stream(messages):
                    success = True
                    yield chunk

                if success:
                    print(f"[API] Success with endpoint '{endpoint_name}'")
                    return  # 成功完成，结束生成

            except TimeoutError as e:
                print(f"[API] Timeout on endpoint '{endpoint_name}'")
                last_error = e
            except ConnectionError as e:
                print(f"[API] Connection error on endpoint '{endpoint_name}': {e}")
                last_error = e
            except Exception as e:
                print(f"[API] Error on endpoint '{endpoint_name}': {e}")
                last_error = e

            # 检查是否启用故障转移
            if self.config.failover_enabled and endpoint_idx < len(self._clients) - 1:
                print("[API] Switching to fallback endpoint...")

        # 所有端点都失败
        raise last_error or Exception("All API endpoints failed")

    def _build_messages(self, blast_type: str, context: Dict[str, Any]) -> list:
        """构建消息列表"""
        # 使用第一个客户端的方法构建消息
        if self._clients:
            return [
                {
                    "role": "system",
                    "content": self._clients[0]._build_system_prompt(blast_type)
                },
                {
                    "role": "user",
                    "content": self._clients[0]._build_user_content(blast_type, context)
                }
            ]
        return []


def create_ai_client(config) -> Optional[FailoverAIClient]:
    """
    根据配置创建AI客户端

    Args:
        config: 配置对象

    Returns:
        FailoverAIClient实例，如果配置无效则返回None
    """
    if not config.ai:
        return None

    return FailoverAIClient(config.ai)
