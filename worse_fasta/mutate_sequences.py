#!/usr/bin/env python3
"""
Random sequence mutator - 将原始序列随机修改
Supports both nucleotide and protein sequences
"""

import random
import argparse
from pathlib import Path


def read_fasta(filepath):
    """读取FASTA文件，返回header和sequence"""
    sequences = []
    current_header = None
    current_seq = []

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('>'):
                if current_header is not None:
                    sequences.append((current_header, ''.join(current_seq)))
                current_header = line
                current_seq = []
            elif line:
                current_seq.append(line)

        if current_header is not None:
            sequences.append((current_header, ''.join(current_seq)))

    return sequences


def write_fasta(filepath, sequences, line_width=70):
    """写入FASTA文件"""
    with open(filepath, 'w') as f:
        for header, seq in sequences:
            f.write(header + '\n')
            for i in range(0, len(seq), line_width):
                f.write(seq[i:i+line_width] + '\n')


def random_substitute(seq, substitution_rate, seq_type='nucleotide'):
    """随机替换字符"""
    if seq_type == 'nucleotide':
        bases = 'ATCG'
    else:
        bases = 'ACDEFGHIKLMNPQRSTVWY'

    seq_list = list(seq.upper())
    num_substitutions = int(len(seq) * substitution_rate)

    positions = random.sample(range(len(seq)), min(num_substitutions, len(seq)))

    for pos in positions:
        new_char = random.choice([b for b in bases if b != seq_list[pos]])
        seq_list[pos] = new_char

    return ''.join(seq_list)


def random_insert(seq, insertion_rate, seq_type='nucleotide'):
    """随机插入字符"""
    if seq_type == 'nucleotide':
        bases = 'ATCG'
    else:
        bases = 'ACDEFGHIKLMNPQRSTVWY'

    seq_list = list(seq.upper())
    num_insertions = int(len(seq) * insertion_rate)

    for _ in range(num_insertions):
        pos = random.randint(0, len(seq_list))
        new_char = random.choice(bases)
        seq_list.insert(pos, new_char)

    return ''.join(seq_list)


def random_delete(seq, deletion_rate):
    """随机删除字符"""
    seq_list = list(seq.upper())
    num_deletions = int(len(seq_list) * deletion_rate)
    if num_deletions >= len(seq_list):
        return seq_list[0] if seq_list else ''

    positions_to_delete = random.sample(range(len(seq_list)), num_deletions)
    positions_to_delete.sort(reverse=True)

    for pos in positions_to_delete:
        del seq_list[pos]

    return ''.join(seq_list)


def mutate_sequence(seq, seq_type='nucleotide', mutation_rate=0.15):
    """
    对序列进行随机修改

    mutation_rate: 修改比例 (0-1)，默认0.15即15%
    """
    if not seq:
        return seq

    # 替换比例为主，插入和删除为辅
    sub_rate = mutation_rate * 0.8   # 80%用于替换
    ins_rate = mutation_rate * 0.1   # 10%用于插入
    del_rate = mutation_rate * 0.1   # 10%用于删除

    mutated = seq.upper()

    # 随机替换
    mutated = random_substitute(mutated, sub_rate, seq_type)

    # 随机删除
    mutated = random_delete(mutated, del_rate)

    # 随机插入
    mutated = random_insert(mutated, ins_rate, seq_type)

    return mutated


def detect_sequence_type(seq):
    """检测序列类型（核苷酸或蛋白质）"""
    seq_chars = set(seq.upper())

    if seq_chars.issubset(set('ATCGN')):
        return 'nucleotide'

    protein_chars = set('ACDEFGHIKLMNPQRSTVWY')
    if seq_chars & (protein_chars - set('ATCG')):
        return 'protein'

    if len(seq_chars) <= 5:
        return 'nucleotide'
    return 'protein'


def process_fasta_file(input_path, output_path, mutation_rate=0.15):
    """处理单个FASTA文件"""
    sequences = read_fasta(input_path)

    if not sequences:
        print(f"Warning: No sequences found in {input_path}")
        return

    mutated_sequences = []
    for header, seq in sequences:
        seq_type = detect_sequence_type(seq)
        mutated_seq = mutate_sequence(seq, seq_type, mutation_rate)
        mutated_sequences.append((header, mutated_seq))

    write_fasta(output_path, mutated_sequences)
    print(f"Processed: {input_path.name} -> {output_path.name}")
    print(f"  Original length: {sum(len(s) for _, s in sequences)}")
    print(f"  Mutated length: {sum(len(s) for _, s in mutated_sequences)}")


def main():
    parser = argparse.ArgumentParser(description='随机修改FASTA序列')
    parser.add_argument('-r', '--rate', type=float, default=0.15,
                        help='修改比例 (0-1), 默认0.15即15%%')
    args = parser.parse_args()

    mutation_rate = args.rate
    if mutation_rate < 0 or mutation_rate > 1:
        print("Error: mutation rate must be between 0 and 1")
        return

    current_dir = Path(__file__).parent
    worse_dir = current_dir / 'worse'
    worse_dir.mkdir(exist_ok=True)

    file_mappings = {
        # 'blastn_original.fasta': 'blastn_worse.fasta',
        # 'blastp_original.fasta': 'blastp_worse.fasta',
        # 'blastx_original.fasta': 'blastx_worse.fasta',
        # 'tblastn_original.fasta': 'tblastn_worse.fasta',
        "tblastx_original.fasta": 'tblastx_worse.fasta',
    }

    print("=" * 60)
    print(f"Sequence Mutator - Mutation rate: {mutation_rate*100:.0f}%")
    print("=" * 60)

    for original_name, worse_name in file_mappings.items():
        input_path = current_dir / original_name
        output_path = worse_dir / worse_name

        if not input_path.exists():
            print(f"Skipping: {original_name} (not found)")
            continue

        if input_path.stat().st_size == 0:
            print(f"Skipping: {original_name} (empty file)")
            continue

        process_fasta_file(input_path, output_path, mutation_rate)
        print()

    print("=" * 60)
    print("Done! Check the 'worse' directory for results.")
    print("=" * 60)


if __name__ == '__main__':
    main()
