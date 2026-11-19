# Olist · 15 个真实数据测试用例

[观看 K03 本地单例测试全程（MP4）](media/K03-revenue.mp4) · [录像对应的单次运行记录](media/K03-results.json) · [阅读本次完整报告](verified/REPORT.md) · [逐项输入、预期与实测 JSON](verified/results.json) · [数据来源和文件指纹](verified/manifest.json)

这套验收使用 KaggleHub 下载的 Olist 完整数据，在本机启动真实 HTTP 服务并执行 15 个 pytest 用例。数字对照来自原始 CSV 的独立计算。用例分为导入审计、经营分析、多表金额、配送差评统计、异常输入及证据重放。适合评审课程项目，也可在修改导入或指标逻辑后做回归。

## 复现

从本仓库根目录运行（Python 3.11，macOS / Linux）：

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r evaluation/kaggle_olist/requirements.txt
.venv/bin/python -m pytest -q evaluation/kaggle_olist/cases.py
```

默认下载调用与下方等价。KaggleHub 返回的目录直接传给导入器。第一次运行需联网，SDK 按版本缓存文件。

```python
import kagglehub

path = kagglehub.dataset_download("olistbr/brazilian-ecommerce")
print("Path to dataset files:", path)
```

要复现已发布报告中的 **v2** 而非未来的最新版：

```sh
.venv/bin/python -m pytest -q evaluation/kaggle_olist/cases.py \
  --olist-version 2 --olist-output runtime/kaggle-v2
```

默认报告保存在 `runtime/kaggle-acceptance/`，包括 REPORT.md、results.json 和 manifest.json。可加 `-k k10` 单跑时间戳口径的统计测试。只有显式指定 `cases.py` 才运行这套需要外部数据的用例。pytest 的失败退出码可供 CI 使用。可设置 `KAGGLEHUB_CACHE` 改变数据缓存位置。测试临时数据库由 pytest 管理；每次运行使用新的快照和历史，不需要占用工作台端口或配置模型密钥。

## 文件与核对方式

| 文件 | 用途 |
|---|---|
| cases.py | 15 项测试的操作、输入与判定 |
| oracle.py | 读取原始 CSV，用十进制累加金额，独立选择最新有效评价并计算风险差和区间 |
| conftest.py | 获取数据、构建隔离环境、通过 HTTP 请求运行系统，记录用例结果 |
| reporting.py | 将同一次 pytest 会话生成 Markdown、JSON 与文件清单 |
| verified/ | 本次在 Mac 上执行的归档结果 |

下载包共九个 CSV，系统导入七张核心表和一张品类翻译表。地理位置表只核对文件指纹和记录数。CC BY-NC-SA 4.0 的数据由 [Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) 发布。此包包括测试源码、数据获取方式和聚合结果。真实模型的生成质量属于另一项实验。
