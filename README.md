# Smart Shopping AI：自主决策型购物助手

这是从原购物助手各周代码与 PRD 中重新整合出的课程作业版本。前端恢复自 Week 7 原版成品的白底橙色界面，并连接 FastAPI 后端和服务端推荐算法，不再是仅靠浏览器静态数据运行的页面。

运行环境要求：Python 3.9 或更高版本。

## 在线部署

**公开 Demo：** [https://smart-shopping-agent-wuanrui229-art.onrender.com](https://smart-shopping-agent-wuanrui229-art.onrender.com)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2Fwuanrui229-art%2Fsmart-shopping-agent)

点击上方按钮可把完整的前端、FastAPI 后端和推荐算法部署为公开 Render Web Service。仓库已提供 `render.yaml`，部署时会自动安装依赖、启动服务并检查 `/api/health`。

免费实例适合作业和论文演示：闲置一段时间后会休眠，首次访问可能需要等待约一分钟。演示数据使用临时 SQLite 文件，服务休眠、重启或重新部署后，历史会话和偏好可能被清空。未配置 `OPENAI_API_KEY` 时系统自动使用离线规则算法，主要演示流程仍可完整运行。

## 一、系统包含什么

- **前端**：原版 `Smart Shopping AI` 白底橙色界面，实现对话、六类快捷入口、会话历史、偏好设置、Top 3 深度分析、横向比较和风险提示。
- **后端**：FastAPI REST API，负责原版推荐接口、会话、消息、偏好、SQLite 持久化、算法编排和加购授权记录。
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

建议展示：首页原版视觉 → 服务端品类识别 → 四维评分 → Top 3 → 评论情感 → 横向对比 → 个性化分析 → 风险提示 → 历史会话 → 偏好记忆。

## 五、测试

```bash
.venv/bin/python -m pytest -q
```

测试覆盖六品类原版推荐、品类识别、需求解析、评论刷评风险、加权排序、API、偏好保存和加购授权。

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
