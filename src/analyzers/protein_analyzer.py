"""
蛋白质分析器

分析blastp、blastx、tblastn结果，包括保守区域、功能预测等。
"""

from typing import Dict, Any, List, Optional
from .base_analyzer import BaseAnalyzer
from ..models.blast_result import BlastResult, BlastProgram, HSP
from ..utils.statistics import analyze_species_distribution


class ProteinAnalyzer(BaseAnalyzer):
    """
    蛋白质BLAST分析器

    分析blastp、blastx、tblastn结果，提供：
    - 保守区域分析
    - 功能预测
    - 结构域推断
    """

    def __init__(self, result: BlastResult):
        super().__init__(result)
        self._conserved_regions = None

    def analyze(self) -> Dict[str, Any]:
        """执行蛋白质BLAST分析"""
        return {
            "blast_type": self.result.program.value,
            "query_info": {
                "id": self.result.query_id,
                "definition": self.result.query_def,
                "length": self.result.query_len
            },
            "statistics": self.statistics,
            "top_hits": self.get_top_hits(),
            "species_distribution": self._analyze_species(),
            "conserved_regions": self._analyze_conserved_regions(),
            "functional_prediction": self._predict_function(),
            "quality_assessment": self._assess_quality(),
            "frame_analysis": self._analyze_frames() if self._needs_frame_analysis() else None
        }

    def generate_summary_text(self) -> str:
        """生成蛋白质BLAST摘要文本"""
        blast_type = self.result.program.value.upper()
        lines = []
        lines.append(f"## {blast_type} 分析报告")
        lines.append(f"")
        lines.append(f"### 查询序列信息")
        lines.append(f"- 序列ID: {self.result.query_id}")
        lines.append(f"- 序列描述: {self.result.query_def}")
        lines.append(f"- 序列长度: {self.result.query_len} aa")
        lines.append(f"")
        lines.append(f"### 比对统计")
        stats = self.statistics
        lines.append(f"- 总命中数: {stats['total_hits']}")
        lines.append(f"- 总HSP数: {stats['total_hsps']}")
        lines.append(f"- 平均一致性: {stats['avg_identity']}%")
        lines.append(f"- 最高一致性: {stats['max_identity']}%")
        lines.append(f"- 最小E值: {stats['min_evalue']}")
        lines.append(f"- 覆盖度: {stats['coverage_percent']}%")

        if "avg_positive" in stats:
            lines.append(f"- 平均相似度: {stats['avg_positive']}%")

        lines.append(f"")

        # 最佳命中
        if self.result.best_hit and self.result.best_hit.best_hsp:
            best = self.result.best_hit
            hsp = best.best_hsp
            lines.append(f"### 最佳命中")
            lines.append(f"- 登录号: {best.accession}")
            lines.append(f"- 描述: {best.definition[:80]}...")
            lines.append(f"- 比对得分: {hsp.bit_score}")
            lines.append(f"- E值: {hsp.evalue}")
            lines.append(f"- 一致性: {hsp.identity_percent:.2f}%")
            if hsp.positive:
                lines.append(f"- 相似度: {hsp.positive_percent:.2f}%")
            lines.append(f"- 比对长度: {hsp.align_len} aa")
            lines.append(f"")

        # 阅读框分析（blastx/tblastn）
        if self._needs_frame_analysis():
            frame_info = self._analyze_frames()
            if frame_info:
                lines.append(f"### 阅读框分析")
                lines.append(f"- 主要阅读框: {frame_info.get('primary_frame', 'N/A')}")
                lines.append(f"- 阅读框分布: {frame_info.get('frame_distribution', {})}")
                lines.append(f"")

        # 功能预测
        func_pred = self._predict_function()
        if func_pred.get("predicted_function"):
            lines.append(f"### 功能预测")
            lines.append(f"- 预测功能: {func_pred.get('predicted_function', 'N/A')}")
            lines.append(f"- 置信度: {func_pred.get('confidence', 'N/A')}")
            lines.append(f"")

        return "\n".join(lines)

    def _analyze_species(self) -> Dict[str, int]:
        """分析物种分布"""
        return analyze_species_distribution(self.result)

    def _needs_frame_analysis(self) -> bool:
        """判断是否需要阅读框分析"""
        return self.result.program in [BlastProgram.BLASTX, BlastProgram.TBLASTN]

    def _analyze_frames(self) -> Optional[Dict[str, Any]]:
        """分析阅读框分布（blastx/tblastn特有）"""
        if not self._needs_frame_analysis():
            return None

        frame_key = "query_frame" if self.result.program == BlastProgram.BLASTX else "hit_frame"

        frame_distribution: Dict[int, int] = {}
        for hit in self.result.hits:
            for hsp in hit.hsps:
                frame = getattr(hsp, frame_key, 0)
                frame_distribution[frame] = frame_distribution.get(frame, 0) + 1

        # 找出主要阅读框
        primary_frame = max(frame_distribution.items(), key=lambda x: x[1])[0] if frame_distribution else 0

        return {
            "primary_frame": primary_frame,
            "frame_distribution": frame_distribution,
            "strand": "正向" if primary_frame > 0 else "反向"
        }

    def _analyze_conserved_regions(self) -> Dict[str, Any]:
        """分析保守区域"""
        if self._conserved_regions is not None:
            return self._conserved_regions

        regions = {
            "highly_conserved": [],  # 高度保守区域（>=95%一致性）
            "moderately_conserved": [],  # 中等保守区域（80-95%）
            "variable_regions": [],  # 可变区域（<80%）
            "consensus_motifs": []  # 共识基序
        }

        # 基于最佳命中的比对信息分析
        if self.result.best_hit and self.result.best_hit.best_hsp:
            hsp = self.result.best_hit.best_hsp

            # 简化的保守区域分析
            identity_pct = hsp.identity_percent

            if identity_pct >= 95:
                regions["highly_conserved"].append({
                    "start": hsp.query_from,
                    "end": hsp.query_to,
                    "identity": identity_pct
                })
            elif identity_pct >= 80:
                regions["moderately_conserved"].append({
                    "start": hsp.query_from,
                    "end": hsp.query_to,
                    "identity": identity_pct
                })
            else:
                regions["variable_regions"].append({
                    "start": hsp.query_from,
                    "end": hsp.query_to,
                    "identity": identity_pct
                })

        self._conserved_regions = regions
        return regions

    def _predict_function(self) -> Dict[str, Any]:
        """预测蛋白质功能"""
        prediction = {
            "predicted_function": None,
            "confidence": "low",
            "evidence": [],
            "go_terms": [],
            "protein_family": None
        }

        if not self.result.hits:
            return prediction

        # 从最佳命中的描述中提取功能信息
        best_hit = self.result.best_hit
        if best_hit:
            definition = best_hit.definition

            # 提取功能关键词
            keywords = self._extract_function_keywords(definition)
            prediction["evidence"] = keywords

            if keywords:
                prediction["predicted_function"] = keywords[0] if len(keywords) == 1 else "; ".join(keywords[:3])

            # 提取蛋白质家族
            family = self._extract_protein_family(definition)
            if family:
                prediction["protein_family"] = family

            # 根据比对质量评估置信度
            if best_hit.best_hsp:
                hsp = best_hit.best_hsp
                if hsp.identity_percent >= 90 and hsp.evalue < 1e-50:
                    prediction["confidence"] = "high"
                elif hsp.identity_percent >= 70 and hsp.evalue < 1e-10:
                    prediction["confidence"] = "medium"

        return prediction

    def _extract_function_keywords(self, definition: str) -> List[str]:
        """从描述中提取功能关键词"""
        keywords = []
        # 常见功能关键词
        function_patterns = [
            "kinase", "phosphatase", "transferase", "reductase",
            "oxidase", "synthase", "protease", "receptor",
            "channel", "transporter", "factor", "binding",
            "regulator", "enzyme", "subunit", "chain",
            "hemoglobin", "globin", "p53", "tumor suppressor",
            "antigen", "membrane", "nuclear"
        ]

        definition_lower = definition.lower()
        for pattern in function_patterns:
            if pattern in definition_lower:
                keywords.append(pattern)

        return keywords

    def _extract_protein_family(self, definition: str) -> Optional[str]:
        """提取蛋白质家族信息"""
        # 查找RecName或AltName中的Full=后内容
        import re

        match = re.search(r'Full=([^;\[\]]+)', definition)
        if match:
            return match.group(1).strip()

        return None

    def _assess_quality(self) -> Dict[str, Any]:
        """评估比对质量"""
        quality = {
            "overall_quality": "unknown",
            "coverage_quality": "unknown",
            "significance": "unknown",
            "similarity_quality": "unknown"
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

        # 相似度评估（蛋白质特有）
        avg_positive = stats.get("avg_positive", 0)
        if avg_positive >= 80:
            quality["similarity_quality"] = "高度相似（>=80%）"
        elif avg_positive >= 60:
            quality["similarity_quality"] = "中等相似（60-80%）"
        elif avg_positive >= 40:
            quality["similarity_quality"] = "低相似度（40-60%）"
        else:
            quality["similarity_quality"] = "相似度较低（<40%）"

        # 综合评估
        if coverage >= 70 and min_evalue < 0.05:
            quality["overall_quality"] = "高质量比对"
        elif coverage >= 50 and min_evalue < 0.05:
            quality["overall_quality"] = "中等质量比对"
        else:
            quality["overall_quality"] = "低质量比对"

        return quality
