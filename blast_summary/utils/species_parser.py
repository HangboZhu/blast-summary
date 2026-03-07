"""
物种信息文件解析器

解析 Tax BLAST report 格式的物种信息文件 (_18.txt)
"""

import re
from typing import Dict, Optional
from pathlib import Path


def parse_species_file(file_path: str) -> Dict[str, str]:
    """
    解析物种信息文件，返回 accession -> species 的映射

    Args:
        file_path: 物种信息文件路径

    Returns:
        Dict[str, str]: accession号到物种名的映射

    Example:
        >>> species_map = parse_species_file("SININ0IZZWN_18.txt")
        >>> species_map["P69905"]
        'Homo sapiens (human) [primates]'
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Species file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    return parse_species_content(content)


def parse_species_content(content: str) -> Dict[str, str]:
    """
    解析物种信息文件内容

    Args:
        content: 文件内容

    Returns:
        Dict[str, str]: accession号到物种名的映射
    """
    species_map: Dict[str, str] = {}
    current_species: Optional[str] = None

    lines = content.split('\n')
    for line in lines:
        stripped = line.strip()

        # Skip empty lines and header lines
        if not stripped:
            continue

        # Skip header/title lines
        if 'Tax BLAST report' in line or 'Organism Report' in line:
            continue
        if line.startswith('Query=') or line.startswith('Length='):
            continue
        if 'Accession' in line and 'Description' in line:
            continue

        # Check if this is a species line (ends with classification in brackets)
        # Species line format: "Species name (common name) [classification]"
        # The line usually starts with whitespace and ends with ']'
        species_match = _parse_species_line(line)
        if species_match:
            current_species = species_match
            continue

        # Check if this is an accession line
        # Accession line format: " P69905    RecName: Full=...  317   3e-109"
        accession = _parse_accession_line(line)
        if accession and current_species:
            species_map[accession] = current_species

    return species_map


def _parse_species_line(line: str) -> Optional[str]:
    """
    解析物种行

    物种行特征：
    - 以空白开头
    - 包含物种名称和分类，以方括号结尾
    - 格式如: "                                   Homo sapiens (human) [primates]"

    Args:
        line: 单行文本

    Returns:
        物种名称字符串，如果不是物种行则返回 None
    """
    # Check if line ends with classification bracket
    if not re.search(r'\[[^\]]+\]\s*$', line):
        return None

    # Check if line starts with whitespace (species lines are indented)
    if not line.startswith(' ') and not line.startswith('\t'):
        return None

    # Extract species name (strip whitespace)
    stripped = line.strip()

    # Verify it's not an accession line (accession lines start with alphanumeric)
    # Species lines start with the species name (e.g., "Homo sapiens")
    if re.match(r'^[A-Z0-9]+\s+', stripped):
        # This looks like an accession line
        return None

    return stripped


def _parse_accession_line(line: str) -> Optional[str]:
    """
    解析 accession 行

    Accession 行特征：
    - 以空白开头，然后是 Accession 号
    - 格式如: " P69905    RecName: Full=Hemoglobin subunit alpha; ...  317   3e-109"

    Args:
        line: 单行文本

    Returns:
        Accession 号字符串，如果不是 accession 行则返回 None
    """
    # Check if line starts with whitespace followed by an accession
    # Accession format: typically alphanumeric, like P69905, NP_001234, etc.
    match = re.match(r'^\s+([A-Za-z0-9]+)\s+', line)
    if match:
        accession = match.group(1)
        # Skip if it looks like a header word
        if accession.lower() in ('accession', 'description', 'score', 'e-value'):
            return None
        return accession

    return None
