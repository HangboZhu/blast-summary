"""测试 AI API 的 token 输出速度"""

import time
import requests
import os
import sys
from pathlib import Path

# 加载 .env 配置
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)

# API 配置
API_KEY = os.getenv("OPENAI_API_KEY", "")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

if not API_KEY:
    print("错误: 未配置 OPENAI_API_KEY")
    sys.exit(1)

# 确保 base_url 格式正确
if not BASE_URL.endswith("/"):
    BASE_URL += "/"

url = f"{BASE_URL}chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# 测试提示词 - 要求输出较长内容以便测试
test_prompt = """请写一篇关于 BLAST（Basic Local Alignment Search Tool）生物信息学工具的详细介绍，
包括以下几个方面：
1. BLAST 的基本原理
2. 主要的 BLAST 类型及其用途
3. E值的含义
4. BLAST 在生物研究中的应用

请详细回答，字数不少于 500 字。"""

payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": test_prompt}],
    "max_tokens": 2000,
    "temperature": 0.7,
    "stream": True  # 使用流式输出以便更精确计时
}

print(f"API: {BASE_URL}")
print(f"模型: {MODEL}")
print("-" * 50)
print("开始测试...\n")

start_time = time.time()
first_token_time = None
total_tokens = 0
response_text = ""

try:
    with requests.post(url, headers=headers, json=payload, stream=True, timeout=300) as resp:
        resp.raise_for_status()

        for line in resp.iter_lines():
            if not line:
                continue

            line = line.decode('utf-8')
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break

                try:
                    import json
                    chunk = json.loads(data)
                    if "choices" in chunk and len(chunk["choices"]) > 0:
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            if first_token_time is None:
                                first_token_time = time.time()
                                ttft = first_token_time - start_time
                                print(f"首 token 延迟 (TTFT): {ttft:.2f} 秒")
                                print("-" * 50)

                            response_text += content
                            total_tokens += 1  # 粗略估计
                            print(content, end="", flush=True)
                except json.JSONDecodeError:
                    pass

except requests.exceptions.Timeout:
    print("\n错误: 请求超时")
    sys.exit(1)
except Exception as e:
    print(f"\n错误: {e}")
    sys.exit(1)

end_time = time.time()
total_time = end_time - start_time
generation_time = end_time - first_token_time if first_token_time else total_time

print("\n")
print("=" * 50)
print("测试结果")
print("=" * 50)
print(f"总耗时: {total_time:.2f} 秒")
print(f"首 token 延迟: {ttft:.2f} 秒")
print(f"生成耗时: {generation_time:.2f} 秒")
print(f"输出字符数: {len(response_text)}")
print(f"估计 token 数: {len(response_text) // 2}")  # 中文约 2 字符/token
print(f"输出速度: {len(response_text) / generation_time:.1f} 字符/秒")
print(f"估计 token 速度: {len(response_text) // 2 / generation_time:.1f} tokens/秒")