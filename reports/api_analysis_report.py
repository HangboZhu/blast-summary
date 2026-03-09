#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API性能对比分析报告生成脚本
比较 big-deepseek 和 baidu-deepseek-v3.2 两个API的性能差异
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'STHeiti']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
df = pd.read_csv('big_vs_baidu.csv')

# 分组数据
big_data = df[df['Model'] == 'big-deepseek']
baidu_data = df[df['Model'] == 'baidu-deepseek-v3.2']

# 定义要分析的指标
metrics = {
    'Total_Time(s)': '总耗时(秒)',
    'First_Token_Latency(s)': '首Token延迟(秒)',
    'Generation_Time(s)': '生成耗时(秒)',
    'Output_Chars': '输出字符数',
    'Est_Tokens': '估计Token数',
    'Output_Speed(chars/s)': '输出速度(字符/秒)',
    'Est_Token_Speed(tokens/s)': 'Token速度(个/秒)'
}

# 计算统计指标
def calc_stats(series):
    """计算统计指标"""
    return {
        '均值': series.mean(),
        '标准差': series.std(),
        '最小值': series.min(),
        '最大值': series.max(),
        '中位数': series.median()
    }

# 打印统计结果
print("=" * 80)
print("API性能对比分析报告")
print("=" * 80)
print("\n1. 基础统计数据\n")

stats_results = {}
for metric_eng, metric_cn in metrics.items():
    stats_results[metric_eng] = {
        'big-deepseek': calc_stats(big_data[metric_eng]),
        'baidu-deepseek-v3.2': calc_stats(baidu_data[metric_eng])
    }
    print(f"\n【{metric_cn}】")
    print("-" * 60)
    big_stats = stats_results[metric_eng]['big-deepseek']
    baidu_stats = stats_results[metric_eng]['baidu-deepseek-v3.2']
    print(f"{'指标':<10} {'big-deepseek':>15} {'baidu-deepseek-v3.2':>20}")
    for stat_name in ['均值', '标准差', '最小值', '最大值', '中位数']:
        print(f"{stat_name:<10} {big_stats[stat_name]:>15.2f} {baidu_stats[stat_name]:>20.2f}")

# 计算差异百分比
print("\n" + "=" * 80)
print("2. 性能差异分析")
print("=" * 80)

diff_analysis = []
for metric_eng, metric_cn in metrics.items():
    big_mean = stats_results[metric_eng]['big-deepseek']['均值']
    baidu_mean = stats_results[metric_eng]['baidu-deepseek-v3.2']['均值']
    # 计算百度相对于Big的提升/下降百分比
    diff_pct = ((baidu_mean - big_mean) / big_mean) * 100
    diff_analysis.append({
        '指标': metric_cn,
        'big-deepseek均值': big_mean,
        'baidu-deepseek均值': baidu_mean,
        '差异(%)': diff_pct
    })

diff_df = pd.DataFrame(diff_analysis)
print("\n" + diff_df.to_string(index=False))

# 创建可视化图表
fig = plt.figure(figsize=(18, 14))
fig.suptitle('API性能对比分析报告\nbig-deepseek vs baidu-deepseek-v3.2', fontsize=16, fontweight='bold')

colors = {'big-deepseek': '#2E86AB', 'baidu-deepseek-v3.2': '#E94F37'}

# 1. 总耗时对比
ax = plt.subplot(3, 3, 1)
x = np.arange(2)
means = [big_data['Total_Time(s)'].mean(), baidu_data['Total_Time(s)'].mean()]
stds = [big_data['Total_Time(s)'].std(), baidu_data['Total_Time(s)'].std()]
bars = ax.bar(['big-deepseek', 'baidu-deepseek-v3.2'], means, yerr=stds,
              color=[colors['big-deepseek'], colors['baidu-deepseek-v3.2']],
              capsize=5, alpha=0.8)
ax.set_ylabel('秒 (s)', fontsize=11)
ax.set_title('总耗时对比', fontsize=12, fontweight='bold')
for bar, mean in zip(bars, means):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + stds[0]*0.3,
            f'{mean:.1f}s', ha='center', va='bottom', fontsize=10)

