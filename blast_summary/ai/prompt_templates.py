"""
提示词模板

定义不同BLAST类型的AI提示词模板。
"""

from typing import Dict, Any


def get_system_prompt(blast_type: str) -> str:
    """
    获取系统提示词

    Args:
        blast_type: BLAST类型

    Returns:
        系统提示词
    """
    base_prompt = """你是一位专业的生物信息学专家，擅长分析BLAST比对结果并提供生物学意义的解释。

你的任务是：
1. 分析BLAST比对结果的统计数据
2. 解释命中序列的生物学意义
3. 推断查询序列的可能功能
4. 提供进化关系的见解
5. 评估比对结果的质量和可靠性

请使用专业但易于理解的语言进行解释，并提供具体的生物学背景知识。
回答需要用中文，但是专业术语可以保留英文。

格式要求：                                                                                                                                                             
- 使用列表时，每个要点单独一行，使用 - 或 * 开头                                                                                                                       
- 多个论点或证据请分行展示，不要堆砌在同一行                                                                                                                           
- 关键信息可以使用 **加粗** 强调  

注意：直接输出分析内容，不要有开场白、引言或客套话，直接开始分析报告。"""

    type_specific = {
        "blastn": """

对于blastn（核苷酸-核苷酸比对），请特别关注：
- 序列一致性和物种鉴定
- 变异位点分析
- 进化距离估计
- 可能的基因功能""",

        "blastp": """

对于blastp（蛋白质-蛋白质比对），请特别关注：
- 蛋白质保守结构域
- 功能位点和活性位点
- 蛋白质家族归属
- 三维结构预测的可能性""",

        "blastx": """

对于blastx（翻译核苷酸-蛋白质比对），请特别关注：
- 正确的阅读框预测
- 基因编码区识别
- 可能的基因功能
- 选择性剪接可能性""",

        "tblastn": """

对于tblastn（蛋白质-翻译核苷酸比对），请特别关注：
- 基因组定位
- 基因结构预测
- 外显子-内含子边界
- 同源基因分布"""
    }

    return base_prompt + type_specific.get(blast_type, "")


def get_user_prompt_template(blast_type: str) -> str:
    """
    获取用户提示词模板

    Args:
        blast_type: BLAST类型

    Returns:
        用户提示词模板
    """
    return """请分析以下{blast_type}比对结果并提供生物学意义的解释：

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

## 前{hits_count}个最佳命中
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


def format_context_for_prompt(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    格式化上下文信息用于提示词

    Args:
        context: 原始上下文

    Returns:
        格式化后的上下文
    """
    # 构建命中表格
    top_hits = context.get("top_hits", [])
    hits_table_lines = [f"| 排名 | 登录号 | 描述 | 得分 | E值 | 一致性 | (共{len(top_hits)}条)"]
    hits_table_lines.append("|------|--------|------|------|-----|--------|")

    for hit in top_hits:
        desc = hit.get("definition", "")[:40]
        hits_table_lines.append(
            f"| {hit.get('rank', 'N/A')} | {hit.get('accession', 'N/A')} | "
            f"{desc}... | {hit.get('bit_score', 'N/A'):.1f} | "
            f"{hit.get('evalue', 'N/A'):.2e} | {hit.get('identity_percent', 0):.1f}% |"
        )

    # 获取参数
    params = context.get("parameters", {})

    formatted = {
        "blast_type": context.get("blast_type", "blastn"),
        "query_id": context.get("query_id", "N/A"),
        "query_def": context.get("query_def", "N/A"),
        "query_len": context.get("query_len", "N/A"),
        "database": context.get("database", "N/A"),
        "matrix": params.get("matrix", "N/A"),
        "evalue_threshold": params.get("expect", "N/A"),
        "total_hits": context.get("total_hits", 0),
        "significant_hits": context.get("significant_hits", 0),
        "avg_identity": context.get("statistics", {}).get("avg_identity", 0),
        "max_identity": context.get("statistics", {}).get("max_identity", 0),
        "min_evalue": context.get("statistics", {}).get("min_evalue", 0),
        "coverage_percent": context.get("statistics", {}).get("coverage_percent", 0),
        "top_hits_table": "\n".join(hits_table_lines),
        "hits_count": len(top_hits)
    }

    return formatted


def get_blast_type_prompt(blast_type: str) -> str:
    """获取BLAST类型特定提示"""
    prompts = {
        "blastn": "这是一个核苷酸序列比对结果，查询序列和数据库序列都是核苷酸。",
        "blastp": "这是一个蛋白质序列比对结果，查询序列和数据库序列都是蛋白质。",
        "blastx": "这是一个翻译核苷酸比对结果，查询核苷酸序列被翻译成蛋白质后与蛋白质数据库比对。",
        "tblastn": "这是一个蛋白质-翻译核苷酸比对结果，查询蛋白质序列与核苷酸数据库（翻译成蛋白质）比对。",
        "tblastx": "这是一个翻译核苷酸比对结果，查询核苷酸序列被翻译成蛋白质后与翻译成蛋白质的核苷酸数据库比对。"
    }
    return prompts.get(blast_type, "")
