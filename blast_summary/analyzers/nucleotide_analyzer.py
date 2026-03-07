"""
核苷酸分析器

分析blastn结果，包括变异分析、进化推断等。
"""

from typing import Dict, Any, List
from .base_analyzer import BaseAnalyzer
from ..models.blast_result import BlastResult, HSP
from ..utils.statistics import analyze_species_distribution, format_hits_table, format_blast_params


class NucleotideAnalyzer(BaseAnalyzer):
    """
    核苷酸BLAST分析器

    专门分析blastn结果，提供：
    - 变异位点分析
    - 进化关系推断
    - 物种鉴定
    """

    def __init__(self, result: BlastResult):
        super().__init__(result)
        self._mutations = None

    def analyze(self) -> Dict[str, Any]:
        """执行核苷酸BLAST分析"""
        return {
            "blast_type": "blastn",
            "query_info": {
                "id": self.result.query_id,
                "definition": self.result.query_def,
                "length": self.result.query_len
            },
            "statistics": self.statistics,
            "top_hits": self.get_top_hits(),
            "species_distribution": self._analyze_species(),
            "mutation_analysis": self._analyze_mutations(),
            "evolutionary_insights": self._analyze_evolution(),
            "quality_assessment": self._assess_quality()
        }

    def generate_summary_text(self) -> str:
        """生成核苷酸BLAST摘要文本"""
        lines = []
        lines.append(f"## blastn 分析报告")
        lines.append(f"")

        # BLAST 参数信息
        lines.append(format_blast_params(self.result))

        # 高得分比对表格
        lines.append(f"### 高得分比对")
        lines.append(f"")
        lines.append(format_hits_table(self.result, 5))
        lines.append(f"")

        # 物种分布
        species = self._analyze_species()
        if species:
            lines.append(f"### 物种分布")
            lines.append(f"")
            for sp, count in list(species.items())[:5]:
                lines.append(f"- {sp}: {count}次命中")
            if len(species) > 5:
                lines.append(f"- 其他: {len(species) - 5}个物种")
            lines.append(f"")

            # 进化推断
            evolution = self._analyze_evolution()
            if evolution.get("conservation_level"):
                lines.append(f"### 进化推断")
                lines.append(f"")
                lines.append(f"- 保守程度: {evolution['conservation_level']}")
                lines.append(f"")

        # 质量评估
        quality = self._assess_quality()
        lines.append(f"### 质量评估")
        lines.append(f"")
        lines.append(f"- 覆盖度质量: {quality['coverage_quality']}")
        lines.append(f"- 显著性: {quality['significance']}")
        lines.append(f"- 综合评价: {quality['overall_quality']}")

        return "\n".join(lines)

    def _analyze_species(self) -> Dict[str, int]:
        """分析物种分布"""
        return analyze_species_distribution(self.result)

    def _analyze_mutations(self) -> Dict[str, Any]:
        """分析变异位点"""
        if self._mutations is not None:
            return self._mutations

        mutations = {
            "total_mutations": 0,
            "transitions": 0,  # 转换 (A↔G, C↔T)
            "transversions": 0,  # 颠换 (A↔C, A↔T, G↔C, G↔T)
            "gap_events": 0
        }

        # 分析最佳HSP的变异
        if self.result.best_hit and self.result.best_hit.best_hsp:
            hsp = self.result.best_hit.best_hsp
            mutations["gap_events"] = hsp.gaps

            # 计算变异位点
            if hsp.identity < hsp.align_len:
                mutations["total_mutations"] = hsp.align_len - hsp.identity

        self._mutations = mutations
        return mutations

    def _analyze_evolution(self) -> Dict[str, Any]:
        """分析进化关系"""
        insights = {
            "conservation_level": "unknown",
            "related_species": [],
            "divergence_estimate": None
        }

        if not self.result.hits:
            return insights

        # 根据一致性判断保守程度
        best_identity = self.statistics.get("max_identity", 0)

        if best_identity >= 99:
            insights["conservation_level"] = "高度保守（可能是同一物种或非常近缘）"
        elif best_identity >= 95:
            insights["conservation_level"] = "较保守（近缘物种）"
        elif best_identity >= 80:
            insights["conservation_level"] = "中等保守（同属或同科物种）"
        elif best_identity >= 70:
            insights["conservation_level"] = "较低保守（远缘相关）"
        else:
            insights["conservation_level"] = "低保守（可能为同源基因）"

        # 提取相关物种
        species = self._analyze_species()
        insights["related_species"] = list(species.keys())[:5]

        return insights

    def _assess_quality(self) -> Dict[str, Any]:
        """评估比对质量"""
        quality = {
            "overall_quality": "unknown",
            "coverage_quality": "unknown",
            "significance": "unknown"
        }

        stats = self.statistics

        # 覆盖度评估
        coverage = stats.get("coverage_percent", 0)
        if coverage >= 90:
            quality["coverage_quality"] = "优秀（>=90%）"
        elif coverage >= 70:
            quality["coverage_quality"] = "良好（70-90%）"
        elif coverage >= 50:
            quality["coverage_quality"] = "一般（50-70%）"
        else:
            quality["coverage_quality"] = "较差（<50%）"

        # 显著性评估
        min_evalue = stats.get("min_evalue", 1)
        if min_evalue < 1e-50:
            quality["significance"] = "高度显著（E < 1e-50）"
        elif min_evalue < 1e-10:
            quality["significance"] = "显著（E < 1e-10）"
        elif min_evalue < 0.05:
            quality["significance"] = "边缘显著（E < 0.05）"
        else:
            quality["significance"] = "不显著（E >= 0.05）"

        # 综合评估
        if coverage >= 70 and min_evalue < 0.05:
            quality["overall_quality"] = "高质量比对"
        elif coverage >= 50 and min_evalue < 0.05:
            quality["overall_quality"] = "中等质量比对"
        else:
            quality["overall_quality"] = "低质量比对"

        return quality
