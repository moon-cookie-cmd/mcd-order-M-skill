
"""
点餐推荐助手离线演示【全局优化完整版】
特性：浮点预算、菜品数量限制、异常容错、TOP3推荐、MCP预留接口
不会自动下单，输出二次核验提示
"""
from typing import List, Dict
from filter_recipe import filter_dishes
from score_combo import get_dish_score

# 菜品库
menu_data = [
    {
        "name": "吉士汉堡",
        "category": "汉堡",
        "time_period": ["breakfast", "lunch", "dinner"],
        "price": 12.0,
        "calorie": 320,
        "ingredients": ["面包", "牛肉饼", "芝士", "酸黄瓜", "番茄酱"],
        "can_custom": True
    },
    {
        "name": "麦香鸡汉堡",
        "category": "汉堡",
        "time_period": ["breakfast", "lunch", "dinner"],
        "price": 11.0,
        "calorie": 290,
        "ingredients": ["面包", "鸡肉饼", "生菜", "沙拉酱"],
        "can_custom": True
    },
    {
        "name": "薯条（中）",
        "category": "小食",
        "time_period": ["lunch", "dinner"],
        "price": 9.0,
        "calorie": 340,
        "ingredients": ["土豆"],
        "can_custom": False
    },
    {
        "name": "可乐（中杯）",
        "category": "饮品",
        "time_period": ["breakfast", "lunch", "dinner"],
        "price": 8.0,
        "calorie": 190,
        "ingredients": ["碳酸水", "糖浆"],
        "can_custom": False
    },
    {
        "name": "板烧鸡腿堡",
        "category": "汉堡",
        "time_period": ["lunch", "dinner"],
        "price": 16.0,
        "calorie": 380,
        "ingredients": ["面包", "板烧鸡腿肉", "生菜", "板烧酱"],
        "can_custom": True
    },
    {
        "name": "吉士蛋堡",
        "category": "汉堡",
        "time_period": ["breakfast"],
        "price": 10.0,
        "calorie": 280,
        "ingredients": ["面包", "鸡蛋", "芝士"],
        "can_custom": True
    }
]

def knapsack_top_combos(dish_list: List[Dict], budget: float, purpose: str, max_item_count: int = 3) -> List[Dict]:
    """
    改进01背包，全局最优组合
    :param dish_list: 筛选后的菜品
    :param budget: 预算上限（支持小数）
    :param purpose: 健身 / 嘴馋
    :param max_item_count: 一套套餐最多菜品数量，真实点餐限制
    :return: 按分数降序的TOP3套餐
    """
    from collections import defaultdict
    # key:(花费,菜品数量)  value:(总分,菜品列表)
    dp = defaultdict(lambda: {"score": 0.0, "items": []})
    dp[(0.0, 0)] = {"score": 0.0, "items": []}

    for dish in dish_list:
        dish_val = get_dish_score(dish, purpose)
        dish_cost = dish["price"]
        # 倒序遍历，防止重复选取同一个菜品
        prev_states = list(dp.items())
        for (cost, cnt), state in prev_states:
            new_cost = cost + dish_cost
            new_cnt = cnt + 1
            if new_cost > budget or new_cnt > max_item_count:
                continue
            new_score = state["score"] + dish_val
            # 更新更优解
            if new_score > dp[(new_cost, new_cnt)]["score"]:
                dp[(new_cost, new_cnt)] = {
                    "score": new_score,
                    "items": state["items"] + [dish]
                }
    # 收集全部有效套餐
    all_combos = []
    for (cost, cnt), state in dp.items():
        items = state["items"]
        if len(items) == 0:
            continue
        total_cal = sum(i["calorie"] for i in items)
        total_price = sum(i["price"] for i in items)
        all_combos.append({
            "items": items,
            "total_price": round(total_price, 2),
            "total_cal": total_cal,
            "score": round(state["score"], 2)
        })
    # 分数降序，取TOP3
    all_combos.sort(key=lambda x: x["score"], reverse=True)
    return all_combos[:3]

