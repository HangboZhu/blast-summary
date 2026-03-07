#!/bin/bash
# 批量处理 demo_data 目录下的所有 BLAST 数据
# 自动匹配同 Job-ID 的 _5.txt (BLAST结果) 和 _18.txt (物种信息文件)

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 统计变量
total=0
success=0
no_hits=0
failed=0

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="$PROJECT_ROOT/output/batch_reports"

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

echo "======================================"
echo "BLAST 结果批量处理脚本"
echo "======================================"
echo ""

# 遍历所有类别和 BLAST 类型
for category in good worse non-results; do
    for blast_type in blastn blastp blastx tblastn tblastx; do
        category_dir="$PROJECT_ROOT/demo_data/$category/$blast_type"

        if [ ! -d "$category_dir" ]; then
            continue
        fi

        echo -e "${YELLOW}Processing: $category/$blast_type${NC}"

        # 遍历所有 Job 目录
        for job_dir in "$category_dir"/*/; do
            if [ ! -d "$job_dir" ]; then
                continue
            fi

            job_id=$(basename "$job_dir")
            xml_file="${job_dir}${job_id}_5.txt"
            species_file="${job_dir}${job_id}_18.txt"

            if [ ! -f "$xml_file" ]; then
                echo -e "  ${RED}✗${NC} $job_id: BLAST文件不存在"
                ((failed++))
                ((total++))
                continue
            fi

            ((total++))

            # 构建命令
            if [ -f "$species_file" ]; then
                cmd="blast-summary -i \"$xml_file\" -s \"$species_file\" --no-ai -o \"$OUTPUT_DIR/${job_id}_summary.md\""
            else
                cmd="blast-summary -i \"$xml_file\" --no-ai -o \"$OUTPUT_DIR/${job_id}_summary.md\""
            fi

            # 执行命令并捕获输出
            output=$(eval "$cmd" 2>&1)
            exit_code=$?

            if [ $exit_code -eq 0 ]; then
                if echo "$output" | grep -q "No hits found"; then
                    echo -e "  ${YELLOW}○${NC} $job_id: 无命中结果"
                    ((no_hits++))
                else
                    echo -e "  ${GREEN}✓${NC} $job_id: 成功"
                    ((success++))
                fi
            else
                echo -e "  ${RED}✗${NC} $job_id: 失败"
                echo "    错误: $output"
                ((failed++))
            fi
        done

        echo ""
    done
done

# 打印统计
echo "======================================"
echo "统计汇总"
echo "======================================"
echo -e "总处理数: $total"
echo -e "  ${GREEN}成功: $success${NC}"
echo -e "  ${YELLOW}无命中: $no_hits${NC}"
echo -e "  ${RED}失败: $failed${NC}"
echo ""
echo "报告保存至: $OUTPUT_DIR"