# 2. 首Token延迟对比
ax = plt.subplot(3, 3, 2)
means = [big_data['First_Token_Latency(s)'].mean(), baidu_data['First_Token_Latency(s)'].mean()]
stds = [big_data['First_Token_Latency(s)'].std(), baidu_data['First_Token_Latency(s)'].std()]
bars = ax.bar(['big-deepseek', 'baidu-deepseek-v3.2'], means, yerr=stds,
              color=[colors['big-deepseek'], colors['baidu-deepseek-v3.2']],
              capsize=5, alpha=0.8)
ax.set_ylabel('秒 (s)', fontsize=11)
ax.set_title('首Token延迟对比', fontsize=12, fontweight='bold')
for bar, mean in zip(bars, means):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + stds[0]*0.3,
            f'{mean:.2f}s', ha='center', va='bottom', fontsize=10)

# 3. 生成耗时对比
ax = plt.subplot(3, 3, 3)
means = [big_data['Generation_Time(s)'].mean(), baidu_data['Generation_Time(s)'].mean()]
stds = [big_data['Generation_Time(s)'].std(), baidu_data['Generation_Time(s)'].std()]
bars = ax.bar(['big-deepseek', 'baidu-deepseek-v3.2'], means, yerr=stds,
              color=[colors['big-deepseek'], colors['baidu-deepseek-v3.2']],
              capsize=5, alpha=0.8)
ax.set_ylabel('秒 (s)', fontsize=11)
ax.set_title('生成耗时对比', fontsize=12, fontweight='bold')
for bar, mean in zip(bars, means):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + stds[0]*0.3,
            f'{mean:.1f}s', ha='center', va='bottom', fontsize=10)

# 4. 输出字符数对比
ax = plt.subplot(3, 3, 4)
means = [big_data['Output_Chars'].mean(), baidu_data['Output_Chars'].mean()]
stds = [big_data['Output_Chars'].std(), baidu_data['Output_Chars'].std()]
bars = ax.bar(['big-deepseek', 'baidu-deepseek-v3.2'], means, yerr=stds,
              color=[colors['big-deepseek'], colors['baidu-deepseek-v3.2']],
              capsize=5, alpha=0.8)
ax.set_ylabel('字符数', fontsize=11)
ax.set_title('输出字符数对比', fontsize=12, fontweight='bold')
for bar, mean in zip(bars, means):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + stds[0]*0.3,
            f'{mean:.0f}', ha='center', va='bottom', fontsize=10)

# 5. 输出速度对比（字符/秒）- 对数坐标
ax = plt.subplot(3, 3, 5)
means = [big_data['Output_Speed(chars/s)'].mean(), baidu_data['Output_Speed(chars/s)'].mean()]
stds = [big_data['Output_Speed(chars/s)'].std(), baidu_data['Output_Speed(chars/s)'].std()]
bars = ax.bar(['big-deepseek', 'baidu-deepseek-v3.2'], means, yerr=stds,
              color=[colors['big-deepseek'], colors['baidu-deepseek-v3.2']],
              capsize=5, alpha=0.8)
ax.set_ylabel('字符/秒', fontsize=11)
ax.set_title('输出速度对比（字符/秒）', fontsize=12, fontweight='bold')
ax.set_yscale('log')
for bar, mean in zip(bars, means):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.5,
            f'{mean:.1f}', ha='center', va='bottom', fontsize=10)

# 6. Token速度对比
ax = plt.subplot(3, 3, 6)
means = [big_data['Est_Token_Speed(tokens/s)'].mean(), baidu_data['Est_Token_Speed(tokens/s)'].mean()]
stds = [big_data['Est_Token_Speed(tokens/s)'].std(), baidu_data['Est_Token_Speed(tokens/s)'].std()]
bars = ax.bar(['big-deepseek', 'baidu-deepseek-v3.2'], means, yerr=stds,
              color=[colors['big-deepseek'], colors['baidu-deepseek-v3.2']],
              capsize=5, alpha=0.8)
ax.set_ylabel('Token/秒', fontsize=11)
ax.set_title('Token生成速度对比', fontsize=12, fontweight='bold')
ax.set_yscale('log')
for bar, mean in zip(bars, means):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.5,
            f'{mean:.1f}', ha='center', va='bottom', fontsize=10)

# 7. 各指标归一化对比
ax = plt.subplot(3, 3, 7)
# 归一化处理用于对比
norm_metrics = ['Total_Time(s)', 'First_Token_Latency(s)', 'Generation_Time(s)',
                'Output_Speed(chars/s)', 'Est_Token_Speed(tokens/s)']
