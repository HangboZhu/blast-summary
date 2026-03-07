"""
tblastx解析器

解析核苷酸翻译-核苷酸翻译BLAST结果。
"""

import xml.etree.ElementTree as ET
from .base_parser import BaseParser
from ..models.blast_result import HSP


class TblastxParser(BaseParser):
    """
    tblastx解析器

    专门处理tblastx类型的BLAST结果。
    tblastx将核苷酸查询序列翻译成蛋白质，
    与核苷酸数据库（翻译成蛋白质）进行比对，
    因此同时包含query-frame和hit-frame信息。
    """

    def _parse_hsp(self, hsp_elem: ET.Element) -> HSP:
        """解析tblastx HSP"""
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
            # tblastx特有字段（同时有query_frame和hit_frame）
            positive=self._get_elem_int(hsp_elem, "Hsp_positive"),
            query_frame=self._get_elem_int(hsp_elem, "Hsp_query-frame"),
            hit_frame=self._get_elem_int(hsp_elem, "Hsp_hit-frame")
        )
        return hsp
