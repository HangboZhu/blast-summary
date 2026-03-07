"""
解析器工厂

根据BLAST类型创建相应的解析器。
"""

from typing import Optional
from .base_parser import BaseParser
from .blastn_parser import BlastnParser
from .blastp_parser import BlastpParser
from .blastx_parser import BlastxParser
from .tblastn_parser import TblastnParser
from .tblastx_parser import TblastxParser
from ..models.blast_result import BlastProgram, BlastResult


class ParserFactory:
    """
    解析器工厂类

    根据BLAST程序类型创建对应的解析器实例。
    """

    # 解析器注册表
    _parsers = {
        BlastProgram.BLASTN: BlastnParser,
        BlastProgram.BLASTP: BlastpParser,
        BlastProgram.BLASTX: BlastxParser,
        BlastProgram.TBLASTN: TblastnParser,
        BlastProgram.TBLASTX: TblastxParser,
    }

    @classmethod
    def create_parser(cls, program: BlastProgram) -> BaseParser:
        """
        创建指定类型的解析器

        Args:
            program: BLAST程序类型

        Returns:
            对应的解析器实例

        Raises:
            ValueError: 不支持的BLAST类型
        """
        parser_class = cls._parsers.get(program)
        if parser_class is None:
            raise ValueError(f"Unsupported BLAST program: {program}")
        return parser_class()

    @classmethod
    def create_parser_from_string(cls, program_name: str) -> BaseParser:
        """
        根据程序名称字符串创建解析器

        Args:
            program_name: BLAST程序名称（如"blastn", "blastp"等）

        Returns:
            对应的解析器实例

        Raises:
            ValueError: 不支持的BLAST类型
        """
        program_map = {
            "blastn": BlastProgram.BLASTN,
            "blastp": BlastProgram.BLASTP,
            "blastx": BlastProgram.BLASTX,
            "tblastn": BlastProgram.TBLASTN,
            "tblastx": BlastProgram.TBLASTX,
        }
        program = program_map.get(program_name.lower())
        if program is None:
            raise ValueError(f"Unsupported BLAST program: {program_name}")
        return cls.create_parser(program)

    @classmethod
    def auto_detect_and_parse(cls, xml_content: str) -> BlastResult:
        """
        自动检测BLAST类型并解析

        Args:
            xml_content: BLAST XML内容

        Returns:
            BlastResult对象
        """
        import xml.etree.ElementTree as ET

        # 解析XML获取程序类型
        root = ET.fromstring(xml_content)
        program_elem = root.find("BlastOutput_program")
        if program_elem is None or program_elem.text is None:
            raise ValueError("Cannot determine BLAST program type")

        program_name = program_elem.text.lower()
        parser = cls.create_parser_from_string(program_name)
        return parser.parse(xml_content)

    @classmethod
    def auto_detect_and_parse_file(cls, file_path: str) -> BlastResult:
        """
        自动检测BLAST类型并解析文件

        Args:
            file_path: BLAST XML文件路径

        Returns:
            BlastResult对象
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return cls.auto_detect_and_parse(content)