def parse_user_sentence(input_text: str):
    """
    一句话解析用户输入，提取：时段、预算、忌口、用餐目的
    返回字典，缺失字段值为None，交由后续分步提问补全
    """
    import re
    res = {
        "time_period": None,
        "budget": None,
        "taboo": [],
        "purpose": None
    }
    text = input_text.lower()

    # 提取时段
    if "早餐" in text:
        res["time_period"] = "breakfast"
    elif "午餐" in text:
        res["time_period"] = "lunch"
    elif "晚餐" in text:
        res["time_period"] = "dinner"
    elif "下午茶" in text:
        res["time_period"] = "afternoon_tea"

    # 提取预算数字
    num_match = re.search(r"(\d+)\s*(元|块)", text)
    if num_match:
        res["budget"] = int(num_match.group(1))

    # 提取忌口（关键词：不要 / 不吃 / 忌口）
    taboo_words = ["不要", "不吃", "忌口"]
    for kw in taboo_words:
        if kw in text:
            raw = text.split(kw)[-1]
            # 简单分割，逗号分隔多个忌口食材
            items = re.split(r"[,，和、]", raw)
            for item in items:
                clean = item.strip()
                if clean and clean not in ["", "元", "块"]:
                    res["taboo"].append(clean)
            break

    # 提取用餐目的
    if any(w in text for w in ["正餐"]):
        res["purpose"] = "正餐"
    elif any(w in text for w in ["减脂", "健身"]):
        res["purpose"] = "健身"
    elif any(w in text for w in ["下午茶"]):
        res["purpose"] = "下午茶"
    elif any(w in text for w in ["解馋", "嘴馋"]):
        res["purpose"] = "嘴馋"

    return res
def get_user_input() -> Dict:
    """收集用户需求，增加输入清洗，MCP对接时直接替换这个函数"""
    print("===== 点餐推荐助手【全局优化版】 =====")
    user_info = {}
    user_info["time"] = input("用餐时段（breakfast/lunch/dinner）：").strip().lower()
    # 预算容错
    while True:
        budget_str = input("预算上限(元)：").strip()
        try:
            user_info["budget"] = float(budget_str)
            break
        except ValueError:
            print("输入无效，请输入数字！")
    user_info["purpose"] = input("用餐目的：健身/嘴馋：").strip()
    taboo_input = input("忌口食材，多个用逗号隔开，无则直接回车：").strip()
    user_info["taboo"] = [t.strip() for t in taboo_input.split(",")] if taboo_input else []
    return user_info

def show_result(final_combos: List[Dict]):
    """输出套餐结果 + 二次确认提示，大赛要求：禁止直接下单"""
    if len(final_combos) == 0:
        print("\n⚠️ 在当前条件下没有找到匹配的套餐组合。")
        print("💡 当前使用离线模拟菜单数据；对接MCP后，会实时拉取门店菜单、活动，可选择品类会更多。")
        print("👉 建议：放宽预算、调整忌口食材，或者更换用餐时段重新尝试。")
        return

    print("\n==== 🥇 最优推荐套餐 TOP3 ====")
    for idx, combo in enumerate(final_combos):
        names = [i["name"] for i in combo["items"]]
        print(f"\n方案{idx+1}：{' + '.join(names)}")
        print(f"总价：{combo['total_price']}元 | 总热量：{combo['total_cal']} kcal")
        print(f"综合评分：{combo['score']:.2f}")

    print("\n⚠️【重要二次检查提醒】")
    print("1. 推荐仅为参考，请核对门店营业状态、实时优惠活动，本系统不会自动下单！")
    print("2. 套餐内汉堡若含有忌口配料，前往点餐页面手动移除对应配料。")
