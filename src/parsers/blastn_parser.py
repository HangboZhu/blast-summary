"""
blastn解析器

解析核苷酸-核苷酸BLAST结果。
"""

import xml.etree.ElementTree as ET
from .base_parser import BaseParser
from ..models.blast_result import HSP


class BlastnParser(BaseParser):
    """
    blastn解析器

    专门处理blastn类型的BLAST结果，包含blastn特有的字段如sc-match和sc-mismatch。
    """

    def _parse_hsp(self, hsp_elem: ET.Element) -> HSP:
        """解析blastn HSP"""
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
            # blastn特有字段
            sc_match=self._get_elem_int(hsp_elem, "Hsp_sc-match"),
            sc_mismatch=self._get_elem_int(hsp_elem, "Hsp_sc-mismatch")
        )
        return hsp
