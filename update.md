# 任务：BLAST 结果分析与物种信息融合 (全类别处理与命令行参数化)

## 1. 任务背景与目标
你需要编写或更新 `main.py`，用于处理 BLAST 生产环境数据。数据分布在 `demo_data/` 目录下的三个类别中：`good`、`worse` 和 `non-results`。
核心目标是：通过解析 XML 格式的 BLAST 结果提取 `<Hit_accession>`，并将对应的物种信息融合到已有分析中。如果没有遇到这个hit记录，就要打印“No hits found, skipping analysis”这样的异常结果处理机制～

## 2. 命令行参数要求 (Argparse)
必须使用 Python 的 `argparse` 模块，使 `main.py` 能够接收单次任务的具体文件路径：
* `-i` 或 `--input_xml`：传入 XML 格式的 BLAST 结果文件（例如 `_5.txt`，请将此参数接收的文件作为 XML 解析的绝对目标）。
* `-s` 或 `--species_file`：传入包含物种信息的对应文件（同一个 Job-ID 下的另一个配套文件， `_18.txt`）。

## 3. 核心处理逻辑与关联规则
1. **XML 解析与有效性拦截（兼容 non-results 和 worse 的关键）**：
   * 使用 `xml.etree.ElementTree` 或类似库读取 `-i` 传入的文件。
   * 检查是否包含实质性的 `<Hit>` 标签。
   * **跳过规则**：如果该 XML 中没有任何 `<Hit>` 记录（在 `non-results` 目录或部分 `worse` 数据中极为常见），**脚本应打印 "No hits found, skipping analysis" 并以状态码 0 正常退出**，切勿抛出异常或继续执行后续分析。
2. **数据关联映射**：
   * 若存在比对结果，从 XML 结构中提取所有的 `<Hit_accession>`。
   * 读取 `-s` 传入的物种信息文件，探查其文本格式（可能是制表符分隔或简单键值对），并提取对应的物种注释 (Species)。
3. **融合与报告输出**：
   * 将 `<Hit_accession>` 作为 Key，与物种信息进行匹配映射。
   * 在已有分析结果的基础上，追加物种维度信息，将物种信息融入到现在已有的五个模块的分析中,并保存更新后的报告。

## 4. 执行要求
* 编写 `main.py` 时，请确保代码对 XML 解析异常、文件为空或标签缺失等边界情况具备高健壮性。
* 完成 `main.py` 后，请你额外提供一个简单的 Shell 命令示例或 Python 包装脚本，展示如何遍历 `demo_data/{good,worse,non-results}/*/*` 目录，将同属一个 Job-ID 的两个文件（如 `*_18.txt` 和 `*_5.txt`）成对提取，并动态传给 `main.py` 的 `-i` 和 `-s` 参数进行批量自动化测试。