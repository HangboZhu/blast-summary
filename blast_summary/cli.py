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

    # Create analyzer
    analyzer = create_analyzer(result)

    # Generate basic summary
    print("\nGenerating analysis report...")
    basic_summary = analyzer.generate_summary_text()

    # Use AI to generate biological interpretation (if API is configured)
    ai_summary = ""
    if config.ai and not args.no_ai:
        print("\nGenerating biological interpretation with AI...")
        try:
            ai_client = create_ai_client(config)
            if ai_client:
                context = analyzer.prepare_ai_context()
                ai_summary = ai_client.generate_summary(
                    result.program.value,
                    context
                )
                print("AI analysis completed")
        except Exception as e:
            print(f"Warning: AI analysis failed - {e}")
            ai_summary = f"\n\n**AI analysis temporarily unavailable**: {str(e)}"

    # Combine reports
    full_report = combine_reports(basic_summary, ai_summary)

    # Output results
    output_path = determine_output_path(args, result, config)

    if args.stdout:
        print("\n" + "=" * 60)
        print(full_report)
    else:
        save_report(full_report, output_path)
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

    # Specify output file
    blast-summary -i data/blastn/blastn_example.txt -o output/report.md

    # Output to stdout
    blast-summary -i data/blastx/blastx_example.txt --stdout

    # Skip AI analysis
    blast-summary -i data/tblastn/tblastn_example.txt --no-ai
        """
    )

    parser.add_argument(
        "-i", "--input",
        dest="blast_file",
        required=True,
        help="Input BLAST XML file path"
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

    return parser.parse_args()


def create_analyzer(result):
    """Create analyzer based on BLAST type"""
    if result.program == BlastProgram.BLASTN:
        return NucleotideAnalyzer(result)
    else:
        return ProteinAnalyzer(result)


def combine_reports(basic_summary: str, ai_summary: str) -> str:
    """Combine basic report and AI analysis"""
    report_parts = [basic_summary]

    if ai_summary:
        report_parts.append("\n---\n")
        report_parts.append("## 生物学解释\n")
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


if __name__ == "__main__":
    sys.exit(main())
