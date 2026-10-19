# 麦当劳智能点餐推荐助手 · McDonald's Smart Order Recommender

> 基于 **WorkBuddy + MCP** 的轻量化本地点餐推荐助手，**仅做推荐，不接入下单链路，不替代门店核单**。
> 通过 5 项结构化信息收集，一次性固定输出三套独立方案：**热量优选（减脂款） · 解馋备选 · 性价比优惠款**。

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)
![MCP Ready](https://img.shields.io/badge/MCP-Ready-purple.svg)
![No Third-Party Deps](https://img.shields.io/badge/Dependencies-Standard%20Library%20Only-green.svg)

[项目简介](#1-项目简介) · [核心创新亮点](#2-核心创新亮点) · [功能清单](#3-功能清单) · [系统三层架构](#4-系统三层架构) · [项目限制 & 免责声明](#5-项目限制--免责声明) · [使用说明](#6-使用说明) · [MCP 对接说明](#7-mcp-对接说明) · [开源许可证](#8-开源许可证mit-license)

---

## 1. 项目简介

**麦当劳智能点餐推荐助手** 是为 WorkBuddy 对话流量身定制的点餐辅助工具。它通过结构化的 **5 项用户信息收集**（用餐时段、忌口配料、热量目标、预算上限、用餐需求），结合本地菜单 / 套餐快照与柔性规则引擎，一次性输出 **热量优选（减脂款） / 解馋备选 / 性价比优惠款** 三套相互独立的方案。

它不试图成为另一个外卖 App，而是把「**推荐**」这件事做得很克制：

- **不接入任何下单或支付链路** —— 没有下单 API、没有二维码、没有支付跳转、没有诱导到店外交易。
- **不假装实时核价** —— 菜单与套餐快照是本地 JSON，所有价格一律标注「参考价」，不保证实时库存与活动状态。
- **不锁死时段** —— 系统全天可用，早 / 午 / 晚餐仅用于微调推荐偏好；用户深夜想吃麦满分，完全可以，只在结果中附带跨时段提示。
- **不粗暴删除菜品** —— 忌蛋黄酱时巨无霸仍然出现，仅做辅料级标注与柔性扣分。

### 1.1 目录结构

```
mcd-order-M-skill/
│
├── README_new.md                  # 本文件（项目说明 · MCP 赛事提交版）
├── SKILL_new.md                   # WorkBuddy 技能定义主文档（agent_created）
├── README.md / SKILL.md           # 历史版本，保留不覆盖
├── workbuddy.md                   # WorkBuddy 对话层集成说明
├── MCP_INTEGRATION.md             # MCP 网关集成协议
│
├── assets/                        # 默认菜单快照
│   └── menu_snapshot.json         # 13 个单品（汉堡 / 小食 / 甜品 / 饮料）
│
├── references/                    # 参考文档
│   └── mcp-input-schema.md        # 完整 MCP 入参 / 出参 Schema
│
├── scripts/                       # 可执行脚本
│   ├── offline_demo.py            # 推荐引擎主程序（CLI + library 双模式）
│   ├── filter_recipe.py           # 柔性忌口筛选模块
│   └── score_combo.py             # 套餐打分模块
│
├── static_data/                   # 静态数据扩展
│   └── seasonal_menu.json         # 季节性单品（春 / 夏 / 秋 / 冬）
│
└── test/                          # 冒烟测试
    └── test_cases.py              # 核心场景覆盖
```

### 1.2 数据流特性

- **单向、无状态**：每次调用相互独立，无跨会话记忆，不落库。
- **本地优先**：仅读 `assets/` 与 `static_data/`，从不访问外网。
- **可审计**：所有错误码与 stderr 信息可在测试套件中复现。
- **断网可运行**：仅依赖 Python 标准库，零第三方依赖。

### 1.3 数据来源说明（离线演示版）

【备注】热门联名套餐、活动信息、积分抵扣数据，正式部署时由MCP官方接口动态拉取、自动更新；过期联名会自动移除。当前离线演示版本仅使用单品快照，用于功能验证。

- 当前 `assets/menu_snapshot.json` 仅含 13 个单品（汉堡 / 小食 / 甜品 / 饮料），**不含 `combos`、活动有效期（`promo_valid_from` / `promo_valid_to`）与积分（`points_redeemable`）字段**，因此离线演示版的套餐权重（60 / 25 / 15）与积分加分不参与实际打分，三套方案均为自由单品组合。
- 上述字段已按 MCP 出参 Schema 预留，对接麦当劳 MCP 官方接口后由服务端下发、自动更新，过期联名自动移除，**引擎侧无需改动即可启用套餐权重与积分排序**。

---

## 2. 核心创新亮点

### 2.1 亮点1：时段感知，但不锁死菜品

- 系统**全天可用**；用餐时段（早餐 / 午餐 / 下午茶 / 晚餐 / 夜宵）仅用于**微调推荐偏好**，不作为硬过滤条件。
- 早 / 午 / 晚餐区分只影响排序权重与品类倾向，**不硬性限制菜品选择**。
- 跨时段单品可正常选择，并在 `meta.cross_slot_notice` 中附带一条精简提示，由用户自行决定是否到店沟通。
- 典型场景：深夜想吃麦满分？推荐引擎不会因为「早餐时段已过」而拒绝，只在匹配说明中提示该单品属非常规时段供应。

| 时段 | 偏好倾向 | 备注 |
|------|----------|------|
| breakfast | 麦满分、早餐板烧、鲜煮咖啡 | 偏好加权，跨时段单品不屏蔽 |
| lunch | 巨无霸、双层牛肉堡、小食 | 偏好加权 |
| afternoon_tea | 派、麦旋风、小食 | 偏好加权 |
| dinner | 主餐汉堡 + 小食 + 饮料 | 偏好加权 |
| late_night | 小食 + 饮料 | 偏好加权，不阻断其他时段单品 |

### 2.2 亮点2：柔性忌口筛选机制

- **所有辅料平等赋值扣分**：命中任一忌口辅料即扣除相同分值，不区分主料 / 辅料等级，避免规则膨胀。
- **不一次性全盘剔除**：含忌口食材的菜品采用**扣分机制**参与排序，而不是直接删除，最大限度保留用户选择空间。
- **汉堡仅剔除第二层配料，保留汉堡本体**：汉堡命中忌口时只标记「可剔除配料：xxx（请点单时备注）」，**绝不会直接删除汉堡选项**。
- 套餐级命中时保留套餐，标记「单品可替换：xxx → 推荐替换为 yyy」；整杯饮品 / 整份小食由忌口配料构成时，允许替换为同类替代品并明示。
- 例：忌蛋黄酱 → 巨无霸仍出现在「解馋备选」中，标注「巨无霸：可剔除配料 mayonnaise（保留汉堡本体）」。

### 2.3 亮点3：多套方案推荐（嵌入套餐权重、积分排序逻辑）

每次固定输出 **3 套独立推荐方案**，顺序为：**热量优选（减脂款） → 解馋备选 → 性价比优惠款**。

| 方案 | 定位 | 排序侧重 |
|------|------|----------|
| 热量优选（减脂款） | 满足饱腹前提下总热量最低 | 热量贴合度优先 |
| 解馋备选 | 口味与组合丰富度优先 | 允许热量适度上浮 |
| 性价比优惠款 | 单价最优、活动力度最大 | 预算贴合度 + 套餐权重优先 |

**套餐权重策略（内嵌于打分）**

| 套餐类型 | 权重 | 处理逻辑 |
|----------|------|----------|
| 热门活动 / 联名套餐 | **60%** | 在有效期内加权进入推荐池，优先级最高 |
| 基础经典套餐 | **25%** | 稳定供给，作为兜底主推 |
| 自由单品组合 | **15%** | 满足个性化搭配，权重最低 |
| 过期套餐 | — | **直接剔除**，不参与任何打分 |

**积分排序逻辑**

- 套餐的**可抵扣积分**纳入综合打分，积分越高，推荐排名越靠前。
- 综合打分公式（0–100 分制）：

```text
final_score = S_base
            + W_type_bonus        # 套餐类型加权奖励：热门活动/联名 60 / 经典 25 / 自由组合 15
            - penalty_dietary     # 柔性忌口扣分：命中一个辅料 -6 分（所有辅料平等赋值）
            + bonus_points        # 积分加分：min(可抵扣积分 / 10, 15)
            - penalty_over_budget # 超预算扣分：超出金额 × 2
```

- `S_base`：热量贴合度 + 饱腹度 + 预算贴合度的加权基础分（0–100）。
- 过期套餐、无活动标识套餐按下表降级处理，绝不静默保留高权重。

### 2.4 业务规则全集（固定 10 条，两份文档完全一致）

1. **用餐时段**：系统全天可用；区分早 / 午 / 晚餐仅用于微调推荐偏好，不硬性限制菜品选择，跨时段菜品可正常选择并附带提示。
2. **柔性梯度忌口筛选**：所有辅料平等赋值扣分；汉堡仅剔除第二层配料，保留汉堡本体，不会直接删除汉堡选项；不一次性全盘剔除含忌口食材的菜品，采用扣分机制。
3. **套餐权重策略**：热门活动 / 联名套餐权重 60%，过期套餐直接剔除；基础经典套餐权重 25%；自由单品组合权重 15%。
4. **预算规则**：活动套餐允许小幅超出预算，严控超预算方案数量；出现超预算方案，附带精简的预算预警贴士。
5. **评分维度**：套餐可抵扣积分纳入综合打分，积分越高，推荐排名越靠前。
6. **输出方案**：每次固定输出 3 套独立推荐方案：热量优选（减脂款）、解馋备选、性价比优惠款。
7. **筛选优先级（顺序不可调换）**：忌口过滤 > 预算约束 > 套餐权重 > 积分加分。
8. **交互强制约束**：仅提供菜品推荐，禁止自动下单；所有推荐结果强制提醒用户二次核对门店、套餐、价格信息。
9. **贴士规则**：贴士精简，仅两类场景触发：预算预警、忌口食材冲突提示，不额外增加多余小贴士。
10. **MCP 预留**：预留套餐活动有效期、积分、预算相关字段，为后续对接麦当劳 MCP 接口预留扩展空间。

---

## 3. 功能清单

- [x] 5 项用户信息结构化收集（时段 / 忌口 / 热量 / 预算 / 需求）
- [x] 输入隐私校验：拒绝手机号、邮箱、地址等个人敏感信息入参
- [x] 3 套固定方案模板输出（热量优选（减脂款） / 解馋备选 / 性价比优惠款）
- [x] 柔性梯度忌口筛选：所有辅料平等扣分，保留单品并标记可剔除配料
- [x] 汉堡级保护：仅剔除第二层配料，绝不删除汉堡本体
- [x] 跨时段单品可正常选择并附带提示（`meta.cross_slot_notice`）
- [x] 套餐活动有效期校验：`promo_valid_from` / `promo_valid_to` / `is_active`
- [x] 过期套餐自动剔除，不参与打分与推荐
- [x] 套餐权重策略：热门活动 / 联名 60%，经典 25%，自由组合 15%
- [x] 套餐可抵扣积分纳入综合打分，积分越高排名越靠前
- [x] 活动套餐小幅超预算放行 + 超预算方案数量严控（≤ 1 套 / 次）
- [x] 精简贴士机制：仅预算预警、忌口冲突两类触发
- [x] 筛选优先级固化：忌口 > 预算 > 套餐权重 > 积分
- [x] 缺快照自动回退占位菜单（`meta.used_fallback_menu = true`）
- [x] 完整 MCP 入参 / 出参 JSON Schema，预留活动、积分、预算扩展字段
- [x] CLI 双模式（`--input`/`--output` 脚本 + `recommend()` 库函数）
- [x] 强制二次核对 disclaimer（禁止删改、合并、改写）
- [x] 用户输入匿名化校验（拒绝邮箱 / 手机号格式，`user_id` 仅用匿名 ID）
- [x] 标准化错误码（2 / 3 / 4 / 5 / 6）
- [x] 季节性菜单扩展（`static_data/seasonal_menu.json`）
- [x] 冒烟测试覆盖核心场景

---

## 4. 系统三层架构

```
┌─────────────────────────────────────────────────────────────┐
│              第 1 层：WorkBuddy 对话层 (Chat Layer)          │
│   ┌───────────────────────────────────────────────────┐     │
│   │  · 触发词匹配 + 5 项信息收集                      │     │
│   │  · 输入隐私校验（拒绝手机号 / 邮箱 / 地址）       │     │
│   │  · 自然语言 → 标准 JSON 入参                      │     │
│   │  · 按固定模板渲染 3 套方案 + 贴士 + disclaimer    │     │
│   └───────────────────────────────────────────────────┘     │
└──────────────────────────┬──────────────────────────────────┘
                           │  标准 request.json（MCP 协议）
                           ▼
┌─────────────────────────────────────────────────────────────┐
│            第 2 层：MCP 网关 (Model Context Protocol)        │
│   ┌───────────────────────────────────────────────────┐     │
│   │  · 协议转换        · 入参 Schema 校验              │     │
│   │  · 进程调用        · 隐私兜底脱敏                  │     │
│   │  · 超时熔断        · 错误码透传                    │     │
│   │  · 活动有效期 / 积分 / 预算字段预留占位透传        │     │
│   └───────────────────────────────────────────────────┘     │
└──────────────────────────┬──────────────────────────────────┘
                           │  subprocess
                           │  python scripts/offline_demo.py
                           │    --input  request.json
                           │    --output response.json
                           ▼
┌─────────────────────────────────────────────────────────────┐
│        第 3 层：offline_demo.py (Python 推荐引擎)            │
│   ┌───────────────────────────────────────────────────┐     │
│   │  load_menu()          菜单/套餐加载 + 占位回退     │     │
│   │  filter_pool()        时段偏好加权 + 跨时段标记    │     │
│   │  detect_dietary()     柔性忌口扣分（不删除）       │     │
│   │  apply_budget()       预算约束 + 小幅超预算放行    │     │
│   │  apply_combo_weight() 60/25/15 权重 + 过期剔除     │     │
│   │  apply_points()       可抵扣积分加分               │     │
│   │  build_plans()        生成 3 套独立方案            │     │
│   │  attach_tips()        预算预警 / 忌口冲突贴士      │     │
│   │  attach_disclaimer()  强制尾部二次核对提示         │     │
│   └───────────────────────────────────────────────────┘     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
      { "plans": [...3 套...], "tips": [...], "disclaimer": "..." }
                           │
                           ▼
                 WorkBuddy 对话层渲染给用户
```

**层级职责边界**

| 层 | 负责 | 不负责 |
|----|------|--------|
| WorkBuddy 对话层 | 收集信息、渲染结果、强制二次核对提示 | 打分、算价、过滤、编造数据 |
| MCP 网关 | 协议转换、入参校验、脱敏、错误码透传 | 业务决策、下单、支付 |
| offline_demo.py 引擎 | 忌口扣分、预算约束、套餐权重、积分加分、生成方案 | 任何网络请求、任何下单动作 |

**筛选优先级（顺序不可调换）**：`忌口过滤 > 预算约束 > 套餐权重 > 积分加分`。

---

## 5. 项目限制 & 免责声明

| 限制 | 说明 | 缓解方式 |
|------|------|----------|
| **价格非实时** | 菜单 / 套餐中的 `price_cny` 均为**参考价**，不保证与实际售价一致 | 所有价格标注「参考价」，输出末尾强制 disclaimer |
| **库存不可知** | 单品是否售罄、时段是否供应需到店 / 官方 App 确认 | disclaimer 明示，不保证实时库存 |
| **活动不可知** | 优惠券、买一送一、联名活动等以 `promo_valid_from` / `promo_valid_to` 快照为准 | 过期套餐直接剔除，disclaimer 明示 |
| **积分不可核销** | 可抵扣积分仅参与排序打分，不执行实际积分扣减 | 明确告知积分以门店 / 官方 App 为准 |
| **不接入下单支付** | 全链路无下单 API、无支付链接、无二维码、无核销接口 | 架构层面隔离，仅输出推荐文本 |
| **不替代医疗** | 减脂热量推荐仅作为饮食搭配参考，不属于医疗健康建议 | disclaimer 明示，特殊人群建议咨询医生 / 营养师 |
| **不采集隐私** | 不采集手机号、地址、身份证、银行卡、人脸、定位等 | 入参加隐私校验，命中即拒绝并提示 |
| **不替代人工点餐** | 最终下单需用户自行通过官方渠道完成 | 全程无下单链路 |
| **快照需维护** | 新品上市 / 季节限定下架需手动同步 | `assets/menu_snapshot.json`、`static_data/seasonal_menu.json` 可热更新 |
| **5 项信息需输入** | 不支持 0 输入的「全自动猜你喜欢」 | 通过预设选项降低输入负担 |

**免责声明（输出末尾强制原文保留，禁止删改、合并、改写）**

> ⚠️ **仅为推荐，请自行核对门店套餐内容、实时价格与优惠活动，本助手无法下单，也无法核验门店库存。**

---

## 6. 使用说明

### 6.1 前置条件

- Python **3.10+**（仅使用标准库，零第三方依赖）
- 无需安装任何 `pip` 包，断网可运行

### 6.2 构造 request.json 样例

按 [`references/mcp-input-schema.md`](./references/mcp-input-schema.md) 构造 `request.json`，其中活动有效期、积分、预算相关字段为 **MCP 预留字段**（当前走本地快照，后续可直接对接麦当劳 MCP 接口）：

```json
{
  "request": {
    "user_id": "anon-3a8b1f",
    "meal_slot": "lunch",
    "dietary_restrictions": ["mayonnaise", "cheese"],
    "calorie_target_kcal": 600,
    "budget_cny": 35,
    "meal_purpose": "fitness",
    "menu_snapshot_path": "assets/menu_snapshot.json",
    "options": {
      "max_results_per_plan": 3,
      "allow_cross_slot_items": true,
      "language": "zh-CN",
      "combo_weight": {
        "promo": 0.60,
        "classic": 0.25,
        "free": 0.15
      },
      "budget_overflow": {
        "allow": true,
        "max_ratio": 0.10,
        "max_cny": 5.0,
        "max_plans": 1
      },
      "points": {
        "enabled": true,
        "max_bonus": 15
      },
      "tips": {
        "budget_warning": true,
        "dietary_conflict": true
      }
    }
  }
}
```

**套餐快照中的活动 / 积分预留字段样例**（`static_data/` 或对接 MCP 后由服务端下发）：

```json
{
  "combos": [
    {
      "id": "C001",
      "name": "巨无霸超值套餐（联名限定）",
      "type": "promo",
      "items": ["B001", "S001", "D001"],
      "price_cny": 38.0,
      "kcal": 1083,
      "points_redeemable": 120,
      "promo_valid_from": "2026-10-01",
      "promo_valid_to": "2026-10-31",
      "is_active": true
    },
    {
      "id": "C002",
      "name": "双层牛肉堡经典套餐",
      "type": "classic",
      "items": ["B002", "S001", "D002"],
      "price_cny": 40.5,
      "kcal": 770,
      "points_redeemable": 60,
      "promo_valid_from": null,
      "promo_valid_to": null,
      "is_active": true
    }
  ]
}
```

### 6.3 方式 A：CLI 调用

```bash
python scripts/offline_demo.py \
    --input  request.json \
    --output recommendation.json
```

退出码 `0` 即成功，`recommendation.json` 内含 3 套方案、精简贴士与 disclaimer。

### 6.4 方式 B：Python 库调用

```python
from scripts.offline_demo import recommend

payload = {
    "request": {
        "user_id": "anon-3a8b1f",
        "meal_slot": "lunch",
        "dietary_restrictions": ["mayonnaise"],
        "calorie_target_kcal": 600,
        "budget_cny": 35,
        "meal_purpose": "fitness",
        "menu_snapshot_path": "assets/menu_snapshot.json",
        "options": {
            "max_results_per_plan": 3,
            "allow_cross_slot_items": True,
            "language": "zh-CN",
            "combo_weight": {"promo": 0.60, "classic": 0.25, "free": 0.15},
            "budget_overflow": {"allow": True, "max_ratio": 0.10, "max_cny": 5.0, "max_plans": 1},
            "points": {"enabled": True, "max_bonus": 15},
            "tips": {"budget_warning": True, "dietary_conflict": True},
        },
    }
}

result = recommend(payload)
for plan in result["plans"]:
    print(plan["name"], "|", plan["total_kcal"], "kcal", "|",
          "参考价", plan["total_price_cny"], "元", "| 积分", plan.get("points_redeemable"))
```

### 6.5 返回结构样例

```json
{
  "meta": {
    "user_id": "anon-3a8b1f",
    "meal_slot": "lunch",
    "meal_purpose": "fitness",
    "used_fallback_menu": false,
    "fallback_notice": null,
    "cross_slot_notice": "含非常规时段单品：麦满分·火腿芝士，建议确认门店时段菜单"
  },
  "plans": [
    {
      "name": "热量优选（减脂款）",
      "combo_type": "classic",
      "items": [{"id": "B002", "name": "双层牛肉堡", "qty": 1},
                {"id": "D002", "name": "无糖可乐", "qty": 1}],
      "total_kcal": 450,
      "total_price_cny": 29.0,
      "points_redeemable": 60,
      "score_breakdown": {
        "base": 72.0,
        "type_bonus": 25.0,
        "dietary_penalty": -6.0,
        "points_bonus": 6.0,
        "over_budget_penalty": 0.0,
        "final_score": 97.0
      },
      "match_reason": "优先控制总热量与糖脂摄入，舍弃口味丰富度。",
      "restriction_notes": ["双层牛肉堡：可剔除配料 mayonnaise（保留汉堡本体）"]
    },
    {
      "name": "解馋备选",
      "combo_type": "promo",
      "items": [{"id": "B001", "name": "巨无霸", "qty": 1},
                {"id": "S001", "name": "中份薯条", "qty": 1}],
      "total_kcal": 883,
      "total_price_cny": 36.0,
      "points_redeemable": 120,
      "score_breakdown": {
        "base": 60.0,
        "type_bonus": 60.0,
        "dietary_penalty": -12.0,
        "points_bonus": 12.0,
        "over_budget_penalty": -2.0,
        "final_score": 118.0
      },
      "match_reason": "口味与组合丰富度优先，热量适度上浮。",
      "restriction_notes": ["巨无霸：可剔除配料 mayonnaise / cheese（保留汉堡本体）"]
    },
    {
      "name": "性价比优惠款",
      "combo_type": "free",
      "items": [{"id": "B004", "name": "麦辣鸡腿堡", "qty": 1},
                {"id": "D001", "name": "中杯可乐", "qty": 1}],
      "total_kcal": 680,
      "total_price_cny": 28.0,
      "points_redeemable": 30,
      "score_breakdown": {
        "base": 68.0,
        "type_bonus": 15.0,
        "dietary_penalty": 0.0,
        "points_bonus": 3.0,
        "over_budget_penalty": 0.0,
        "final_score": 86.0
      },
      "match_reason": "单价最优，预算贴合度最高。",
      "restriction_notes": ["无冲突"]
    }
  ],
  "tips": [
    {"type": "budget_warning", "text": "解馋备选为活动套餐，参考价 36.0 元，小幅超出预算 1.0 元，请确认可接受。"},
    {"type": "dietary_conflict", "text": "命中忌口：mayonnaise / cheese，请点单时手动剔除第二层配料（保留汉堡本体）。"}
  ],
  "disclaimer": "仅为推荐，请自行核对门店套餐内容、实时价格与优惠活动，本助手无法下单，也无法核验门店库存。"
}
```

### 6.6 错误码

| 退出码 | 含义 |
|--------|------|
| 0 | 成功 |
| 2 | 入参文件不存在 |
| 3 | 入参 JSON 解析失败 |
| 4 | 入参缺少根字段 `request` |
| 5 | 入参缺少必填字段 `meal_slot` / `meal_purpose` |
| 6 | 入参命中隐私校验（疑似手机号 / 邮箱 / 地址），已拒绝处理 |

### 6.7 运行测试

```bash
python test/test_cases.py
```

---

## 7. MCP 对接说明

本项目按 **MCP（Model Context Protocol）** 规范设计，推荐引擎通过标准 JSON 入参与上层解耦，当前以 `subprocess` 本地进程方式调用，后续可无缝切换为远端 MCP Server。

**预留扩展字段（为对接麦当劳 MCP 接口预留）**

| 字段 | 归属 | 当前状态 | 对接后数据来源 |
|------|------|----------|----------------|
| `promo_valid_from` / `promo_valid_to` | 套餐活动有效期 | 本地快照占位 | 麦当劳活动 MCP 接口 |
| `is_active` | 套餐上下架状态 | 本地快照占位 | 麦当劳商品 MCP 接口 |
| `points_redeemable` | 套餐可抵扣积分 | 本地快照占位 | 麦当劳会员积分 MCP 接口 |
| `budget_cny` / `budget_overflow` | 预算约束 | 用户输入 | 用户输入（可联动优惠券接口） |
| `combo_weight` | 套餐权重 | 固定 60 / 25 / 15 | 可由运营侧 MCP 接口下发 |

**对接方式**

1. **本地进程模式（当前）**：MCP 网关以 `subprocess` 拉起 `scripts/offline_demo.py --input ... --output ...`，对话层无感。
2. **远端服务模式（后续）**：将 `offline_demo.py` 的 `recommend()` 封装为 HTTP MCP Server，网关改为 POST 调用，入参 / 出参 Schema 保持不变。
3. **数据来源升级**：把 `assets/menu_snapshot.json`、`static_data/seasonal_menu.json` 替换为 MCP 实时接口返回值，字段结构保持兼容，引擎代码零改动。

**对接红线**：MCP 接口**仅用于读取菜单、活动、积分、营养等只读数据**；禁止申请或调用下单、支付、核销、优惠券发放类写接口。

完整字段定义、约束与示例见 [`references/mcp-input-schema.md`](./references/mcp-input-schema.md)，网关协议见 [`MCP_INTEGRATION.md`](./MCP_INTEGRATION.md)。

---

## 8. 开源许可证（MIT License）

本项目采用 **MIT License**。

```
MIT License

Copyright (c) 2026 McDonald's Smart Order Recommender Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
