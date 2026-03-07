# 定义需要处理的BLAST类型列表
blast_types=("blastn" "blastp" "blastx" "tblastn")
data_path ="./demo_data"
output_path="./output"
# 循环执行命令，同时打印当前处理的类型
for type in "${blast_types[@]}"; do
  # 打印正在处理的BLAST类型（英文提示）
  echo "Processing ${type} now..."
  
  # 执行blast-summary命令
  blast-summary -i "$data_path/good/${type}/${type}_example.txt" -o "$output_path/good/${type}_good_out_report.md"

  blast-summary -i "$data_path/worse/${type}/${type}_worse_example.txt" -o "$output_path/worse/${type}_worse_out_report.md"

  
  # 打印当前类型处理完成的提示（可选，增强可读性）
  echo "Completed processing for ${type}."
  echo "----------------------------------------"
done

# 全部完成后的总提示
echo "All BLAST types (blastn, blastp, blastx, tblastn) have been processed successfully!"