def generate_tips(user_params, combo_list):
    tips_list = []
    taboo = user_params.get("taboo", [])
    taste = user_params.get("taste", "无")
    time_period = user_params.get("time_period")
    budget = user_params.get("budget", 0)

    # 判断是否存在辅料忌口
    has_ingredient_adjust = bool(taboo)
    if has_ingredient_adjust:
        tips_list.append("汉堡辅料可调整，辅料之间平等评估；仅主料忌口才会移除整款汉堡")

    # 清淡口味
    if taste == "清淡":
        tips_list.append("推荐少酱、蔬菜较多的搭配")

    # 早餐提示
    if time_period == "breakfast":
        tips_list.append("早餐仅作为推荐分类，麦当劳全天都可以选购")

    # 检测是否有活动套餐
    has_activity_combo = any(item.get("type") == "热门活动套餐" for item in combo_list)
    if has_activity_combo:
        tips_list.append("活动套餐存在有效期，下单前请务必核对门店活动状态")

    # 预算紧张判断：最贵套餐接近预算
    if combo_list:
        max_price = max(float(c["total_price"]) for c in combo_list)
        if max_price >= budget * 0.9:
            tips_list.append("优先选择基础套餐，性价比更高")

    # 多套方案提示
    if len(combo_list) > 1:
        tips_list.append("方案排序综合参考价格、菜品搭配、热门程度")

    # 兜底
    if not tips_list:
        tips_list.append("按需核对配料，合理搭配用餐。")

    # 限制最多2条贴士
    final_tips = " ".join(tips_list[:2])
    return final_tips
def run_skill(user_req: Dict):
    """
    预留MCP对外调用入口
    WorkBuddy / MCP 对接时直接调用此函数，不需要控制台输入
    """
    # 入参归一化：兼容 MCP 入参键名（meal_slot / meal_purpose），预算统一转 float
    req = dict(user_req)
    req["time"] = req.get("time") or req.get("meal_slot") or ""
    req["purpose"] = req.get("purpose") or req.get("meal_purpose") or ""
    try:
        req["budget"] = float(req.get("budget", 0))
    except (TypeError, ValueError):
        req["budget"] = 0.0

    available_dishes = filter_dishes(menu_data, req)
    # 修复：knapsack_top_combos 签名是 (dish_list, budget, purpose)，原调用把整个 user_req 当预算传入
    top_combos = knapsack_top_combos(available_dishes, req["budget"], req["purpose"])
    # 生成小贴士，组装标准返回结构，对齐MCP出参Schema
    tips_text = generate_tips(req, top_combos)
    return {
        "combo_list": top_combos,
        "tips": tips_text,
        "msg": "成功生成推荐套餐" if top_combos else "暂无匹配的套餐，请放宽条件重试"
    }



if __name__ == "__main__":
    print("===== 点餐推荐助手【全局优化版】=====")
    print("使用方式：①直接输入一整句话描述需求；②直接回车，进入分步填写模式")
    while True:
        raw_input = input("\n请输入你的点餐需求：").strip()
        if not raw_input:
            # 用户直接回车，走原来分步问答
            user_info = get_user_info()
        else:
            # 尝试解析一句话
            parsed = parse_user_sentence(raw_input)
            user_info = parsed
            # 检查缺失字段，缺失则逐个追问补齐
            if not user_info["time_period"]:
                time_in = input("用餐时段(breakfast/lunch/dinner/afternoon_tea)：").strip()
                user_info["time_period"] = time_in
            if not user_info["budget"]:
                while True:
                    try:
                        b = int(input("预算上限(元)："))
                        user_info["budget"] = b
                        break
                    except ValueError:
                        print("输入无效，请输入数字！")
            if not user_info["purpose"]:
                purpose_in = input("用餐目的（正餐/健身/嘴馋/下午茶等）：").strip()
                user_info["purpose"] = purpose_in
            if len(user_info["taboo"]) == 0:
                taboo_in = input("忌口食材，多个用逗号隔开，无则直接回车：").strip()
                if taboo_in:
                    user_info["taboo"] = [t.strip() for t in taboo_in.split(",")]

        # 调用推荐逻辑
        available_dishes = filter_dishes(menu_data,user_info)
        top_combos = knapsack_top_combos(available_dishes, user_info["budget"],user_info["purpose"] )
        show_result(top_combos)

        again = input("\n是否继续推荐？(y/n)")
        if again.lower() != "y":
            print("程序退出")
            break
