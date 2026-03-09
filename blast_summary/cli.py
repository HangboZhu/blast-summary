#!/usr/bin/env python3
"""
BLAST Result AI Summary Tool - CLI Entry Point

This module serves as the package's CLI entry point and can be called from command line.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .config import Config
from .parsers.parser_factory import ParserFactory
from .analyzers.nucleotide_analyzer import NucleotideAnalyzer
from .analyzers.protein_analyzer import ProteinAnalyzer
from .ai.openai_client import create_ai_client
from .models.blast_result import BlastProgram
from .utils.species_parser import parse_species_file
from .utils.statistics import format_blast_params


def main():
    """Main function - CLI entry point"""
    args = parse_args()

    # Load configuration
    if args.env_file:
        config = Config.from_env(args.env_file)
    else:
        config = Config.from_env()

    # Ensure output directory exists
    config.ensure_output_dir()

    # Parse BLAST file
    print(f"Parsing BLAST file: {args.blast_file}")
    try:
        result = ParserFactory.auto_detect_and_parse_file(args.blast_file)
        print(f"Successfully parsed BLAST result, type: {result.program.value}")
        print(f"Total hits: {result.total_hits}")
    except Exception as e:
        print(f"Error: Failed to parse BLAST file - {e}")
        sys.exit(1)

    # Check for no hits
    if not result.hits:
        print("No hits found, generating empty report")
        no_hits_report = generate_no_hits_report(result)
        output_path = determine_output_path(args, result, config)

        if args.stdout:
            print("\n" + "=" * 60)
            print(no_hits_report)
        else:
            save_report(no_hits_report, output_path)
            print(f"\nReport saved to: {output_path}")

        return 0

    # Parse species file if provided
    species_map = {}
    if args.species_file:
        print(f"Parsing species file: {args.species_file}")
        try:
            species_map = parse_species_file(args.species_file)
            print(f"Found {len(species_map)} species mappings")

            # Map species to hits
            for hit in result.hits:
                if hit.accession in species_map:
                    hit.species = species_map[hit.accession]
        except Exception as e:
            print(f"Warning: Failed to parse species file - {e}")
            # Continue without species information

    # Create analyzer
    analyzer = create_analyzer(result)

    # Generate basic summary
    print("\nGenerating analysis report...")
    basic_summary = analyzer.generate_summary_text()

    # Determine output path early for streaming
    output_path = determine_output_path(args, result, config)

    # Use AI to generate biological interpretation (if API is configured)
    ai_summary = ""
    if config.ai and not args.no_ai:
        print("\nGenerating biological interpretation with AI...")
        try:
            ai_client = create_ai_client(config)
            if ai_client:
                context = analyzer.prepare_ai_context()

                # 流式模式：边生成边写入
                if args.stream:
                    ai_summary = generate_ai_summary_stream(
                        ai_client, result.program.value, context,
                        basic_summary, output_path, args.stdout
                    )
                else:
                    ai_summary = ai_client.generate_summary(
                        result.program.value,
                        context
                    )
                    print("AI analysis completed")
        except Exception as e:
            print(f"Warning: AI analysis failed - {e}")
            ai_summary = f"\n\n**AI analysis temporarily unavailable**: {str(e)}"

    # Combine reports and output (非流式模式或有错误时)
    if not args.stream or not config.ai or args.no_ai:
        full_report = combine_reports(basic_summary, ai_summary)

        if args.stdout:
            print("\n" + "=" * 60)
            print(full_report)
        else:
            save_report(full_report, output_path)
            print(f"\nReport saved to: {output_path}")
    elif args.stream and not args.stdout:
        print(f"\nReport saved to: {output_path}")

    return 0


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="BLAST Result AI Summary Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Analyze blastp result
    blast-summary -i data/blastp/blastp_example.txt

    # Analyze with species information file
    blast-summary -i data/blastp/blastp_5.txt -s data/blastp/blastp_18.txt

    # Specify output file
    blast-summary -i data/blastn/blastn_example.txt -o output/report.md

    # Output to stdout
    blast-summary -i data/blastx/blastx_example.txt --stdout

    # Skip AI analysis
    blast-summary -i data/tblastn/tblastn_example.txt --no-ai

    # Enable streaming output (real-time file writing)
    blast-summary -i data/blastp/blastp_5.txt --stream

    # Streaming output to stdout
    blast-summary -i data/blastp/blastp_5.txt --stream --stdout
        """
    )

    parser.add_argument(
        "-i", "--input",
        dest="blast_file",
        required=True,
        help="Input BLAST XML file path"
    )

    parser.add_argument(
        "-s", "--species_file",
        dest="species_file",
        help="Species information file path (Tax BLAST report format, e.g. *_18.txt)"
    )

    parser.add_argument(
        "-o", "--output",
        dest="output_file",
        help="Output file path (default: output/summaries/{blast_type}_{query_name}_summary.md)"
    )

    parser.add_argument(
        "--env-file",
        help="Path to .env configuration file (default: .env in project root)"
    )

    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Skip AI analysis, generate basic report only"
    )

    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Output to stdout instead of file"
    )

    parser.add_argument(
        "--stream",
        action="store_true",
        help="Enable streaming output, write to file in real-time"
    )

    return parser.parse_args()


