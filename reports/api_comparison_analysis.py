#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Performance Comparison Analysis Script
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Set matplotlib style
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False
plt.style.use('seaborn-v0_8-whitegrid')

# Read data
df = pd.read_csv('big_vs_baidu.csv')

# Define colors
colors = {'big-deepseek': '#E74C3C', 'baidu-deepseek-v3.2': '#27AE60'}

# Create figure with 4 subplots (2x2)
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1. Total Time Comparison (Bar Chart)
ax1 = axes[0, 0]
models = ['big-deepseek', 'baidu-deepseek-v3.2']
means = [df[df['Model'] == m]['Total_Time(s)'].mean() for m in models]
stds = [df[df['Model'] == m]['Total_Time(s)'].std() for m in models]

x = np.arange(len(models))
bars = ax1.bar(x, means, yerr=stds, color=[colors[m] for m in models],
               capsize=8, alpha=0.85, edgecolor='black', linewidth=1.5, width=0.6)

ax1.set_ylabel('Time (seconds)', fontsize=12, fontweight='bold')
ax1.set_title('Total Response Time', fontsize=14, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(['big-deepseek', 'baidu-deepseek-v3.2'], fontsize=11)
ax1.set_ylim(0, max(means) * 1.15)

# Add value labels
for bar, mean, std in zip(bars, means, stds):
    ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + std + 20,
             f'{mean:.1f}s', ha='center', va='bottom', fontsize=12, fontweight='bold')

# 2. Token Speed Comparison (Bar Chart)
ax2 = axes[0, 1]
speed_means = [df[df['Model'] == m]['Est_Token_Speed(tokens/s)'].mean() for m in models]
speed_stds = [df[df['Model'] == m]['Est_Token_Speed(tokens/s)'].std() for m in models]

bars2 = ax2.bar(x, speed_means, yerr=speed_stds, color=[colors[m] for m in models],
                capsize=8, alpha=0.85, edgecolor='black', linewidth=1.5, width=0.6)

ax2.set_ylabel('Speed (tokens/s)', fontsize=12, fontweight='bold')
ax2.set_title('Token Generation Speed', fontsize=14, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(['big-deepseek', 'baidu-deepseek-v3.2'], fontsize=11)

for bar, mean, std in zip(bars2, speed_means, speed_stds):
    ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + std + 1,
             f'{mean:.1f}', ha='center', va='bottom', fontsize=12, fontweight='bold')

# 3. Line Chart - Time by Round
ax3 = axes[1, 0]
for model in models:
    model_data = df[df['Model'] == model]
    ax3.plot(model_data['Test_Round'], model_data['Total_Time(s)'],
             'o-', color=colors[model], linewidth=2.5, markersize=12,
             label=model, markeredgecolor='black', markeredgewidth=1.5)

ax3.set_xlabel('Test Round', fontsize=12, fontweight='bold')
ax3.set_ylabel('Total Time (seconds)', fontsize=12, fontweight='bold')
ax3.set_title('Response Time by Round', fontsize=14, fontweight='bold')
ax3.legend(fontsize=11, loc='upper right')
ax3.set_xticks([1, 2, 3])

# 4. Performance Metrics Summary Table
ax4 = axes[1, 1]
ax4.axis('off')

# Create summary data
summary_data = [
    ['Metric', 'big-deepseek', 'baidu-deepseek-v3.2', 'Difference'],
    ['Total Time (s)', '749.6 ± 30.0', '37.7 ± 4.7', '↓ 95.0%'],
    ['First Token (s)', '4.0 ± 5.6', '18.9 ± 3.1', '↑ 374%'],
    ['Gen Time (s)', '745.6 ± 25.2', '18.8 ± 1.7', '↓ 97.5%'],
    ['Token Speed (t/s)', '1.4 ± 0.1', '56.9 ± 8.3', '↑ 39.7x'],
]

table = ax4.table(cellText=summary_data[1:], colLabels=summary_data[0],
                  loc='center', cellLoc='center',
                  colColours=['#3498DB', '#E74C3C', '#27AE60', '#9B59B6'])
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1.2, 1.8)

# Style header
for (row, col), cell in table.get_celld().items():
    if row == 0:
        cell.set_text_props(fontweight='bold', color='white')
    cell.set_edgecolor('black')

ax4.set_title('Performance Summary', fontsize=14, fontweight='bold', pad=20)

plt.tight_layout(pad=2.0)
plt.savefig('api_performance_comparison.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("Chart saved to: api_performance_comparison.png")
