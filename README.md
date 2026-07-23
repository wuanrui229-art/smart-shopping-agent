# Smart Shopping AI：自主决策型购物助手

运行环境要求：Python 3.9 或更高版本。

## 在线部署

**Vercel 公开 Demo（推荐）：** [https://smart-shopping-agent-wuanrui.vercel.app](https://smart-shopping-agent-wuanrui.vercel.app)

**Render 备用 Demo：** [https://smart-shopping-agent-wuanrui229-art.onrender.com](https://smart-shopping-agent-wuanrui229-art.onrender.com)

Vercel 版本把原版前端、FastAPI 后端和 Python 推荐算法部署在同一个域名下，并支持实时流式响应。Vercel Functions 的本地磁盘不是永久数据库，因此课程演示中的会话历史和偏好以浏览器本地状态为主；每次推荐请求会携带当前偏好，确保 Serverless 实例切换后个性化排序仍然一致。课程版不保存敏感或支付数据。

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2Fwuanrui229-art%2Fsmart-shopping-agent)

点击上方按钮可把完整的前端、FastAPI 后端和推荐算法部署为公开 Render Web Service。仓库已提供 `render.yaml`，部署时会自动安装依赖、启动服务并检查 `/api/health`。

Render 免费实例适合作业和论文备用演示：闲置一段时间后会休眠，首次访问可能需要等待约一分钟。未配置 `OPENAI_API_KEY` 时系统自动使用离线规则算法，主要演示流程仍可完整运行。

## 一、系统包含什么

- **前端**：原版 `Smart Shopping AI` 白底橙色界面，实现对话、六类快捷入口、会话历史、偏好设置、Top 3 深度分析、横向比较和风险提示；请求过程中会实时展示后端处理阶段与本次请求编号。
- **后端**：FastAPI REST API，负责原版推荐接口、实时 NDJSON 流、会话、消息、偏好、SQLite 持久化、算法编排和加购授权记录。
- **算法**：原版六品类多维推荐与偏好感知排序；另保留可选 OpenAI 需求解析、评论可信度分析和可解释加权决策管线。

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

首页提供六个原版快捷入口：`Kids Backpack`、`Headphones`、`Running Shoes`、`Tablet`、`Keyboard` 和 `Smart Watch`。也可以依次输入：

1. `Show me Kids Backpack`
2. `Recommend noise canceling Headphones`
3. `I need Running Shoes for daily training`

发送请求后，页面会通过 `POST /api/original/chat/stream` 实时显示：FastAPI 接收请求 → 读取用户偏好 → 识别商品品类 → 加载评论统计 → 四维评分排序 → 返回完整结果。旧的 `POST /api/original/chat` JSON 接口仍然保留，在不支持流式响应时自动降级使用。

建议展示：首页原版视觉 → 实时后端处理链路 → 四维评分 → Top 3 → 评论情感 → 横向对比 → 修改价格敏感度 → 相同需求重新排序 → `/docs` 接口文档。

完整计时讲稿见 [`docs/六分钟作业展示讲稿.md`](docs/六分钟作业展示讲稿.md)。

## 五、测试

```bash
.venv/bin/python -m pytest -q
```

测试覆盖六品类原版推荐、品类识别、需求解析、评论刷评风险、加权排序、普通/实时流式 API、偏好保存和加购授权。

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
