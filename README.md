# Smart Shopping AI：自主决策型购物助手

这是从原购物助手各周代码与 PRD 中重新整合出的课程作业版本。前端恢复自 Week 7 原版成品的白底橙色界面，并连接 FastAPI 后端和服务端推荐算法，不再是仅靠浏览器静态数据运行的页面。

运行环境要求：Python 3.9 或更高版本。

## 在线部署

**Vercel 公开 Demo（推荐）：** [https://smart-shopping-agent-wuanrui.vercel.app](https://smart-shopping-agent-wuanrui.vercel.app)

**Render 备用 Demo：** [https://smart-shopping-agent-wuanrui229-art.onrender.com](https://smart-shopping-agent-wuanrui229-art.onrender.com)

Vercel 版本把原版前端、FastAPI 后端、大语言模型和 Python 推荐算法部署在同一个域名下，并支持实时流式响应。它采用混合推荐：任何消费品类都可以开放对话和生成 Top 3 建议；六个课程数据集品类还会进入可复现的多维评分算法。Vercel Functions 的本地磁盘不是永久数据库，因此课程演示中的会话历史和偏好以浏览器本地状态为主。课程版不保存敏感或支付数据。

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2Fwuanrui229-art%2Fsmart-shopping-agent)

点击上方按钮可把完整的前端、FastAPI 后端和推荐算法部署为公开 Render Web Service。仓库已提供 `render.yaml`，部署时会自动安装依赖、启动服务并检查 `/api/health`。

Render 免费实例适合作业和论文备用演示：闲置一段时间后会休眠，首次访问可能需要等待约一分钟。未配置大模型密钥时系统自动使用离线规则算法，主要演示流程仍可完整运行。

## 一、系统包含什么

- **前端**：原版 `Smart Shopping AI` 白底橙色界面，实现开放式多轮对话、六个示例快捷入口、会话历史、偏好设置、Top 3 深度分析、横向比较和风险提示；请求过程中只显示简洁的分析状态，结果返回后自动隐藏。
- **后端**：FastAPI REST API，负责原版推荐接口、实时 NDJSON 流、会话、消息、偏好、SQLite 持久化、算法编排和加购授权记录。
- **算法**：大模型负责开放对话、意图判断和任意品类候选生成；六个已有数据品类由偏好感知的确定性算法重新排序；另保留评论可信度分析和可解释加权决策管线。

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

## 三、大语言模型配置

推荐直接使用 Kimi。请在 Vercel 项目的 Environment Variables 中设置以下服务端变量，然后重新部署：

```text
LLM_PROVIDER=kimi
MOONSHOT_API_KEY=你的 Kimi Key
MOONSHOT_MODEL=kimi-k3
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1
```

代码也兼容 `KIMI_API_KEY` 这个变量名，但推荐使用 Kimi 官方文档中的 `MOONSHOT_API_KEY`。如果密钥来自使用其他 API 地址的控制台，请把 `MOONSHOT_BASE_URL` 改为该控制台标明的地址。也可以选择设置 `OPENAI_API_KEY`，或通过 `AI_GATEWAY_API_KEY` / Vercel 部署身份令牌连接 AI Gateway。`LLM_PROVIDER` 可取 `kimi`、`openai` 或 `vercel`。

模型把回答约束为结构化 JSON：区分普通聊天、需要追问和可以推荐三种意图，并携带品类、预算、关注点与三款候选。若模型不可用，六个内置数据品类仍可通过离线算法完整演示；任意品类的开放推荐则需要模型服务在线。

这些变量只由后端读取，不要添加 `NEXT_PUBLIC_` 前缀。请勿把包含真实密钥的 `.env` 提交给老师或上传到公开仓库。

## 四、课堂演示建议

首页的六个按钮只是快捷示例，不是品类限制。建议依次输入：

1. `你好，你能帮我做什么？`，展示开放式聊天。
2. `我想买一支适合黄皮通勤、预算 300 元以内的哑光口红，请推荐三款`，展示任意新品类。
3. `I need Running Shoes for daily training`，展示内置数据和确定性评分。

发送请求后，页面会通过 `POST /api/original/chat/stream` 实时接收。大模型先结合最近对话识别意图；若命中六个内置品类，后端加载课程数据并运行偏好感知评分；其他品类返回明确标记为 AI 生成的建议和估算价格，不冒充实时库存、评论或评分。前端只显示单行的用户友好状态，完成后自动隐藏。

建议展示：首页原版视觉 → 实时分析状态 → 四维评分 → Top 3 → 评论情感 → 横向对比 → 修改价格敏感度 → 相同需求重新排序 → `/docs` 接口文档。

完整计时讲稿见 [`docs/六分钟作业展示讲稿.md`](docs/六分钟作业展示讲稿.md)。

## 五、测试

```bash
.venv/bin/python -m pytest -q
```

测试覆盖任意品类结构化结果、六品类确定性推荐、品类识别、需求解析、评论刷评风险、加权排序、普通/实时流式 API、偏好保存和加购授权。

## 六、项目结构

```text
smart-shopping-agent/
├── frontend/              # 前端界面
├── backend/               # FastAPI 与 SQLite
├── algorithm/             # LLM、评论分析、推荐算法
├── tests/                 # 自动化测试
├── docs/                  # 作业说明与原始材料
├── run.py                 # 服务入口
├── app.py                 # Vercel FastAPI 入口
├── vercel.json            # Vercel Function 配置
├── start.sh / start.bat   # 一键启动
└── requirements.txt
```

更多说明见 `docs/系统设计与答辩说明.md` 和 `docs/原项目整合说明.md`。
