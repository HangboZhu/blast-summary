"""
BLAST结果数据模型

定义了HSP、Hit和BlastResult数据类，用于存储BLAST比对结果。
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class BlastProgram(Enum):
    """BLAST程序类型枚举"""
    BLASTN = "blastn"
    BLASTP = "blastp"
    BLASTX = "blastx"
    TBLASTN = "tblastn"
    TBLASTX = "tblastx"


@dataclass
class HSP:
    """
    High-scoring Segment Pair - 高得分片段对

    HSP是BLAST比对的基本单位，表示查询序列和目标序列之间的一个局部比对区域。

    Attributes:
        num: HSP编号
        bit_score: 标准化得分，可跨不同BLAST比较
        score: 原始得分
        evalue: 期望值，越小越显著（<0.05显著）
        identity: 完全匹配数
        positive: 相似残基数（仅蛋白质BLAST）
        gaps: 空位数
        align_len: 比对长度
        query_from: 查询序列起始位置
        query_to: 查询序列终止位置
        hit_from: 目标序列起始位置
        hit_to: 目标序列终止位置
        query_frame: 查询序列阅读框（blastx/tblastx）
        hit_frame: 目标序列阅读框（tblastn/tblastx）
        query_seq: 查询序列比对部分
        hit_seq: 目标序列比对部分
        midline: 比对中线（显示匹配情况）
        sc_match: 简单匹配数（仅blastn）
        sc_mismatch: 简单错配数（仅blastn）
    """
    num: int
    bit_score: float
    score: int
    evalue: float
    identity: int
    align_len: int
    query_from: int
    query_to: int
    hit_from: int
    hit_to: int
    gaps: int = 0
    positive: Optional[int] = None  # 仅蛋白质BLAST
    query_frame: Optional[int] = None  # 仅blastx/tblastx
    hit_frame: Optional[int] = None  # 仅tblastn/tblastx
    query_seq: str = ""
    hit_seq: str = ""
    midline: str = ""
    sc_match: Optional[int] = None  # 仅blastn
    sc_mismatch: Optional[int] = None  # 仅blastn

    @property
    def identity_percent(self) -> float:
        """计算一致性百分比"""
        if self.align_len == 0:
            return 0.0
        return (self.identity / self.align_len) * 100

    @property
    def gap_percent(self) -> float:
        """计算空位百分比"""
        if self.align_len == 0:
            return 0.0
        return (self.gaps / self.align_len) * 100

    @property
    def positive_percent(self) -> Optional[float]:
        """计算相似度百分比（仅蛋白质BLAST）"""
        if self.positive is None or self.align_len == 0:
            return None
        return (self.positive / self.align_len) * 100

    def is_significant(self, evalue_threshold: float = 0.05) -> bool:
        """判断HSP是否显著"""
        return self.evalue < evalue_threshold

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "num": self.num,
            "bit_score": self.bit_score,
            "score": self.score,
            "evalue": self.evalue,
            "identity": self.identity,
            "identity_percent": round(self.identity_percent, 2),
            "positive": self.positive,
            "positive_percent": round(self.positive_percent, 2) if self.positive_percent else None,
            "gaps": self.gaps,
            "gap_percent": round(self.gap_percent, 2),
            "align_len": self.align_len,
            "query_from": self.query_from,
            "query_to": self.query_to,
            "hit_from": self.hit_from,
            "hit_to": self.hit_to,
            "query_frame": self.query_frame,
            "hit_frame": self.hit_frame,
            "sc_match": self.sc_match,
            "sc_mismatch": self.sc_mismatch
        }


@dataclass
class Hit:
    """
    比对命中结果

    表示一个数据库序列与查询序列的比对结果，包含一个或多个HSP。

    Attributes:
        num: 命中编号
        id: 序列标识符
        accession: 登录号
        definition: 序列描述
        length: 序列长度
        hsps: HSP列表
        species: 物种信息（可选，从物种文件解析）
    """
    num: int
    id: str
    accession: str
    definition: str
    length: int
    hsps: List[HSP] = field(default_factory=list)
    species: Optional[str] = None

    @property
    def best_hsp(self) -> Optional[HSP]:
        """获取最佳HSP（bit_score最高）"""
        if not self.hsps:
            return None
        return max(self.hsps, key=lambda h: h.bit_score)

    @property
    def worst_hsp(self) -> Optional[HSP]:
        """获取最差HSP（bit_score最低）"""
        if not self.hsps:
            return None
        return min(self.hsps, key=lambda h: h.bit_score)

    @property
    def total_hsps(self) -> int:
        """HSP总数"""
        return len(self.hsps)

    @property
    def significant_hsps(self) -> List[HSP]:
        """获取显著的HSP列表"""
        return [hsp for hsp in self.hsps if hsp.is_significant()]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "num": self.num,
            "id": self.id,
            "accession": self.accession,
            "definition": self.definition,
            "length": self.length,
            "species": self.species,
            "total_hsps": self.total_hsps,
            "best_bit_score": self.best_hsp.bit_score if self.best_hsp else None,
            "best_evalue": self.best_hsp.evalue if self.best_hsp else None
        }


@dataclass
class BlastResult:
    """
    BLAST比对结果

    包含整个BLAST比对的结果信息。

    Attributes:
        program: BLAST程序类型
        version: BLAST版本
        database: 数据库名称
        query_id: 查询序列ID
        query_def: 查询序列描述
        query_len: 查询序列长度
        parameters: 比对参数
        hits: 命中列表
    """
    program: BlastProgram
    version: str
    database: str
    query_id: str
    query_def: str
    query_len: int
    parameters: Dict[str, Any] = field(default_factory=dict)
    hits: List[Hit] = field(default_factory=list)

    @property
    def total_hits(self) -> int:
        """命中总数"""
        return len(self.hits)

    @property
    def total_hsps(self) -> int:
        """HSP总数"""
        return sum(len(hit.hsps) for hit in self.hits)

    @property
    def best_hit(self) -> Optional[Hit]:
        """获取最佳命中"""
        if not self.hits:
            return None
        return max(self.hits, key=lambda h: h.best_hsp.bit_score if h.best_hsp else 0)

    @property
    def significant_hits(self) -> List[Hit]:
        """获取有显著HSP的命中列表"""
        return [hit for hit in self.hits if hit.significant_hsps]

    def get_top_hits(self, n: int = 10) -> List[Hit]:
        """获取前N个最佳命中"""
        sorted_hits = sorted(
            self.hits,
            key=lambda h: h.best_hsp.bit_score if h.best_hsp else 0,
            reverse=True
        )
        return sorted_hits[:n]

    def to_summary_dict(self) -> Dict[str, Any]:
        """生成摘要字典"""
        return {
            "program": self.program.value,
            "version": self.version,
            "database": self.database,
            "query_id": self.query_id,
            "query_def": self.query_def,
            "query_len": self.query_len,
            "parameters": self.parameters,
            "total_hits": self.total_hits,
            "total_hsps": self.total_hsps,
            "significant_hits": len(self.significant_hits)
        }
