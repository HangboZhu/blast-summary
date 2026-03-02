"""
blastp解析器

解析蛋白质-蛋白质BLAST结果。
"""

import xml.etree.ElementTree as ET
from .base_parser import BaseParser
from ..models.blast_result import HSP


class BlastpParser(BaseParser):
    """
    blastp解析器

    专门处理blastp类型的BLAST结果，包含蛋白质BLAST特有的字段如positive（相似残基数）。
    """

    def _parse_hsp(self, hsp_elem: ET.Element) -> HSP:
        """解析blastp HSP"""
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
            # blastp特有字段
            positive=self._get_elem_int(hsp_elem, "Hsp_positive")
        )
        return hsp
