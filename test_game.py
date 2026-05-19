"""
SYB 沙盘模拟游戏 - 综合测试脚本
运行方式：python test_game.py
"""

from syb_game.game_state import GameState, Loan, Inventory, Market
from syb_game.save_load import save_game, load_game
from syb_game import config


def test_basic_flow():
    print("=" * 60)
    print("测试1：基础流程测试（初始化 → 购买 → 生产 → 销售）")
    print("=" * 60)

    gs = GameState("张三")
    assert gs.player_name == "张三", "玩家名称错误"
    assert gs.cash == 10000.0, f"初始现金错误：{gs.cash}"
    assert gs.day == 0, f"初始天数错误：{gs.day}"
    print("✅ 游戏初始化成功")

    price_rc = gs.market.get_material_price("RC")
    assert price_rc > 0, "原材料价格异常"
    print(f"  原材料当前价：{price_rc}")

    success, msg = gs.buy_raw_material("RC", 20)
    assert success, f"购买失败：{msg}"
    assert gs.inventory.get_raw_material_qty("RC") == 20, "原材料库存数量错误"
    print(f"✅ 购买原材料成功：{msg}")

    success, msg = gs.produce("CP", 10)
    assert success, f"生产失败：{msg}"
    assert gs.inventory.get_product_qty("CP") == 10, "产品库存数量错误"
    assert gs.inventory.get_raw_material_qty("RC") == 10, "生产后原材料消耗异常"
    print(f"✅ 生产产品成功：{msg}")

    price_cp = gs.market.get_product_buy_price("CP", "RT2")
    assert price_cp > 0, "产品收购价异常"
    print(f"  标准零售商产品收购价：{price_cp}")

    cash_before = gs.cash
    success, msg = gs.sell("CP", 3, "RT2")
    assert success, f"销售失败：{msg}"
    assert gs.cash > cash_before, "销售后现金未增加"
    assert gs.inventory.get_product_qty("CP") == 7, "销售后库存数量错误"
    print(f"✅ 销售产品成功：{msg}")

    print("✅ 基础流程测试通过！\n")


def test_next_day():
    print("=" * 60)
    print("测试2：时间推进与固定开销")
    print("=" * 60)

    gs = GameState("李四")
    cash_before = gs.cash

    events = gs.next_day()
    assert gs.day == 1, f"天数推进错误：{gs.day}"
    assert len(events) > 0, "无事件触发"
    assert gs.cash == cash_before - config.FIXED_COST_TOTAL, "固定开销扣除异常"
    print(f"✅ 天数推进到第{gs.day}天，固定开销{config.FIXED_COST_TOTAL}金币已扣除")
    for e in events:
        print(f"  • {e}")

    gs.next_day()
    gs.next_day()
    gs.next_day()
    gs.next_day()
    gs.next_day()
    gs.next_day()
    gs.next_day()
    assert gs.day == 8, f"天数推进错误：{gs.day}"
    print(f"✅ 推进到第{gs.day}天")

    print("✅ 时间推进测试通过！\n")


def test_loan_and_repay():
    print("=" * 60)
    print("测试3：贷款与还款")
    print("=" * 60)

    gs = GameState("王五")

    success, msg = gs.take_loan(5000)
    assert success, f"贷款失败：{msg}"
    assert gs.cash == 15000, f"贷款后现金异常：{gs.cash}"
    assert len(gs.loans) == 1, "贷款记录异常"
    print(f"✅ 贷款成功：{msg}")

    success, msg = gs.repay_loan()
    assert success, f"还款失败：{msg}"
    print(f"✅ 还款成功：{msg}")

    success, msg = gs.take_loan(3000)
    assert success, f"第二次贷款失败：{msg}"
    cash_after_loan = gs.cash
    print(f"✅ 再次贷款成功，当前现金：{cash_after_loan}")

    gs.next_day()
    assert gs.loans[0].days_remaining == 9, "贷款天数未减少"
    print(f"✅ 过一天后贷款到期日：{gs.loans[0].days_remaining}天")

    success, msg = gs.repay_loan()
    assert success, f"还款失败：{msg}"
    print(f"✅ 还款成功：{msg}")

    print("✅ 贷款还款测试通过！\n")


