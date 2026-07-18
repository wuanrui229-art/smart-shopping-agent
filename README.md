# 智选：自主决策型 AI 购物系统

这是从原购物助手各周代码与 PRD 中重新整合出的课程作业版本。系统明确分为前端、后端和算法三层，并且既能接入真实大语言模型，也能在没有 API 密钥时完整演示。

运行环境要求：Python 3.9 或更高版本。

## 在线部署

**公开 Demo：** [https://smart-shopping-agent-wuanrui229-art.onrender.com](https://smart-shopping-agent-wuanrui229-art.onrender.com)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2Fwuanrui229-art%2Fsmart-shopping-agent)

点击上方按钮可把完整的前端、FastAPI 后端和推荐算法部署为公开 Render Web Service。仓库已提供 `render.yaml`，部署时会自动安装依赖、启动服务并检查 `/api/health`。

免费实例适合作业和论文演示：闲置一段时间后会休眠，首次访问可能需要等待约一分钟。演示数据使用临时 SQLite 文件，服务休眠、重启或重新部署后，历史会话和偏好可能被清空。未配置 `OPENAI_API_KEY` 时系统自动使用离线规则算法，主要演示流程仍可完整运行。

## 一、系统包含什么

- **前端**：原生 HTML/CSS/JavaScript，实现聊天、历史会话、偏好设置、需求解析展示、Top 3 推荐、评分审计、横向对比和授权式演示加购。
- **后端**：FastAPI REST API，负责会话、消息、偏好、SQLite 持久化、算法编排和加购授权记录。
- **算法**：可选 OpenAI Responses API 需求解析；评论可信度分析；多条件匹配；加权决策排序；明确输出 1 个主推和 2 个备选。

核心评分公式：

```text
综合分 = 评论可信度 × 40% + 需求匹配度 × 30% + 价格竞争力 × 20% + 平台评分 × 10%
```

## 二、最快运行方式

### macOS / Linux

```bash
chmod +x start.sh
./start.sh
```

### Windows

双击 `start.bat`，或在命令行运行：

```bat
start.bat
```

启动成功后打开：<http://127.0.0.1:8000>

接口文档：<http://127.0.0.1:8000/docs>

## 三、启用真实大语言模型（可选）

1. 复制 `.env.example` 为 `.env`。
2. 填写 `OPENAI_API_KEY`。
3. 重新启动系统。

默认模型按原 PRD 的技术路线设置为 `gpt-5.4-mini`。系统通过 Responses API 进行结构化需求解析；若密钥未配置、网络不可用或调用失败，会自动切换到规则解析，不影响课堂演示。

请勿把包含真实密钥的 `.env` 提交给老师或上传到公开仓库。

## 四、课堂演示建议

依次输入下面三句话，可以覆盖主要功能：

1. `推荐一款 500 元以内、适合通勤的防水轻量双肩包`
2. `预算 700 元，想买主动降噪、长续航的蓝牙耳机`
3. `500 元左右的日常慢跑鞋，要缓震、透气、耐磨`

建议展示：需求结构化 → 四步决策链路 → 评论可信度 → 评分明细 → Top 3 → 横向对比 → 授权式演示加购 → 历史会话 → 偏好记忆。

## 五、测试

```bash
.venv/bin/python -m pytest -q
```

测试覆盖需求解析、澄清机制、评论刷评风险、加权排序、API、偏好保存和加购授权。

## 六、项目结构

```text
smart-shopping-agent/
├── frontend/              # 前端界面
├── backend/               # FastAPI 与 SQLite
├── algorithm/             # LLM、评论分析、推荐算法
├── tests/                 # 自动化测试
├── docs/                  # 作业说明与原始材料
├── run.py                 # 服务入口
├── start.sh / start.bat   # 一键启动
└── requirements.txt
```

更多说明见 `docs/系统设计与答辩说明.md` 和 `docs/原项目整合说明.md`。
