# 经济学科普短片 · 机会成本（Opportunity Cost）

**主题**：小明只有 ¥10，冰淇淋和「玩游戏 1 小时」都要 ¥10——选了冰淇淋，被放弃的那一小时游戏就是它的**机会成本**（放弃的选项中价值最高的那个，不只是钱，也包括时间与机会）。

- 场景：`demos/econ_opportunity_cost.yaml`（36 秒，320×180 像素 ×3 放大，12fps）
- 成片：`demos/output/econ_opportunity_cost.mp4`
- 关键帧：`demos/frames/econ_opportunity_cost_t*.png`

剧情节拍：标题卡 → 小明带 ¥10 走进集市 → 左看冰淇淋 / 右看游戏厅（思考气泡）→ 钱只够一个 → 付 ¥10 换甜筒（钱包 ¥10→¥0）→ 小红在玩游戏，游戏价签被划掉、闪出「机会成本」→ 定义卡 → 结尾卡「我放弃了什么？」

## 重新渲染

```bash
cd /workspace/animasis
.venv/bin/python -m animasis render demos/econ_opportunity_cost.yaml -o demos/output/econ_opportunity_cost.mp4
# 或者连同其它 demo 一起：
.venv/bin/python -m animasis.demos
```

文字/道具由场景 YAML 的 `overlays:` 层绘制（`animasis/overlay.py`）：`card`（标题卡）、`caption`（字幕条，`reveal` 打字机效果）、`tag`（价签，`strike` 划掉、`blink` 闪烁）、`bubble`（跟随角色的思考气泡，`cross` 打叉）、`hud`（钱包）、`stall`（摊位，柜台自动画在角色前）、`cabinet`（街机）、`text`、`icon`。中文字体默认使用系统 Noto Sans CJK（无抗锯齿，保持像素风），可用环境变量 `ANIMASIS_FONT` 指定其它字体。
