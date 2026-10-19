
"""
套餐打分模块 score_combo.py
输出单个菜品的价值分，给背包算法用来求全局最优套餐
"""
def get_dish_score(dish, purpose):
    cal = dish["calorie"]
    price = dish["price"]
    if purpose == "健身":
        # 健身：低热量高分，价格增加扣分
        score = 100 - (cal / 5) - (price * 1.2)
    else:
        # 嘴馋：美味优先，控制热量
        score = 100 - (cal / 12) + (15 - price)
    return score
