# BLAST Summary Tool

基于AI的BLAST结果分析与总结工具。自动解析BLAST XML结果文件，生成结构化的分析报告，并可使用AI生成生物学解释。

## 功能特点

- 支持4种BLAST类型：blastn、blastp、blastx、tblastn
- 自动解析BLAST XML格式结果
- 生成结构化的Markdown报告，包含CNCB-BLAST任务链接
- 支持OpenAI兼容API（包括百度千帆、DeepSeek、Azure OpenAI等）
- 支持多API端点故障转移，提高服务可用性
- 支持流式输出，便于前端实时展示
- 可自定义发送给AI的比对结果数量

## 安装

### 方式一：pip安装（推荐）

```bash
git cloen https://github.com/HangboZhu/blast-summary.git
pip install -e .

pip install -r requirements.txt
```

## 配置

### 创建 .env 文件

复制 `.env.example` 为 `.env` 并配置API参数：

```bash
cp .env.example .env
```

### 配置参数说明

| 参数 | 必填 | 说明 | 默认值 |
|------|------|------|--------|
| `OPENAI_API_KEY` | 是* | API密钥 | - |
| `OPENAI_BASE_URL` | 否 | API基础URL | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | 否 | 使用的模型 | `gpt-4` |
| `OPENAI_MAX_TOKENS` | 否 | 最大token数 | `4096` |
| `OPENAI_TEMPERATURE` | 否 | 温度参数 | `0.7` |

*注：如果使用 `--no-ai` 参数跳过AI分析，则API配置非必填。

### 多端点故障转移配置

支持配置多个API端点，当一个端点失败时自动切换到备用端点：

```env
# 端点0（主端点）
ENDPOINT_0_NAME=endpoint_0
ENDPOINT_0_API_KEY=your-api-key-0
ENDPOINT_0_BASE_URL=https://qianfan.baidubce.com/v2/coding/
ENDPOINT_0_MODEL=qianfan-code-latest

# 端点1（备用端点）
ENDPOINT_1_NAME=endpoint_1
ENDPOINT_1_API_KEY=your-api-key-1
ENDPOINT_1_BASE_URL=https://api.deepseek.com/v1
ENDPOINT_1_MODEL=deepseek-chat
```

配置多个端点后，系统会按顺序尝试，直到成功或全部失败。

### 配置示例

**OpenAI官方API：**
```env
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
```

**百度千帆API：**
```env
OPENAI_API_KEY=your-baidu-api-key
OPENAI_BASE_URL=https://qianfan.baidubce.com
OPENAI_MODEL=ERNIE-Bot-turbo-0922
```

## 使用方法

### 基本用法

```bash
# Analyze blastp result
blast-summary -i data/blastp/blastp_example.txt

# Analyze with species information file
blast-summary -i data/blastp/blastp_5.txt -s data/blastp/blastp_18.txt

# Specify output file
blast-summary -i data/blastn/blastn_example.txt -o output/report.md

# Output to stdout
blast-summary -i data/blastx/blastx_example.txt --stdout

# Skip AI analysis
blast-summary -i data/tblastn/tblastn_example.txt --no-ai
```

### 命令行参数

| 参数 | 简写 | 说明 |
|------|------|------|
| `--input` | `-i` | 输入BLAST XML文件路径（必填） |
| `--output` | `-o` | 输出文件路径（可选，默认自动生成） |
| `--species_file`| `-s`| 输入含有物种信息的文件，blast *_18模式生成|
| `--env-file` | - | 指定.env配置文件路径（可选） |
| `--no-ai` | - | 跳过AI分析，仅生成基础报告 |
| `--stdout` | - | 输出到标准输出而非文件 |
| `--stream`| - | 启用流式输出，实时生成报告 |
| `--top-hits`| - | 发送给AI分析的比对结果数量，默认10，可设为`all`使用全部结果|

### 批量处理

使用提供的脚本批量处理多个BLAST结果：

```bash
bash scripts/batch_process_ai.sh # with ai
bash scripts/batch_process.sh # no ai
```

## 输出报告

工具生成Markdown格式的报告，根据模式不同输出不同内容：

### AI分析模式（默认）
输出AI生成的生物学解释报告，包含：

1. **报告头部**：CNCB-BLAST任务ID和结果链接
2. **结论**：比对结果的核心结论
3. **比对质量评估**：统计显著性、覆盖度、一致性等
4. **物种分析**：命中序列的物种分布和进化关系
5. **功能预测**：基于同源比对的功能注释
6. **生物学意义**：结果的生物学解读
7. **后续建议**：进一步分析的建议

### 基础报告模式（--no-ai）
输出基础的统计报告，包含：

1. **BLAST参数信息**：程序类型、数据库、E值阈值等
2. **高得分比对表格**：排名、登录号、描述、物种、得分、E值等
3. **功能预测**：基于关键词的功能注释
4. **质量评估**：覆盖度、显著性、相似度评估

## 项目结构

```
blast-summary-tool/
├── blast_summary/          # 核心代码
│   ├── ai/                 # AI客户端模块
│   ├── analyzers/          # 分析器模块
│   ├── models/             # 数据模型
│   ├── parsers/            # BLAST结果解析器
│   ├── utils/              # 工具函数
│   ├── cli.py              # 命令行入口
│   └── config.py           # 配置管理
├── data/                   # 示例数据目录
├── output/                 # 输出目录
├── tests/                  # 测试文件
├── main.py                 # 入口脚本
├── pyproject.toml          # 项目配置
├── requirements.txt        # 依赖列表
└── .env.example            # 配置示例
```

## 开发

### 运行测试

```bash
pytest tests/
```

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

## 许可证

MIT License
