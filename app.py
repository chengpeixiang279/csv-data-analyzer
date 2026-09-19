# -*- coding: utf-8 -*-
"""
CSV 数据分析小工具
上传任意 CSV 文件，自动生成数据体检报告：概览、质量检查、数值分析、分类分析。
"""

import io

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns

# ---------- 页面与字体配置 ----------
st.set_page_config(page_title="CSV 数据分析工具", layout="wide")

matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'PingFang SC', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
sns.set_theme(style='whitegrid')

MAX_UNIQUE_FOR_BAR = 50  # 分类字段唯一值超过该数量时，不画柱状图（可能是 ID 类字段）


# ---------- 数据读取 ----------
@st.cache_data
def load_csv(file):
    """读取 CSV，自动尝试多种编码。"""
    raw = file.getvalue()
    for enc in ('utf-8', 'gbk', 'latin-1'):
        try:
            return pd.read_csv(io.BytesIO(raw), encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError('无法识别的文件编码')


def generate_sample(n=300):
    """生成示例数据（含缺失值与重复行，便于演示质量检查）。"""
    rng = np.random.default_rng(42)
    df = pd.DataFrame({
        '订单号': [f'ORD{i:04d}' for i in range(n)],
        '城市': rng.choice(['北京', '上海', '广州', '深圳', '杭州'], n),
        '品类': rng.choice(['食品', '数码', '服饰', '家居', '美妆'], n),
        '单价': np.round(rng.uniform(20, 500, n), 2),
        '数量': rng.integers(1, 10, n),
        '销售额': 0.0,
    })
    df['销售额'] = (df['单价'] * df['数量']).round(2)
    # 注入少量缺失值
    for col, idx in [('城市', 5), ('单价', 30), ('品类', 80), ('数量', 120)]:
        df.loc[idx, col] = np.nan
    # 注入两行重复
    df = pd.concat([df, df.iloc[[0, 7]]], ignore_index=True)
    return df


# ---------- 主界面 ----------
st.title('CSV 数据分析工具')
st.caption('上传任意 CSV 文件，自动生成数据体检报告：概览 · 质量 · 数值 · 分类')

with st.sidebar:
    st.header('数据输入')
    uploaded = st.file_uploader('上传 CSV 文件', type=['csv'])
    if st.button('加载示例数据', use_container_width=True):
        st.session_state['sample'] = True
        st.session_state['uploaded'] = None
        st.rerun()

    st.divider()
    max_rows = st.slider('最大分析行数（超限自动抽样）', 1000, 50000, 20000, step=1000)

# 数据来源判定
df = None
if uploaded is not None:
    try:
        df = load_csv(uploaded)
    except Exception as e:
        st.error(f'文件读取失败：{e}')
elif st.session_state.get('sample'):
    df = generate_sample()
    st.info('当前展示的是**示例数据**，你可以在左侧上传自己的 CSV 文件。')

if df is None:
    st.info('请在左侧上传 CSV 文件，或点击「加载示例数据」体验。')
    st.stop()

# 抽样控制
if len(df) > max_rows:
    df = df.sample(max_rows, random_state=42)
    st.sidebar.warning(f'数据量较大，已随机抽样 {max_rows} 行用于分析。')

# 列类型划分
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
cat_cols = df.select_dtypes(include=['object', 'str']).columns.tolist()

# ---------- 标签页 ----------
tab_overview, tab_quality, tab_numeric, tab_cat = st.tabs(
    ['数据概览', '数据质量', '数值分析', '分类分析']
)

# ===== 数据概览 =====
with tab_overview:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('行数', f'{len(df):,}')
    c2.metric('列数', len(df.columns))
    c3.metric('数值字段', len(numeric_cols))
    c4.metric('分类字段', len(cat_cols))

    st.subheader('数据预览')
    st.dataframe(df.head(10), use_container_width=True)

    st.subheader('字段类型')
    st.dataframe(df.dtypes.astype(str).rename('类型'), use_container_width=True)

# ===== 数据质量 =====
with tab_quality:
    n_missing = int(df.isnull().sum().sum())
    n_dup = int(df.duplicated().sum())
    c1, c2, c3 = st.columns(3)
    c1.metric('缺失值总数', f'{n_missing:,}')
    c2.metric('重复行数', f'{n_dup:,}')
    c3.metric('缺失值比例', f'{n_missing / max(df.size, 1) * 100:.2f}%')

    if n_missing > 0:
        st.subheader('各字段缺失情况')
        miss = df.isnull().sum()
        miss = miss[miss > 0].sort_values(ascending=False)
        miss_df = pd.DataFrame({
            '缺失数': miss,
            '缺失率(%)': (miss / len(df) * 100).round(2),
        })
        st.dataframe(miss_df, use_container_width=True)

        st.subheader('缺失值分布图')
        fig, ax = plt.subplots(figsize=(12, 3))
        sns.heatmap(df.isnull(), cbar=False, yticklabels=False, cmap='Reds', ax=ax)
        ax.set_title('缺失值热力图（红色为缺失）')
        st.pyplot(fig)
    else:
        st.success('没有缺失值。')

    if n_dup > 0:
        st.subheader('重复行示例')
        st.dataframe(df[df.duplicated(keep=False)].head(10), use_container_width=True)

# ===== 数值分析 =====
with tab_numeric:
    if not numeric_cols:
        st.info('没有数值型字段。')
    else:
        st.subheader('数值字段统计')
        st.dataframe(df[numeric_cols].describe().round(2), use_container_width=True)

        st.subheader('分布查看')
        col = st.selectbox('选择数值字段', numeric_cols, key='num_dist')
        fig, axes = plt.subplots(1, 2, figsize=(13, 4))
        axes[0].hist(df[col].dropna(), bins=30, color='#4C72B0', edgecolor='white')
        axes[0].set_title(f'{col} 分布直方图')
        axes[0].set_ylabel('频数')
        axes[1].boxplot(df[col].dropna(), orientation='horizontal', patch_artist=True)
        axes[1].set_title(f'{col} 箱线图')
        axes[1].set_xlabel(col)
        plt.tight_layout()
        st.pyplot(fig)

        if len(numeric_cols) > 1:
            st.subheader('相关性矩阵')
            if len(numeric_cols) <= 20:
                fig, ax = plt.subplots(figsize=(8, 6))
                sns.heatmap(df[numeric_cols].corr(), annot=True, fmt='.2f',
                            cmap='coolwarm', center=0, ax=ax)
                ax.set_title('数值字段相关系数')
                st.pyplot(fig)
            else:
                st.info(f'数值字段较多（{len(numeric_cols)} 个），暂不展示相关性矩阵。')

# ===== 分类分析 =====
with tab_cat:
    if not cat_cols:
        st.info('没有分类（文本）型字段。')
    else:
        col = st.selectbox('选择分类字段', cat_cols, key='cat_count')
        n_unique = df[col].nunique(dropna=True)
        st.caption(f'唯一值数量：{n_unique}')

        if n_unique <= MAX_UNIQUE_FOR_BAR:
            top_n = st.slider('显示前 N 类', 5, 30, 10, key='cat_topn')
            vc = df[col].value_counts(dropna=False).head(top_n)
            fig, ax = plt.subplots(figsize=(9, max(3, len(vc) * 0.35)))
            ax.barh(vc.index.astype(str)[::-1], vc.values[::-1], color='#55A868')
            ax.set_title(f'{col} 取值分布（前 {top_n}）')
            ax.set_xlabel('频数')
            plt.tight_layout()
            st.pyplot(fig)
            st.dataframe(
                vc.rename('频数').to_frame().assign(占比=lambda d: (d['频数'] / len(df) * 100).round(2)),
                use_container_width=True,
            )
        else:
            st.warning(f'该字段唯一值过多（{n_unique} 个），可能是 ID 类字段，不适合画柱状图。')

st.divider()
st.caption('CSV 数据分析工具 · 基于 Streamlit / pandas / matplotlib / seaborn')
