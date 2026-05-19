import argparse
import sys
from syb_game.game_state import GameState
from syb_game.save_load import save_game, load_game, list_saves
from syb_game import config


_current_game = None
_current_save_name = None


def require_game():
    if _current_game is None:
        print("错误：游戏未初始化。请先使用 syb init <player_name> 初始化游戏")
        sys.exit(1)


def cmd_init(args):
    global _current_game, _current_save_name
    if _current_game is not None:
        print(f"警告：当前已有进行中的游戏（玩家：{_current_game.player_name}），将覆盖当前进度")
    _current_game = GameState(args.player_name)
    _current_save_name = None
    print(f"╔══════════════════════════════════════════╗")
    print(f"║        SYB 沙盘模拟 · 企业创办成功！         ║")
    print(f"╠══════════════════════════════════════════╣")
    print(f"║  玩家：{args.player_name}")
    print(f"║  初始资金：{config.INITIAL_CASH:.0f} 金币")
    print(f"║  游戏天数：第 0 天")
    print(f"║                                          ║")
    print(f"║  输入 syb help 查看可用命令                 ║")
    print(f"╚══════════════════════════════════════════╝")


def cmd_save(args):
    require_game()
    save_name = args.save_name or _current_game.player_name
    filepath = save_game(_current_game, save_name)
    global _current_save_name
    _current_save_name = save_name
    print(f"游戏已保存至：{filepath}")


def cmd_load(args):
    global _current_game, _current_save_name
    state, msg = load_game(args.save_name)
    if state is None:
        print(f"错误：{msg}")
        return
    _current_game = state
    _current_save_name = args.save_name
    print(msg)
    print(f"当前现金：{_current_game.cash:.2f} 金币")


def cmd_listsaves(args):
    saves = list_saves()
    if not saves:
        print("暂无存档")
        return
    print(f"╔══════════════════════════════════════════╗")
    print(f"║              存档列表                       ║")
    print(f"╠══════════════════════════════════════════╣")
    for s in saves:
        print(f"║  [{s['name']:12s}] 玩家：{s['player']:8s}  第{s['day']}天  现金：{s['cash']:>8.2f} ║")
    print(f"╚══════════════════════════════════════════╝")


def cmd_next_day(args):
    require_game()
    events = _current_game.next_day()
    print(f"╔══════════════════════════════════════════╗")
    print(f"║         进入第 {_current_game.day} 天              ║")
    print(f"╠══════════════════════════════════════════╣")
    for event in events:
        print(f"║  • {event[:40]:40s}║")
    print(f"║                                          ║")
    print(f"║  当前现金：{_current_game.cash:>8.2f} 金币            ║")
    print(f"╚══════════════════════════════════════════╝")


def cmd_week_report(args):
    require_game()
    report = _current_game.get_weekly_report()
    print(report)


def cmd_market(args):
    require_game()
    info = _current_game.get_market_info()
    print(info)


def cmd_buy(args):
    require_game()
    success, msg = _current_game.buy_raw_material(args.item_id, args.quantity)
    if success:
        print(f"✅ {msg}")
    else:
        print(f"❌ {msg}")


def cmd_produce(args):
    require_game()
    success, msg = _current_game.produce(args.product_id, args.quantity)
    if success:
        print(f"✅ {msg}")
    else:
        print(f"❌ {msg}")


def cmd_inventory(args):
    require_game()
    info = _current_game.get_inventory_info()
    print(info)


def cmd_sell(args):
    require_game()
    success, msg = _current_game.sell(args.product_id, args.quantity, args.retailer_id)
    if success:
        print(f"✅ {msg}")
    else:
        print(f"❌ {msg}")


def cmd_loan(args):
    require_game()
    success, msg = _current_game.take_loan(args.amount)
    if success:
        print(f"✅ {msg}")
    else:
        print(f"❌ {msg}")


def cmd_repay(args):
    require_game()
    success, msg = _current_game.repay_loan()
    if success:
        print(f"✅ {msg}")
    else:
        print(f"❌ {msg}")


def cmd_finance(args):
    require_game()
    report = _current_game.get_finance_report()
    print(report)


