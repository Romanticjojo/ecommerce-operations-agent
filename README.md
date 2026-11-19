# Commerce Lens · 电商运营分析工作台

用自然语言分析电商订单、商品成交额和配送差评。工作台在本机运行，图表中的每个业务指标都能查看数据快照、筛选条件与执行 SQL。中文界面支持中英文提问，默认随附可重复生成的合成数据。

## 拉取并启动

安装 Docker 和 Docker Compose 后运行：

```sh
git clone https://github.com/Romanticjojo/ecommerce-operations-agent.git
cd ecommerce-operations-agent
docker compose up --build -d --wait
```

打开 **[http://127.0.0.1:8731](http://127.0.0.1:8731)**。首次启动会创建演示数据库。本地记录保存在 Docker 卷中。使用 `docker compose down` 停止服务。

也可以在 macOS / Linux 上用 Python **3.11** 和 Node.js **22** 启动：

```sh
./scripts/start.sh
```

脚本建立虚拟环境、安装锁定版本、构建前端、初始化样本并启动服务。命令行需要找到 `python3.11` 和 `npm`。可用 `PYTHON_BIN=/path/to/python3.11 PORT=8732 ./scripts/start.sh` 自定义解释器或端口。在本机已有项目的情况下，直接进入项目目录执行脚本即可。

## 第一次分析

在「分析工作台」选择示例问题，或输入 `Show the top 10 product categories by item revenue in 2018.`。比较表格与柱状图，展开证据后可复制 SQL。在「差评调查」中选择日期范围，比较按精确时间和自然日计算的配送延迟。每一次调查都会显示有效样本数、差评率、百分点差、95% 区间与检验结果。

离线模式识别有限的示例问题，支持的输入见应用示例和 [Agent 说明](docs/operator-guide.md)。要处理更多措辞，可配置兼容 Chat Completions 的模型服务。

## 配置自己的模型

```sh
cp .env.example .env
```

编辑本地 `.env`，填入 `LLM_BASE_URL`（例如兼容服务的 `https://服务地址/v1`）、`LLM_MODEL` 和服务所需的 `LLM_API_KEY`。重新运行本地脚本，或执行 `docker compose up -d --force-recreate`。打开工作台检查模型状态。容器内连接宿主机模型时，基础地址应能从容器访问。提供方收到问题、业务指标与分析结构。快照、明细和查询历史保存在本地。

完整模式将模型返回的结构化计划编译为受限 SQL。基线实验直接向同一模型请求 SQL。两条路径均使用 SQLGlot 检查、受限视图、只读 DuckDB 和独立执行进程。服务面向本机单用户，默认只绑定回环地址。

## 使用完整 Olist 数据

从 [Olist 数据页](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) 下载并解压，保持原 CSV 名称。需要订单、商品行、支付、评价、客户、商品及商家七张表，品类翻译表可选。原始数据采用 **CC BY-NC-SA 4.0**，由使用者自行取得。项目源码和自制演示数据使用 MIT 许可证。

原生运行环境下导入：

```sh
.venv/bin/python -m commerce.cli import /path/to/unzipped-olist
```

使用 Docker 的同一数据卷导入：

```sh
docker compose run --rm -v "/path/to/unzipped-olist:/input:ro" workbench python -m commerce.cli import /input
```

刷新页面即可看到新快照。导入先构建完整候选数据库，再原子替换。导入失败时原快照可继续使用。运行 `python -m commerce.cli demo` 会将当前快照切换回合成数据。查询历史保留各自的快照标识。原生模式默认工作目录为 `runtime/`，可通过 `LENS_HOME` 指向其他本地目录。

## 测试与评估

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m commerce.cli evaluate --mode reference
.venv/bin/python -m commerce.cli evaluate --mode demo --output runtime/demo-report
# 配置模型后，此命令实际调用提供方，产生相应费用
.venv/bin/python -m commerce.cli evaluate --mode model --output runtime/model-report
```

评估页显示最近一次报告。55 题包含 50 道可回答问题、5 道拒答或澄清题。reference 运行原始表参考 SQL，demo 测试离线样例覆盖范围，model 才会调用模型进行 direct/full 对照。题库目前待人工复核。可用 `--limit 3` 做小规模联调。模型 token 价格未配置时费用显示为空。

## 工程导航

| 内容 | 入口 |
|---|---|
| 实测结果、限制与发布检查 | [验收记录](docs/verification.md) |
| 操作、数据口径和故障排查 | [使用指南](docs/operator-guide.md) |
| 四页英文课程技术更新 | [PDF](docs/course/project-update.pdf) · [可编辑 Markdown](docs/course/project-update.md) |
| 数据字典 | [原始表与五个分析视图](docs/data-dictionary.md) |
| 产品范围和需求 | [PRD](docs/PRD.md) |
| 系统组成和 UML | [架构图](docs/architecture.md) |
| 工作包与验收用例 | [生命周期](docs/project-status.md) · [验收计划](docs/acceptance.md) |
| 界面颜色、排版和交互 | [设计规范](DESIGN.md) |
| 原始要求与工程决定 | [来源与取舍](docs/source-review.md) |
| 模型评估题库 | [55 道问题与独立参考 SQL](evaluation/questions.json) |

设计参考 [DB-GPT](https://github.com/eosphoros-ai/DB-GPT) 的工作流与工具契约，以及 [DesignMD Apple](https://designmd.me/discover/apple) 的视觉规范。Commerce Lens 独立实现并使用 [MIT 许可证](LICENSE)。
