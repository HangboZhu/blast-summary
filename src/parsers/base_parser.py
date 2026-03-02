"""
BLAST解析器基类

提供XML解析的通用功能。
"""

import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Optional, List

from ..models.blast_result import BlastResult, Hit, HSP, BlastProgram


class BaseParser(ABC):
    """
    BLAST解析器基类

    提供XML解析的通用方法，子类需要实现特定类型的解析逻辑。
    """

    def __init__(self):
        self.root: Optional[ET.Element] = None

    def parse(self, xml_content: str) -> BlastResult:
        """
        解析BLAST XML输出

        Args:
            xml_content: BLAST XML格式内容

        Returns:
            BlastResult对象
        """
        self.root = ET.fromstring(xml_content)
        return self._parse_result()

    def parse_file(self, file_path: str) -> BlastResult:
        """
        解析BLAST XML文件

        Args:
            file_path: BLAST XML文件路径

        Returns:
            BlastResult对象
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse(content)

    def _parse_result(self) -> BlastResult:
        """解析BLAST结果"""
        # 解析基本信息
        program = self._get_program()
        version = self._get_text("BlastOutput_version")
        database = self._get_text("BlastOutput_db")
        query_id = self._get_text("BlastOutput_query-ID")
        query_def = self._get_text("BlastOutput_query-def")
        query_len = int(self._get_text("BlastOutput_query-len", "0"))

        # 解析参数
        parameters = self._parse_parameters()

        # 解析命中
        hits = self._parse_hits()

        return BlastResult(
            program=program,
            version=version,
            database=database,
            query_id=query_id,
            query_def=query_def,
            query_len=query_len,
            parameters=parameters,
            hits=hits
        )

    def _get_program(self) -> BlastProgram:
        """获取BLAST程序类型"""
        program_text = self._get_text("BlastOutput_program", "blastn")
        program_map = {
            "blastn": BlastProgram.BLASTN,
            "blastp": BlastProgram.BLASTP,
            "blastx": BlastProgram.BLASTX,
            "tblastn": BlastProgram.TBLASTN,
            "tblastx": BlastProgram.TBLASTX
        }
        return program_map.get(program_text.lower(), BlastProgram.BLASTN)

    def _get_text(self, tag: str, default: str = "") -> str:
        """获取标签文本内容"""
        element = self.root.find(f".//{tag}")
        if element is not None and element.text:
            return element.text
        return default

    def _parse_parameters(self) -> dict:
        """解析比对参数"""
        params = {}
        param_elem = self.root.find(".//Parameters")
        if param_elem is not None:
            for child in param_elem:
                tag = child.tag.replace("Parameters_", "")
                params[tag] = child.text if child.text else ""
        return params

    def _parse_hits(self) -> List[Hit]:
        """解析命中列表"""
        hits = []
        iteration = self.root.find(".//Iteration")
        if iteration is None:
            return hits

        hit_elements = iteration.findall(".//Hit")
        for hit_elem in hit_elements:
            hit = self._parse_hit(hit_elem)
            if hit:
                hits.append(hit)
        return hits

    def _parse_hit(self, hit_elem: ET.Element) -> Optional[Hit]:
        """解析单个命中"""
        num = int(self._get_elem_text(hit_elem, "Hit_num", "0"))
        hit_id = self._get_elem_text(hit_elem, "Hit_id")
        accession = self._get_elem_text(hit_elem, "Hit_accession")
        definition = self._get_elem_text(hit_elem, "Hit_def")
        length = int(self._get_elem_text(hit_elem, "Hit_len", "0"))

        # 解析HSPs
        hsps = []
        hsp_elements = hit_elem.findall(".//Hsp")
        for hsp_elem in hsp_elements:
            hsp = self._parse_hsp(hsp_elem)
            hsps.append(hsp)

        return Hit(
            num=num,
            id=hit_id,
            accession=accession,
            definition=definition,
            length=length,
            hsps=hsps
        )

    @abstractmethod
    def _parse_hsp(self, hsp_elem: ET.Element) -> HSP:
        """解析HSP，子类需要实现"""
        pass

    def _get_elem_text(self, parent: ET.Element, tag: str, default: str = "") -> str:
        """获取子元素文本"""
        element = parent.find(tag)
        if element is not None and element.text:
            return element.text
        return default

    def _get_elem_int(self, parent: ET.Element, tag: str, default: int = 0) -> int:
        """获取子元素整数值"""
        text = self._get_elem_text(parent, tag, str(default))
        try:
            return int(float(text))
        except (ValueError, TypeError):
            return default

    def _get_elem_float(self, parent: ET.Element, tag: str, default: float = 0.0) -> float:
        """获取子元素浮点值"""
        text = self._get_elem_text(parent, tag, str(default))
        try:
            return float(text)
        except (ValueError, TypeError):
            return default