norm_labels = ['总耗时', '首Token延迟', '生成耗时', '输出速度', 'Token速度']

big_values = [big_data[m].mean() for m in norm_metrics]
baidu_values = [baidu_data[m].mean() for m in norm_metrics]

# 归一化（以big为基准）
big_norm = [1.0] * len(big_values)
baidu_norm = [baidu_values[i] / big_values[i] if big_values[i] != 0 else 0 for i in range(len(baidu_values))]

x = np.arange(len(norm_metrics))
width = 0.35
bars1 = ax.bar(x - width/2, big_norm, width, label='big-deepseek', color=colors['big-deepseek'], alpha=0.8)
bars2 = ax.bar(x + width/2, baidu_norm, width, label='baidu-deepseek-v3.2', color=colors['baidu-deepseek-v3.2'], alpha=0.8)
ax.set_ylabel('归一化值 (big=1.0)', fontsize=11)
ax.set_title('各指标归一化对比\n(big-deepseek=1.0)', fontsize=12, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(norm_labels, fontsize=9)
ax.legend()
ax.axhline(y=1, color='gray', linestyle='--', alpha=0.5)

# 8. 性能差异百分比
ax = plt.subplot(3, 3, 8)
diff_pcts = []
labels = []
for metric_eng, metric_cn in metrics.items():
    big_mean = stats_results[metric_eng]['big-deepseek']['均值']
    baidu_mean = stats_results[metric_eng]['baidu-deepseek-v3.2']['均值']
    diff_pct = ((baidu_mean - big_mean) / big_mean) * 100
    diff_pcts.append(diff_pct)
    labels.append(metric_cn.split('(')[0])

colors_bar = ['#2E86AB' if d > 0 else '#28A745' for d in diff_pcts]
bars = ax.barh(labels, diff_pcts, color=colors_bar, alpha=0.8)
ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
ax.set_xlabel('差异百分比 (%)', fontsize=11)
ax.set_title('百度相对Big的差异\n(正值=百度更高, 负值=百度更低)', fontsize=12, fontweight='bold')
for bar, val in zip(bars, diff_pcts):
    ax.text(bar.get_width() + 2 if val >= 0 else bar.get_width() - 2,
            bar.get_y() + bar.get_height()/2, f'{val:.1f}%',
            ha='left' if val >= 0 else 'right', va='center', fontsize=9)

# 9. 综合评分
ax = plt.subplot(3, 3, 9)
# 计算综合得分 (时间越短越好，速度越快越好)
def calc_score(data):
    """计算综合性能得分"""
    # 时间得分：基准700秒，每少100秒+10分
    time_score = max(0, 100 - (data['Total_Time(s)'].mean() - 35) / 7)
    # 速度得分：基准50字符/秒，每多10字符/秒+5分
    speed_score = data['Output_Speed(chars/s)'].mean() / 2
    # 延迟得分：基准10秒，每少1秒+5分
    latency_score = max(0, 100 - data['First_Token_Latency(s)'].mean() * 5)
    return (time_score + speed_score + latency_score) / 3

big_score = calc_score(big_data)
baidu_score = calc_score(baidu_data)

scores = [big_score, baidu_score]
bars = ax.bar(['big-deepseek', 'baidu-deepseek-v3.2'], scores,
              color=[colors['big-deepseek'], colors['baidu-deepseek-v3.2']],
              alpha=0.8)
ax.set_ylabel('综合得分', fontsize=11)
ax.set_title('综合性能评分\n(越高越好)', fontsize=12, fontweight='bold')
ax.set_ylim(0, max(scores) * 1.2)
for bar, score in zip(bars, scores):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            f'{score:.1f}', ha='center', va='bottom', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('api_performance_report.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("\n" + "=" * 80)
print("图表已保存: api_performance_report.png")
print("=" * 80)

# 统计检验
print("\n3. 统计显著性检验（t检验）\n")
for metric_eng, metric_cn in metrics.items():
    t_stat, p_value = stats.ttest_ind(big_data[metric_eng], baidu_data[metric_eng])
    significance = "显著" if p_value < 0.05 else "不显著"
    print(f"{metric_cn}: t={t_stat:.3f}, p={p_value:.4f} ({significance})")

print("\n" + "=" * 80)
print("分析完成！")
print("=" * 80)
