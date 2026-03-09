#!/bin/bash
# 批量处理 BLAST 数据（带 AI 分析）
# 输出报告结构遵循 demo_data 目录结构：
# output/{category}/{blast_type}/{job_id}/{job_id}_summary.md
#
# 用法:
#   ./batch_process_ai.sh           # 普通模式
#   ./batch_process_ai.sh --stream  # 流式模式（实时写入文件）

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 统计变量
total=0
success=0
no_hits=0
failed=0

# 是否使用流式模式
STREAM_MODE=""

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --stream)
            STREAM_MODE="--stream"
            shift
            ;;
        *)
            echo "未知参数: $1"
            echo "用法: $0 [--stream]"
            exit 1
            ;;
    esac
done

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="$PROJECT_ROOT/output"

# 检查 AI 配置
check_ai_config() {
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        echo -e "${YELLOW}警告: 未找到 .env 配置文件${NC}"
        echo "请确保已配置 AI API 密钥（OPENAI_API_KEY 或 QIANFAN_API_KEY）"
        echo ""
    fi
}

echo "======================================"
echo "BLAST 结果批量处理脚本 (带 AI 分析)"
if [ -n "$STREAM_MODE" ]; then
    echo "模式: 流式输出"
fi
echo "======================================"
echo ""

# 检查 AI 配置
check_ai_config

# 遍历所有类别和 BLAST 类型
for category in good worse non-results; do
    for blast_type in blastn blastp blastx tblastn tblastx; do
        category_dir="$PROJECT_ROOT/demo_data/$category/$blast_type"

        if [ ! -d "$category_dir" ]; then
            continue
        fi

        echo -e "${BLUE}处理: $category/$blast_type${NC}"

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

            # 构建输出目录结构（遵循 demo_data 结构）
            output_subdir="$OUTPUT_DIR/$category/$blast_type/$job_id"
            mkdir -p "$output_subdir"
            output_file="$output_subdir/${job_id}_summary.md"

            # 构建命令（带 AI 分析）
            if [ -f "$species_file" ]; then
                cmd="blast-summary -i \"$xml_file\" -s \"$species_file\" -o \"$output_file\" $STREAM_MODE"
            else
                cmd="blast-summary -i \"$xml_file\" -o \"$output_file\" $STREAM_MODE"
            fi

            # 执行命令并捕获输出
            output=$(eval "$cmd" 2>&1)
            exit_code=$?

            if [ $exit_code -eq 0 ]; then
                if echo "$output" | grep -q "No hits found"; then
                    echo -e "  ${YELLOW}○${NC} $job_id: 无命中结果"
                    ((no_hits++))
                else
                    echo -e "  ${GREEN}✓${NC} $job_id: 成功 (AI分析完成)"
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
echo ""
echo "目录结构:"
echo "  output/"
echo "  ├── good/"
echo "  │   ├── blastn/{job_id}/{job_id}_summary.md"
echo "  │   ├── blastp/{job_id}/{job_id}_summary.md"
echo "  │   └── ..."
echo "  ├── worse/"
echo "  └── non-results/"
