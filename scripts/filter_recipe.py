
"""
菜品筛选模块
职责：按时段、预算、忌口过滤菜品
规则：汉堡支持自定义配料，存在忌口食材时保留汉堡，点餐阶段手动去除配料；非汉堡含忌口直接剔除
"""
from typing import List, Dict

def filter_dishes(menu_data: List[Dict], user_req: Dict) -> List[Dict]:
    time_target = user_req.get("time", "")
    taboo_list = user_req.get("taboo", [])
    budget = float(user_req.get("budget", 0))
    result = []

    for dish in menu_data:
        # 时段校验
        if time_target not in dish.get("time_period", []):
            continue
        # 单品价格不能超过总预算
        if dish.get("price", 0) > budget:
            continue

        ingredients = dish.get("ingredients", [])
        taboo_contained = any(tab in ingredients for tab in taboo_list if tab.strip())

        if taboo_contained:
            # 汉堡可定制，保留菜品
            if dish["category"] == "汉堡" and dish.get("can_custom", False):
                result.append(dish)
            # 非汉堡含忌口，丢弃
            continue
        else:
            result.append(dish)
    return result
