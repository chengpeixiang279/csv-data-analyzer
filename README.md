# CSV 数据分析工具 CSV Data Analyzer

上传任意 CSV 文件，自动生成一份数据体检报告。基于 Streamlit 的交互式网页应用，零代码、开箱即用。

## 功能

| 模块 | 说明 |
|---|---|
| 数据概览 | 行数、列数、字段类型、前 10 行预览 |
| 数据质量 | 缺失值统计与热力图、重复行检测 |
| 数值分析 | 描述统计、分布直方图 / 箱线图、字段相关性矩阵 |
| 分类分析 | 取值分布条形图（自动跳过 ID 类高基数字段） |

其他细节：

- 自动尝试多种文件编码（utf-8 / gbk / latin-1）
- 大文件自动抽样，避免内存溢出
- 内置「加载示例数据」一键体验
- 中文界面

## 快速开始

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 启动应用：
   ```bash
   streamlit run app.py
   ```
3. 浏览器会自动打开 `http://localhost:8501`，上传 CSV 或点击「加载示例数据」即可体验。

也可以先用 `sample_data/sample.csv` 测试上传功能（该文件含少量缺失值和重复行，便于查看数据质量模块）。

## 部署到云端

本项目可直接免费部署到 [Streamlit Community Cloud](https://share.streamlit.io/)：

1. 用 GitHub 账号登录 Streamlit Community Cloud
2. 点击 "New app"，选择本仓库，主文件填 `app.py`
3. 点击 Deploy，即可获得一个公开链接

## 技术栈

Python · Streamlit · pandas · numpy · matplotlib · seaborn

## 项目结构

```
csv-data-analyzer/
├── app.py                 # 主程序
├── requirements.txt       # 依赖清单
└── sample_data/
    └── sample.csv         # 示例数据
```