def cmd_log(args):
    require_game()
    log = _current_game.get_log()
    print(log)


def cmd_help(args):
    help_text = """
╔══════════════════════════════════════════════════════════════╗
║               SYB 沙盘模拟 · 命令帮助                          ║
╠══════════════════════════════════════════════════════════════╣
║  一、游戏初始化与存档                                          ║
║    syb init <player_name>         初始化游戏                  ║
║    syb save [save_name]           保存游戏                    ║
║    syb load <save_name>           加载存档                    ║
║    syb saves                     查看存档列表                 ║
║                                                              ║
║  二、游戏进程操作                                              ║
║    syb next_day                   推进到下一天                 ║
║    syb week_report                查看本周经营报告             ║
║                                                              ║
║  三、采购与生产                                                ║
║    syb market                    查看市场信息                 ║
║    syb buy <item_id> <qty>       购买原材料                   ║
║    syb produce <product_id> <qty> 生产商品                    ║
║    syb inventory                 查看库存清单                 ║
║                                                              ║
║  四、销售与服务                                                ║
║    syb sell <product_id> <qty> <retailer_id>  销售商品        ║
║    syb loan <amount>             申请银行贷款                 ║
║    syb repay                     偿还贷款                     ║
║                                                              ║
║  五、财务与簿记                                                ║
║    syb finance                   查看财务报表                 ║
║    syb log                       查看经营日志                 ║
║                                                              ║
║  物品ID：WL(羊毛) CB(棉布) NX(尼龙)                            ║
║  产品ID：HT(帽子) SF(围巾) GZ(手套)                            ║
║  零售商ID：RT1(精品) RT2(标准) RT3(折扣)                       ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(help_text)


def main():
    parser = argparse.ArgumentParser(
        prog="syb",
        description="SYB 沙盘模拟游戏 - 体验创办并经营一家企业的完整过程",
        add_help=False,
    )
    parser.add_argument("command", nargs="?", default="help", help="命令")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="命令参数")

    if len(sys.argv) == 1:
        cmd_help(None)
        return

    command = sys.argv[1]
    command_args = sys.argv[2:]

    cmd_map = {
        "init": ("init", ["player_name"]),
        "save": ("save", ["save_name?"]),
        "load": ("load", ["save_name"]),
        "saves": ("listsaves", []),
        "next_day": ("next_day", []),
        "week_report": ("week_report", []),
        "market": ("market", []),
        "buy": ("buy", ["item_id", "quantity"]),
        "produce": ("produce", ["product_id", "quantity"]),
        "inventory": ("inventory", []),
        "sell": ("sell", ["product_id", "quantity", "retailer_id"]),
        "loan": ("loan", ["amount"]),
        "repay": ("repay", []),
        "finance": ("finance", []),
        "log": ("log", []),
        "help": ("help", []),
    }

    if command not in cmd_map:
        print(f"未知命令：{command}")
        print("输入 syb help 查看可用命令")
        return

    cmd_name, arg_spec = cmd_map[command]

    class Args:
        pass

    parsed_args = Args()
    arg_index = 0
    for spec in arg_spec:
        is_optional = spec.endswith("?")
        clean_spec = spec.rstrip("?")
        if arg_index < len(command_args):
            val = command_args[arg_index]
            if clean_spec in ("quantity", "amount"):
                try:
                    val = int(val) if clean_spec == "quantity" else float(val)
                except ValueError:
                    print(f"错误：{clean_spec} 必须为数字")
                    return
            setattr(parsed_args, clean_spec, val)
            arg_index += 1
        elif is_optional:
            setattr(parsed_args, clean_spec, None)
        else:
            print(f"错误：缺少参数 {clean_spec}")
            print(f"用法：syb {command} {' '.join(arg_spec)}")
            return

    cmd_func_name = f"cmd_{cmd_name}"
    if cmd_func_name in globals():
        globals()[cmd_func_name](parsed_args)
    else:
        print(f"内部错误：未实现命令处理函数 {cmd_func_name}")


if __name__ == "__main__":
    main()