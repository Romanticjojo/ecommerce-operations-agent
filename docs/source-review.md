# 材料审阅与依据

审阅日期：2026-11-19。证据优先级：用户本次要求 > 原始课程评分标准与教师反馈 > 原始 proposal > AI spec / blueprint 建议。PDF 原件保留在用户附件位置，不复制到公开项目。

## 原始材料

`Project_update_rubric_dsc200_fa26.pdf` 共 2 页：

- Project Update 截止 Monday 11/23；结合课程 fa26，对应 2026-11-23。
- 提交一个 PDF，另附源码 ZIP 或可访问的 GitHub 链接；用户已要求公开仓库。
- spec 最多 4 页，超页需要说明理由；工程文档可以更长，课程提交版应另行压缩。
- 至少 3 条功能需求、3 条非功能需求；更多时明确选出参与评分的条目。
- 至少 3 种 UML 图，每图附含义和选型理由。
- 至少 3 个单元测试、3 个功能测试，均应写输入、步骤、前置条件、预期结果、后置条件。
- 代码 check-in 需要实际进展和测试状态。开发反思要求 1–2 段，由组员本人撰写；不能以 AI 代写内容作为该反思。
- 评分表本身存在分值排版矛盾：Data Models 标 6 分但子项共 8 分；spec 各项合计也与 70 分不一致。工程验收覆盖全部内容，不自行重算教师评分。

`原始项目提案与教师反馈 PDF` 共 3 页：第 1 页为教师反馈，第 2 页为扫描的原始 proposal，第 3 页空白。已视觉检查第 2 页，不能仅靠 PDF 文本抽取判断其缺失。

- 目标用户：电商运营者与小型在线商家；数据来源为 Olist 约 10 万订单、2016–2018 年的多张关联 CSV。
- 原始五项 Done：自然语言问答；统计和可视化；差评原因调查；有证据的建议；结果验证与溯源。
- 老师明确建议聚焦 2–3 项，并回答系统选型、准确性验证、多数据表利用策略。
- 原始 proposal 写明数据使用 CC BY-NC-SA 4.0。代码许可证与数据许可分开处理；不把下载数据一并改为代码许可证，也不默认重新分发数据。
- 公开工程文档省略学生姓名、联系邮箱与成绩截图。分工按角色表达，实际组员分工由团队确认。

## AI 方案中的保留与修订

| 内容 | 决定 | 原因 |
|---|---|---|
| 销售分析 + 差评调查 | 保留 | 回应教师聚焦要求 |
| 单 Agent、有边界的确定性工具 | 保留 | 适合本地部署和验证 |
| DuckDB 原始关系表 + 分析视图 | 保留 | 避免多对多直接拼接 |
| Streamlit 主界面 | 提议改为 React + FastAPI | 用户明确要求设计完成度高的 Apple 风格页面 |
| 55 道 golden questions | 保留为工程目标 | 题目与答案需独立核对，不能标称已由人审核 |
| 90% / 95% 准确率目标 | 保留为待测阈值 | 无真实模型测试不能宣称达到 |
| 所有评价直接做独立样本检验 | 修订 | 同一订单多评价会破坏独立性；增加订单级主分析和评价级描述 |
| 6 周路线图 | 改为阶段验收关卡 | 当前交付节奏由实际工作推进，不能假装经过六周 |
| 自动运营建议 | 限定为有证据的观察与待验证假设 | 无自动经营执行和因果宣称 |

## 参考项目与设计

DB-GPT 官方仓库于本次审阅查询到的 main commit：`decf2726ab7fcc8d5e7e0ea638d38362a7cc220f`，提交时间 2026-11-18 UTC。实际查看 README、AWEL `simple_dag_example.py`、`agent/core/action/base.py`。借鉴有类型的工作流步骤、工具输入输出和结果展示分离；首版不依赖其全套运行时。

- [固定版本 README](https://github.com/eosphoros-ai/DB-GPT/blob/decf2726ab7fcc8d5e7e0ea638d38362a7cc220f/README.md)
- [AWEL 示例](https://github.com/eosphoros-ai/DB-GPT/blob/decf2726ab7fcc8d5e7e0ea638d38362a7cc220f/examples/awel/simple_dag_example.py)
- [Action 契约](https://github.com/eosphoros-ai/DB-GPT/blob/decf2726ab7fcc8d5e7e0ea638d38362a7cc220f/packages/dbgpt-core/src/dbgpt/agent/core/action/base.py)
- [DesignMD Apple](https://designmd.me/discover/apple)：白/浅灰表面、近黑文字、蓝色交互、系统字体、留白和细分隔线；项目自行编写设计规范，不复制 Apple 品牌素材。
- [Olist 官方数据页](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)：本次网页工具未返回可读正文，数据许可记录目前依据原始 proposal；实际导入时再次核对数据页面/下载包说明。

## 实施复核

真实 Olist 已从官方 Kaggle 发布地址取得，发布方元数据显示许可证为 CC BY-NC-SA 4.0。导入了七张业务表和品类翻译表。系统、数据和模型的最终验证情况见 [验收记录](verification.md)。