def create_analyzer(result):
    """Create analyzer based on BLAST type"""
    if result.program == BlastProgram.BLASTN:
        return NucleotideAnalyzer(result)
    else:
        return ProteinAnalyzer(result)


def generate_no_hits_report(result) -> str:
    """
    生成无命中结果的报告

    Args:
        result: BLAST结果对象

    Returns:
        报告文本
    """
    blast_type = result.program.value.upper()

    lines = [
        f"## {blast_type} 分析报告",
        "",
    ]

    # 添加参数信息
    lines.append(format_blast_params(result))

    lines.extend([
        "### 比对结果",
        "",
        "**未找到命中结果 (No hits found)**",
        "",
        "---",
        "",
        "### 结果说明",
        "",
        "本次 BLAST 比对未找到任何显著的匹配序列。可能的原因包括：",
        "",
        "1. **查询序列质量较差**: 序列可能包含过多未知碱基或测序错误",
        "2. **数据库覆盖不足**: 目标数据库中可能不存在与查询序列相似的序列",
        "3. **参数设置过于严格**: E值阈值过小或其他参数限制了匹配范围",
        "4. **序列类型不匹配**: 例如用核苷酸序列搜索蛋白质数据库",
        "",
        "### 建议",
        "",
        "- 尝试使用更宽松的 E 值阈值重新搜索",
        "- 更换或扩大目标数据库范围",
        "- 检查查询序列是否正确（方向、格式等）",
        "- 考虑使用其他 BLAST 程序（如 blastx 翻译后搜索）",
    ])

    return "\n".join(lines)


def combine_reports(basic_summary: str, ai_summary: str) -> str:
    """Combine basic report and AI analysis"""
    report_parts = [basic_summary]

    if ai_summary:
        report_parts.append("\n---\n")
        report_parts.append("## 生物学解释\n\n")
        report_parts.append(ai_summary)

    return "\n".join(report_parts)


def determine_output_path(args, result, config) -> Path:
    """Determine output file path"""
    if args.output_file:
        return Path(args.output_file)

    # Auto-generate filename
    query_name = result.query_def.split()[0] if result.query_def else "unknown"
    blast_type = result.program.value
    filename = f"{blast_type}_{query_name}_summary.md"

    return config.output_dir / "summaries" / filename


def save_report(report: str, output_path: Path):
    """Save report to file"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)


def generate_ai_summary_stream(
    ai_client,
    blast_type: str,
    context: dict,
    basic_summary: str,
    output_path: Path,
    to_stdout: bool
) -> str:
    """
    流式生成 AI 摘要并实时写入文件

    Args:
        ai_client: AI客户端
        blast_type: BLAST类型
        context: AI上下文
        basic_summary: 基础报告
        output_path: 输出文件路径
        to_stdout: 是否输出到标准输出

    Returns:
        完整的AI摘要文本
    """
    # 准备报告头部（基础报告 + AI分隔符）
    header = basic_summary + "\n---\n\n## 生物学解释\n\n"

    # 确保输出目录存在
    if not to_stdout:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # 先写入基础报告头部
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(header)
        print(f"Streaming to: {output_path}")
    else:
        print("\n" + "=" * 60)
        print(header, end='')

    # 流式生成并写入
    full_ai_content = ""
    try:
        for chunk in ai_client.generate_summary_stream(blast_type, context):
            full_ai_content += chunk

            if to_stdout:
                print(chunk, end='', flush=True)
            else:
                # 追加写入文件
                with open(output_path, 'a', encoding='utf-8') as f:
                    f.write(chunk)
    except Exception as e:
        error_msg = f"\n\n**AI analysis failed**: {str(e)}"
        full_ai_content += error_msg
        if to_stdout:
            print(error_msg)
        elif not to_stdout:
            with open(output_path, 'a', encoding='utf-8') as f:
                f.write(error_msg)

    if to_stdout:
        print()  # 换行

    print("AI analysis completed (streaming)")
    return full_ai_content


if __name__ == "__main__":
    sys.exit(main())