def test_finance_and_log():
    print("=" * 60)
    print("测试4：财务报表与经营日志")
    print("=" * 60)

    gs = GameState("赵六")
    gs.buy_raw_material("RC", 30)
    gs.produce("CP", 10)
    gs.sell("CP", 3, "RT1")
    gs.next_day()
    gs.next_day()
    gs.take_loan(2000)

    report = gs.get_finance_report()
    assert "财务报表" in report, "财务报表格式错误"
    print(report)
    print()

    log = gs.get_log()
    assert "经营日志" in log, "经营日志格式错误"
    print(log)
    print()

    report_text = gs.get_weekly_report()
    assert "本周经营报告" in report_text, "周报格式错误"
    print(report_text)
    print()

    print("✅ 财务报表与日志测试通过！\n")


def test_market_and_inventory():
    print("=" * 60)
    print("测试5：市场信息与库存查看")
    print("=" * 60)

    gs = GameState("钱七")

    market_info = gs.get_market_info()
    assert "市场信息" in market_info, "市场信息格式错误"
    assert "RC" in market_info, "市场信息缺少原材料"
    assert "CP" in market_info, "市场信息缺少产品"
    print(market_info)
    print()

    inv_info = gs.get_inventory_info()
    assert "库存清单" in inv_info, "库存清单格式错误"
    print(inv_info)
    print()

    gs.buy_raw_material("RC", 15)
    gs.produce("CP", 8)

    inv_info2 = gs.get_inventory_info()
    assert "原材料" in inv_info2, "库存清单未包含原材料"
    assert "产品" in inv_info2, "库存清单未包含产品"
    print(inv_info2)
    print()

    print("✅ 市场与库存测试通过！\n")


def test_save_load():
    print("=" * 60)
    print("测试6：存档与读档")
    print("=" * 60)

    gs = GameState("周八")
    gs.buy_raw_material("RC", 20)
    gs.produce("CP", 12)
    gs.sell("CP", 5, "RT3")
    gs.next_day()
    gs.next_day()

    cash_before_save = gs.cash
    day_before_save = gs.day

    filepath = save_game(gs, "test_save")
    print(f"✅ 游戏已保存至：{filepath}")

    loaded_gs, msg = load_game("test_save")
    assert loaded_gs is not None, f"加载失败：{msg}"
    assert loaded_gs.cash == cash_before_save, f"存档现金不一致：{loaded_gs.cash} vs {cash_before_save}"
    assert loaded_gs.day == day_before_save, f"存档天数不一致：{loaded_gs.day} vs {day_before_save}"
    assert loaded_gs.inventory.get_raw_material_qty("RC") == 8, "存档原材料库存不一致"
    assert loaded_gs.inventory.get_product_qty("CP") == 7, "存档产成品库存不一致"
    assert len(loaded_gs.log) == len(gs.log), "存档日志数量不一致"
    print(f"✅ 游戏加载成功：{msg}")

    import os
    os.remove(filepath)
    print("✅ 测试存档已清理")

    print("✅ 存档读档测试通过！\n")


def test_error_handling():
    print("=" * 60)
    print("测试7：错误处理测试")
    print("=" * 60)

    gs = GameState("错误测试")

    success, msg = gs.buy_raw_material("RC", 9999)
    assert not success, "现金不足时购买应失败"
    print(f"✅ 现金不足检查通过：{msg}")

    success, msg = gs.produce("CP", 10)
    assert not success, "原材料不足时应生产失败"
    print(f"✅ 原材料不足检查通过：{msg}")

    success, msg = gs.produce("UNKNOWN", 1)
    assert not success, "未知产品ID应失败"
    print(f"✅ 未知产品检查通过：{msg}")

    gs.buy_raw_material("RC", 10)
    gs.produce("CP", 10)

    success, msg = gs.sell("CP", 20, "RT1")
    assert not success, "库存不足时应销售失败"
    print(f"✅ 库存不足检查通过：{msg}")

    success, msg = gs.sell("CP", 1, "UNKNOWN")
    assert not success, "未知零售商ID应失败"
    print(f"✅ 未知零售商检查通过：{msg}")

    success, msg = gs.take_loan(-100)
    assert not success, "负数贷款应失败"
    print(f"✅ 负数贷款检查通过：{msg}")

    print("✅ 错误处理测试通过！\n")


if __name__ == "__main__":
    print("\n🧪 SYB 沙盘模拟游戏 - 综合测试套件\n")
    test_basic_flow()
    test_next_day()
    test_loan_and_repay()
    test_finance_and_log()
    test_market_and_inventory()
    test_save_load()
    test_error_handling()
    print("=" * 60)
    print("🎉 所有测试通过！")
    print("=" * 60)