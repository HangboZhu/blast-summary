#!/usr/bin/env python3
"""
BLAST结果AI总结工具 - 主入口

用法:
    python -m src.main <blast_file> [--output <output_file>]
    python -m src.main --help
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .config import get_config, reload_config
from .parsers.parser_factory import ParserFactory
from .analyzers.nucleotide_analyzer import NucleotideAnalyzer
from .analyzers.protein_analyzer import ProteinAnalyzer
from .ai.openai_client import create_ai_client
from .models.blast_result import BlastProgram


def main():
    """主函数"""
    args = parse_args()

    # 加载配置
    config = get_config()
    if args.env_file:
        config = reload_config(args.env_file)

    # 确保输出目录存在
    config.ensure_output_dir()

    # 解析BLAST文件
    print(f"正在解析BLAST文件: {args.blast_file}")
    try:
        result = ParserFactory.auto_detect_and_parse_file(args.blast_file)
        print(f"成功解析BLAST结果，类型: {result.program.value}")
        print(f"总命中数: {result.total_hits}")
    except Exception as e:
        print(f"错误: 解析BLAST文件失败 - {e}")
        sys.exit(1)

    # 创建分析器
    analyzer = create_analyzer(result)

    # 生成基础摘要
    print("\n生成分析报告...")
    basic_summary = analyzer.generate_summary_text()

    # 使用AI生成生物学解释（如果配置了API）
    ai_summary = ""
    if config.ai and not args.no_ai:
        print("\n正在使用AI生成生物学解释...")
        try:
            ai_client = create_ai_client(config)
            if ai_client:
                context = analyzer.prepare_ai_context()
                ai_summary = ai_client.generate_summary(
                    result.program.value,
                    context
                )
                print("AI分析完成")
        except Exception as e:
            print(f"警告: AI分析失败 - {e}")
            ai_summary = f"\n\n**AI分析暂时不可用**: {str(e)}"

    # 合并报告
    full_report = combine_reports(basic_summary, ai_summary)

    # 输出结果
    output_path = determine_output_path(args, result, config)

    if args.stdout:
        print("\n" + "=" * 60)
        print(full_report)
    else:
        save_report(full_report, output_path)
        print(f"\n报告已保存到: {output_path}")

    return 0


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="BLAST结果AI总结工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 分析blastp结果
    python -m src.main data/blastp/blastp_example.txt

    # 指定输出文件
    python -m src.main data/blastn/blastn_example.txt -o output/report.md

    # 输出到标准输出
    python -m src.main data/blastx/blastx_example.txt --stdout

    # 不使用AI分析
    python -m src.main data/tblastn/tblastn_example.txt --no-ai
        """
    )

    parser.add_argument(
        "blast_file",
        help="BLAST XML输出文件路径"
    )

    parser.add_argument(
        "-o", "--output",
        dest="output_file",
        help="输出文件路径（默认自动生成）"
    )

    parser.add_argument(
        "--env-file",
        help=".env配置文件路径"
    )

    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="不使用AI分析，仅生成基础报告"
    )

    parser.add_argument(
        "--stdout",
        action="store_true",
        help="输出到标准输出而非文件"
    )

    return parser.parse_args()


def create_analyzer(result):
    """根据BLAST类型创建对应的分析器"""
    if result.program == BlastProgram.BLASTN:
        return NucleotideAnalyzer(result)
    else:
        return ProteinAnalyzer(result)


def combine_reports(basic_summary: str, ai_summary: str) -> str:
    """合并基础报告和AI分析"""
    report_parts = [basic_summary]

    if ai_summary:
        report_parts.append("\n---\n")
        report_parts.append("## AI生物学解释\n")
        report_parts.append(ai_summary)

    report_parts.append("\n\n---\n")
    report_parts.append("*报告由BLAST AI总结工具生成*\n")

    return "\n".join(report_parts)


def determine_output_path(args, result, config) -> Path:
    """确定输出文件路径"""
    if args.output_file:
        return Path(args.output_file)

    # 自动生成文件名
    query_name = result.query_def.split()[0] if result.query_def else "unknown"
    blast_type = result.program.value
    filename = f"{blast_type}_{query_name}_summary.md"

    return config.output_dir / "summaries" / filename


def save_report(report: str, output_path: Path):
    """保存报告到文件"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)


if __name__ == "__main__":
    sys.exit(main())
