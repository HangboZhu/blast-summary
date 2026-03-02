"""
统计计算工具函数
"""

from typing import List, Dict, Any, Optional
from ..models.blast_result import BlastResult, Hit, HSP


def calculate_statistics(result: BlastResult) -> Dict[str, Any]:
    """
    计算BLAST结果的统计信息

    Args:
        result: BLAST结果对象

    Returns:
        统计信息字典
    """
    if not result.hits:
        return {
            "total_hits": 0,
            "total_hsps": 0,
            "avg_identity": 0,
            "avg_evalue": 0,
            "avg_bit_score": 0,
            "max_identity": 0,
            "min_evalue": 0
        }

    # 收集所有HSP
    all_hsps: List[HSP] = []
    for hit in result.hits:
        all_hsps.extend(hit.hsps)

    if not all_hsps:
        return {
            "total_hits": result.total_hits,
            "total_hsps": 0,
            "avg_identity": 0,
            "avg_evalue": 0,
            "avg_bit_score": 0,
            "max_identity": 0,
            "min_evalue": 0
        }

    # 计算统计数据
    identities = [hsp.identity_percent for hsp in all_hsps]
    evalues = [hsp.evalue for hsp in all_hsps]
    bit_scores = [hsp.bit_score for hsp in all_hsps]

    # 过滤无限大的evalue
    valid_evalues = [e for e in evalues if e > 0]
    min_evalue = min(valid_evalues) if valid_evalues else 0

    stats = {
        "total_hits": result.total_hits,
        "total_hsps": len(all_hsps),
        "avg_identity": round(sum(identities) / len(identities), 2) if identities else 0,
        "avg_evalue": round(sum(evalues) / len(evalues), 2) if evalues else 0,
        "avg_bit_score": round(sum(bit_scores) / len(bit_scores), 2) if bit_scores else 0,
        "max_identity": round(max(identities), 2) if identities else 0,
        "min_evalue": min_evalue,
        "coverage_percent": _calculate_coverage(result, all_hsps)
    }

    # 如果是蛋白质BLAST，添加positive统计
    positives = [hsp.positive_percent for hsp in all_hsps if hsp.positive_percent is not None]
    if positives:
        stats["avg_positive"] = round(sum(positives) / len(positives), 2)

    return stats


def _calculate_coverage(result: BlastResult, all_hsps: List[HSP]) -> float:
    """计算查询序列覆盖度"""
    if not all_hsps or result.query_len == 0:
        return 0.0

    # 使用位图标记覆盖位置
    covered = [False] * (result.query_len + 1)

    for hsp in all_hsps:
        start = min(hsp.query_from, hsp.query_to)
        end = max(hsp.query_from, hsp.query_to)
        for i in range(start, min(end + 1, len(covered))):
            covered[i] = True

    covered_count = sum(covered)
    return round((covered_count / result.query_len) * 100, 2)


def get_top_hits_summary(result: BlastResult, n: int = 10) -> List[Dict[str, Any]]:
    """
    获取前N个最佳命中的摘要信息

    Args:
        result: BLAST结果
        n: 命中数量

    Returns:
        命中摘要列表
    """
    top_hits = result.get_top_hits(n)
    summary = []

    for hit in top_hits:
        best_hsp = hit.best_hsp
        if best_hsp is None:
            continue

        hit_info = {
            "rank": hit.num,
            "accession": hit.accession,
            "definition": _truncate_definition(hit.definition, 100),
            "length": hit.length,
            "bit_score": best_hsp.bit_score,
            "evalue": best_hsp.evalue,
            "identity_percent": round(best_hsp.identity_percent, 2),
            "alignment_length": best_hsp.align_len,
            "total_hsps": hit.total_hsps
        }

        # 蛋白质BLAST添加positive信息
        if best_hsp.positive is not None:
            hit_info["positive_percent"] = round(best_hsp.positive_percent, 2)

        summary.append(hit_info)

    return summary


def _truncate_definition(definition: str, max_len: int = 100) -> str:
    """截断定义字符串"""
    if len(definition) <= max_len:
        return definition
    return definition[:max_len] + "..."


def analyze_species_distribution(result: BlastResult) -> Dict[str, int]:
    """
    分析命中物种分布

    Args:
        result: BLAST结果

    Returns:
        物种名称到命中数量的映射
    """
    species_count: Dict[str, int] = {}

    for hit in result.hits:
        # 从定义中提取物种名（通常在方括号中）
        species = _extract_species(hit.definition)
        if species:
            species_count[species] = species_count.get(species, 0) + 1

    # 按数量排序
    return dict(sorted(species_count.items(), key=lambda x: x[1], reverse=True))


def _extract_species(definition: str) -> Optional[str]:
    """从序列定义中提取物种名"""
    import re
    # 匹配方括号中的物种名
    match = re.search(r'\[([^\]]+)\]', definition)
    if match:
        return match.group(1)
    return None
