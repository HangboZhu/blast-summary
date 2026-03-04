"""
tblastn解析器

解析蛋白质-核苷酸翻译BLAST结果。
"""

import xml.etree.ElementTree as ET
from .base_parser import BaseParser
from ..models.blast_result import HSP


class TblastnParser(BaseParser):
    """
    tblastn解析器

    专门处理tblastn类型的BLAST结果。
    tblastn将蛋白质序列与核苷酸数据库（翻译成蛋白质）进行比对，
    因此包含hit-frame（目标序列阅读框）信息。
    """

    def _parse_hsp(self, hsp_elem: ET.Element) -> HSP:
        """解析tblastn HSP"""
        hsp = HSP(
            num=self._get_elem_int(hsp_elem, "Hsp_num"),
            bit_score=self._get_elem_float(hsp_elem, "Hsp_bit-score"),
            score=self._get_elem_int(hsp_elem, "Hsp_score"),
            evalue=self._get_elem_float(hsp_elem, "Hsp_evalue"),
            identity=self._get_elem_int(hsp_elem, "Hsp_identity"),
            align_len=self._get_elem_int(hsp_elem, "Hsp_align-len"),
            query_from=self._get_elem_int(hsp_elem, "Hsp_query-from"),
            query_to=self._get_elem_int(hsp_elem, "Hsp_query-to"),
            hit_from=self._get_elem_int(hsp_elem, "Hsp_hit-from"),
            hit_to=self._get_elem_int(hsp_elem, "Hsp_hit-to"),
            gaps=self._get_elem_int(hsp_elem, "Hsp_gaps"),
            query_seq=self._get_elem_text(hsp_elem, "Hsp_qseq"),
            hit_seq=self._get_elem_text(hsp_elem, "Hsp_hseq"),
            midline=self._get_elem_text(hsp_elem, "Hsp_midline"),
            # tblastn特有字段
            positive=self._get_elem_int(hsp_elem, "Hsp_positive"),
            query_frame=self._get_elem_int(hsp_elem, "Hsp_query-frame"),
            hit_frame=self._get_elem_int(hsp_elem, "Hsp_hit-frame")
        )
        return hsp
