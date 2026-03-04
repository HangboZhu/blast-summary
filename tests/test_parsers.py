"""
BLAST解析器测试
"""

import pytest
from pathlib import Path

from blast_summary.parsers.parser_factory import ParserFactory
from blast_summary.models.blast_result import BlastProgram


# 测试数据路径
DATA_DIR = Path(__file__).parent.parent / "data"


class TestBlastpParser:
    """blastp解析器测试"""

    def test_parse_blastp_file(self):
        """测试解析blastp文件"""
        blastp_file = DATA_DIR / "blastp" / "blastp_example.txt"

        result = ParserFactory.auto_detect_and_parse_file(str(blastp_file))

        # 验证基本信息
        assert result.program == BlastProgram.BLASTP
        assert result.query_len == 393
        assert result.total_hits > 0

        # 验证最佳命中
        best_hit = result.best_hit
        assert best_hit is not None
        assert best_hit.best_hsp is not None

        # 验证HSP数据
        hsp = best_hit.best_hsp
        assert hsp.bit_score > 0
        assert hsp.evalue == 0
        assert hsp.identity_percent == 100.0  # 完全匹配

    def test_blastp_has_positive_field(self):
        """测试blastp包含positive字段"""
        blastp_file = DATA_DIR / "blastp" / "blastp_example.txt"

        result = ParserFactory.auto_detect_and_parse_file(str(blastp_file))
        hsp = result.best_hit.best_hsp

        # blastp应该有positive字段
        assert hsp.positive is not None
        assert hsp.positive_percent is not None


class TestBlastxParser:
    """blastx解析器测试"""

    def test_parse_blastx_file(self):
        """测试解析blastx文件"""
        blastx_file = DATA_DIR / "blastx" / "blastx_example.txt"

        result = ParserFactory.auto_detect_and_parse_file(str(blastx_file))

        # 验证基本信息
        assert result.program == BlastProgram.BLASTX
        assert result.query_len == 628
        assert result.total_hits > 0

    def test_blastx_has_query_frame(self):
        """测试blastx包含query_frame字段"""
        blastx_file = DATA_DIR / "blastx" / "blastx_example.txt"

        result = ParserFactory.auto_detect_and_parse_file(str(blastx_file))
        hsp = result.best_hit.best_hsp

        # blastx应该有query_frame
        assert hsp.query_frame is not None


class TestTblastnParser:
    """tblastn解析器测试"""

    def test_parse_tblastn_file(self):
        """测试解析tblastn文件"""
        tblastn_file = DATA_DIR / "tblastn" / "tblastn_example.txt"

        result = ParserFactory.auto_detect_and_parse_file(str(tblastn_file))

        # 验证基本信息
        assert result.program == BlastProgram.TBLASTN
        assert result.query_len == 2005
        assert result.total_hits > 0

    def test_tblastn_has_hit_frame(self):
        """测试tblastn包含hit_frame字段"""
        tblastn_file = DATA_DIR / "tblastn" / "tblastn_example.txt"

        result = ParserFactory.auto_detect_and_parse_file(str(tblastn_file))
        hsp = result.best_hit.best_hsp

        # tblastn应该有hit_frame
        assert hsp.hit_frame is not None


class TestParserFactory:
    """解析器工厂测试"""

    def test_create_parser_from_string(self):
        """测试从字符串创建解析器"""
        parser = ParserFactory.create_parser_from_string("blastp")
        assert parser is not None

        parser = ParserFactory.create_parser_from_string("BLASTN")
        assert parser is not None

    def test_invalid_program(self):
        """测试无效程序类型"""
        with pytest.raises(ValueError):
            ParserFactory.create_parser_from_string("invalid")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
