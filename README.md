# BLAST Summary Tool

基于AI的BLAST结果分析与总结工具。自动解析BLAST XML结果文件，生成结构化的分析报告，并可使用AI生成生物学解释。

## 功能特点

- 支持4种BLAST类型：blastn、blastp、blastx、tblastn
- 自动解析BLAST XML格式结果
- 生成包含统计信息和最佳比对的结构化Markdown报告
- 支持OpenAI兼容API（包括百度千帆、Azure OpenAI等）
- 可选择仅生成基础报告或跳过AI分析

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
| `--stream`| - | 是否采用流式输出，便于前端调用(如果指定了的话)|
| `--top-hits`| - | 发送给ai的前top个比对结果|

### 批量处理

使用提供的脚本批量处理多个BLAST结果：

```bash
bash scripts/batch_process_ai.sh # with ai
bash scripts/batch_process.sh # no ai
```

## 输出报告

工具生成Markdown格式的报告，包含以下内容：

1. **基本信息**：查询序列信息、BLAST程序类型、比对数量统计
2. **统计摘要**：E-value分布、一致性分布、比对长度分布等
3. **最佳比对**：展示最显著的比对结果
4. **生物学解释**（可选）：AI生成的生物学意义解读

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
