"""
分析器基类

提供BLAST结果分析的通用功能。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List

from ..models.blast_result import BlastResult, Hit, HSP
from ..utils.statistics import calculate_statistics, get_top_hits_summary


class BaseAnalyzer(ABC):
    """
    BLAST结果分析器基类

    提供统计分析、报告生成等通用功能。
    """

    def __init__(self, result: BlastResult):
        self.result = result
        self._statistics = None

    @property
    def statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if self._statistics is None:
            self._statistics = calculate_statistics(self.result)
        return self._statistics

    def get_top_hits(self, n: int = 10) -> List[Dict[str, Any]]:
        """获取前N个最佳命中"""
        return get_top_hits_summary(self.result, n)

    @abstractmethod
    def analyze(self) -> Dict[str, Any]:
        """
        执行分析，子类需要实现

        Returns:
            分析结果字典
        """
        pass

    @abstractmethod
    def generate_summary_text(self) -> str:
        """
        生成摘要文本，子类需要实现

        Returns:
            摘要文本
        """
        pass

    def get_blast_type_description(self) -> str:
        """获取BLAST类型描述"""
        descriptions = {
            "blastn": "核苷酸-核苷酸BLAST (blastn)",
            "blastp": "蛋白质-蛋白质BLAST (blastp)",
            "blastx": "翻译核苷酸-蛋白质BLAST (blastx)",
            "tblastn": "蛋白质-翻译核苷酸BLAST (tblastn)",
        }
        return descriptions.get(self.result.program.value, self.result.program.value)

    def prepare_ai_context(self) -> Dict[str, Any]:
        """
        准备发送给AI的上下文信息

        Returns:
            包含BLAST结果摘要的字典
        """
        return {
            "blast_type": self.result.program.value,
            "query_def": self.result.query_def,
            "query_len": self.result.query_len,
            "database": self.result.database,
            "parameters": self.result.parameters,
            "statistics": self.statistics,
            "top_hits": self.get_top_hits(10),
            "total_hits": self.result.total_hits,
            "significant_hits": len(self.result.significant_hits)
        }
