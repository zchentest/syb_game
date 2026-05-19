import random
import copy
from syb_game import config
from syb_game.config import (
    get_material_name, get_product_name, get_product_info,
    get_material_base_price, get_retailer_info
)


class Loan:
    def __init__(self, amount, days_remaining=config.LOAN_DEFAULT_DAYS,
                 interest_rate=config.LOAN_DAILY_INTEREST_RATE):
        self.amount = amount
        self.interest_rate = interest_rate
        self.days_remaining = days_remaining
        self.total_to_repay = amount * (1 + interest_rate * days_remaining)

    def to_dict(self):
        return {
            "amount": self.amount,
            "interest_rate": self.interest_rate,
            "days_remaining": self.days_remaining,
            "total_to_repay": self.total_to_repay,
        }

    @classmethod
    def from_dict(cls, data):
        loan = cls(data["amount"])
        loan.interest_rate = data["interest_rate"]
        loan.days_remaining = data["days_remaining"]
        loan.total_to_repay = data["total_to_repay"]
        return loan

    def apply_daily_interest(self):
        daily_interest = self.total_to_repay * self.interest_rate
        self.total_to_repay += daily_interest
        self.days_remaining -= 1
        return daily_interest

    @property
    def is_overdue(self):
        return self.days_remaining < 0

    @property
    def is_paid_off(self):
        return self.total_to_repay <= 0


class Inventory:
    def __init__(self):
        self.raw_materials = {}
        self.products = {}

    def to_dict(self):
        return {
            "raw_materials": self.raw_materials,
            "products": self.products,
        }

    @classmethod
    def from_dict(cls, data):
        inv = cls()
        inv.raw_materials = data.get("raw_materials", {})
        inv.products = data.get("products", {})
        return inv

    def add_raw_material(self, material_id, quantity, unit_cost):
        if material_id not in self.raw_materials:
            self.raw_materials[material_id] = {"quantity": 0, "avg_cost": 0.0}
        entry = self.raw_materials[material_id]
        total_qty = entry["quantity"] + quantity
        total_cost = entry["quantity"] * entry["avg_cost"] + quantity * unit_cost
        entry["quantity"] = total_qty
        entry["avg_cost"] = total_cost / total_qty if total_qty > 0 else 0

    def remove_raw_material(self, material_id, quantity):
        if material_id not in self.raw_materials:
            return False
        entry = self.raw_materials[material_id]
        if entry["quantity"] < quantity:
            return False
        entry["quantity"] -= quantity
        if entry["quantity"] == 0:
            entry["avg_cost"] = 0
        return True

    def add_product(self, product_id, quantity, unit_cost):
        if product_id not in self.products:
            self.products[product_id] = {"quantity": 0, "avg_cost": 0.0}
        entry = self.products[product_id]
        total_qty = entry["quantity"] + quantity
        total_cost = entry["quantity"] * entry["avg_cost"] + quantity * unit_cost
        entry["quantity"] = total_qty
        entry["avg_cost"] = total_cost / total_qty if total_qty > 0 else 0

    def remove_product(self, product_id, quantity):
        if product_id not in self.products:
            return False
        entry = self.products[product_id]
        if entry["quantity"] < quantity:
            return False
        entry["quantity"] -= quantity
        if entry["quantity"] == 0:
            entry["avg_cost"] = 0
        return True

    def get_raw_material_qty(self, material_id):
        if material_id not in self.raw_materials:
            return 0
        return self.raw_materials[material_id]["quantity"]

    def get_product_qty(self, product_id):
        if product_id not in self.products:
            return 0
        return self.products[product_id]["quantity"]

    def get_raw_material_value(self, material_id, current_price=None):
        if material_id not in self.raw_materials:
            return 0
        entry = self.raw_materials[material_id]
        if current_price:
            return entry["quantity"] * current_price
        return entry["quantity"] * entry["avg_cost"]

    def get_product_value(self, product_id, current_price=None):
        if product_id not in self.products:
            return 0
        entry = self.products[product_id]
        if current_price:
            return entry["quantity"] * current_price
        return entry["quantity"] * entry["avg_cost"]

    def total_inventory_value(self, material_prices=None, product_prices=None):
        total = 0
        for mid, entry in self.raw_materials.items():
            if material_prices and mid in material_prices:
                total += entry["quantity"] * material_prices[mid]
            else:
                total += entry["quantity"] * entry["avg_cost"]
        for pid, entry in self.products.items():
            if product_prices and pid in product_prices:
                total += entry["quantity"] * product_prices[pid]
            else:
                total += entry["quantity"] * entry["avg_cost"]
        return total


class LogEntry:
    def __init__(self, day, entry_type, description, amount=0, balance=0):
        self.day = day
        self.entry_type = entry_type
        self.description = description
        self.amount = amount
        self.balance = balance

    def to_dict(self):
        return {
            "day": self.day,
            "type": self.entry_type,
            "description": self.description,
            "amount": self.amount,
            "balance": self.balance,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["day"], data["type"],
            data["description"], data["amount"], data["balance"]
        )


class Market:
    def __init__(self, day=0):
        self.day = day
        self.material_prices = {}
        self.retailer_product_prices = {}
        self.demand_trends = {}
        self._init_prices()

    def _init_prices(self):
        random.seed(42)
        for m in config.RAW_MATERIALS:
            variance = random.uniform(-0.1, 0.1)
            self.material_prices[m["id"]] = round(
                m["base_price"] * (1 + variance), 2
            )
        for p in config.PRODUCTS:
            base_price = sum(
                config.get_material_base_price(rid) * qty
                for rid, qty in p["recipe"].items()
            )
            self.demand_trends[p["id"]] = random.randint(0, 2)
            self.retailer_product_prices[p["id"]] = {}
            for r in config.RETAILERS:
                variance = random.uniform(-0.05, 0.05)
                price = round(base_price * r["price_multiplier"] * (1 + variance), 2)
                self.retailer_product_prices[p["id"]][r["id"]] = price

    def update_prices(self):
        self.day += 1
        random.seed()
        for m in config.RAW_MATERIALS:
            change = random.uniform(-0.15, 0.15)
            current = self.material_prices.get(m["id"], m["base_price"])
            new_price = current * (1 + change)
            new_price = max(m["base_price"] * 0.5, min(m["base_price"] * 1.5, new_price))
            self.material_prices[m["id"]] = round(new_price, 2)
        for p in config.PRODUCTS:
            trend_shift = random.random()
            if trend_shift < 0.3:
                self.demand_trends[p["id"]] = random.randint(0, 2)
            for r in config.RETAILERS:
                base_product_cost = sum(
                    config.get_material_base_price(rid) * qty
                    for rid, qty in p["recipe"].items()
                )
                change = random.uniform(-0.08, 0.08)
                price = round(
                    base_product_cost * r["price_multiplier"] * (1 + change), 2
                )
                self.retailer_product_prices[p["id"]][r["id"]] = price

    def get_demand_trend_text(self, product_id):
        info = config.get_product_info(product_id)
        if not info:
            return ""
        trend_idx = self.demand_trends.get(product_id, 1)
        template = config.DEMAND_TRENDS[trend_idx]
        return template.format(product=info["name"])

    def get_material_price(self, material_id):
        return self.material_prices.get(
            material_id,
            config.get_material_base_price(material_id)
        )

    def get_product_buy_price(self, product_id, retailer_id):
        return self.retailer_product_prices.get(product_id, {}).get(retailer_id, 0)

    def to_dict(self):
        return {
            "day": self.day,
            "material_prices": self.material_prices,
            "retailer_product_prices": self.retailer_product_prices,
            "demand_trends": self.demand_trends,
        }

    @classmethod
    def from_dict(cls, data):
        market = cls()
        market.day = data.get("day", 0)
        market.material_prices = data.get("material_prices", {})
        market.retailer_product_prices = data.get("retailer_product_prices", {})
        market.demand_trends = data.get("demand_trends", {})
        return market


class GameState:
    def __init__(self, player_name=None):
        self.player_name = player_name
        self.cash = config.INITIAL_CASH if player_name else 0
        self.day = config.INITIAL_DAY if player_name else 0
        self.reputation = config.INITIAL_REPUTATION if player_name else 0
        self.inventory = Inventory() if player_name else Inventory()
        self.loans = []
        self.log = []
        self.market = Market(self.day) if player_name else Market(0)
        self.week_revenue = 0
        self.week_cost = 0
        self.weekly_log = []
        if player_name:
            self._log("init", f"游戏初始化完成，{player_name}的企业正式成立！初始资金：{config.INITIAL_CASH}金币", config.INITIAL_CASH, config.INITIAL_CASH)

    def _log(self, entry_type, description, amount=0, balance=None):
        if balance is None:
            balance = self.cash
        entry = LogEntry(self.day, entry_type, description, amount, balance)
        self.log.append(entry)
        return entry

    def next_day(self):
        self.day += 1
        events = []

        fixed_cost = config.FIXED_COST_TOTAL
        self.cash -= fixed_cost
        self._log("expense", f"支付第{self.day}天固定开销：租金{config.FIXED_COST_RENT}+水电{config.FIXED_COST_UTILITIES}+其他{config.FIXED_COST_OTHER}={fixed_cost}金币", -fixed_cost)
        events.append(f"支付固定开销 {fixed_cost} 金币")

        interest_total = 0
        for loan in self.loans[:]:
            if not loan.is_paid_off:
                interest = loan.apply_daily_interest()
                interest_total += interest
                if loan.is_overdue:
                    events.append(f"贷款逾期！剩余{loan.days_remaining}天，应还{loan.total_to_repay:.2f}金币")
                elif loan.days_remaining >= 0:
                    events.append(f"贷款到期日：{loan.days_remaining}天，本息合计{loan.total_to_repay:.2f}金币")

        if interest_total > 0:
            self._log("interest", f"贷款利息累计：{interest_total:.2f}金币", -interest_total)
            events.append(f"贷款利息 {interest_total:.2f} 金币已计入")

        self.market.update_prices()

        trend_event = random.choice(["市场需求波动", "原材料价格变动", "零售商报价更新"])
        events.append(trend_event)

        self._log("day", f"进入第{self.day}天", 0)
        return events

    def buy_raw_material(self, material_id, quantity):
        price_per_unit = self.market.get_material_price(material_id)
        total_cost = price_per_unit * quantity

        if self.cash < total_cost:
            return False, f"现金不足！需要{total_cost:.2f}金币，当前只有{self.cash:.2f}金币"

        self.cash -= total_cost
        self.inventory.add_raw_material(material_id, quantity, price_per_unit)

        name = config.get_material_name(material_id)
        self._log("buy", f"购买 {name}x{quantity}，单价{price_per_unit:.2f}金币，总价{total_cost:.2f}金币", -total_cost)
        return True, f"成功购买 {name}x{quantity}，花费{total_cost:.2f}金币"

    def produce(self, product_id, quantity):
        product_info = config.get_product_info(product_id)
        if not product_info:
            return False, f"未知的产品ID：{product_id}"

        recipe = product_info["recipe"]
        for material_id, required_qty in recipe.items():
            available = self.inventory.get_raw_material_qty(material_id)
            if available < required_qty * quantity:
                mat_name = config.get_material_name(material_id)
                return False, f"原材料不足！需要{mat_name}x{required_qty * quantity}，当前仅有{available}"

        total_cost = 0
        for material_id, required_qty in recipe.items():
            entry = self.inventory.raw_materials.get(material_id, {})
            unit_cost = entry.get("avg_cost", 0)
            cost = unit_cost * required_qty * quantity
            total_cost += cost
            self.inventory.remove_raw_material(material_id, required_qty * quantity)

        unit_cost = total_cost / quantity if quantity > 0 else 0
        self.inventory.add_product(product_id, quantity, unit_cost)

        name = config.get_product_name(product_id)
        self._log("produce", f"生产 {name}x{quantity}，消耗原材料成本{total_cost:.2f}金币", 0)
        return True, f"成功生产 {name}x{quantity}！消耗原材料完毕，生产周期1天"

    def sell(self, product_id, quantity, retailer_id):
        retailer = config.get_retailer_info(retailer_id)
        if not retailer:
            return False, f"未知的零售商ID：{retailer_id}"

        price_per_unit = self.market.get_product_buy_price(product_id, retailer_id)
        if price_per_unit <= 0:
            return False, f"零售商 {retailer['name']} 当前不出价购买此产品"

        available = self.inventory.get_product_qty(product_id)
        if available < quantity:
            prod_name = config.get_product_name(product_id)
            return False, f"库存不足！需要{prod_name}x{quantity}，当前仅有{available}"

        total_revenue = price_per_unit * quantity
        self.cash += total_revenue
        self.inventory.remove_product(product_id, quantity)

        prod_name = config.get_product_name(product_id)
        entry = self.inventory.products.get(product_id, {})
        cost_per_unit = entry.get("avg_cost", 0)
        profit = (price_per_unit - cost_per_unit) * quantity

        self._log("sell", f"向{retailer['name']}出售 {prod_name}x{quantity}，单价{price_per_unit:.2f}金币，总收入{total_revenue:.2f}金币，利润{profit:.2f}金币", total_revenue)

        self.week_revenue += total_revenue
        self.week_cost += cost_per_unit * quantity
        self.weekly_log.append(f"出售 {prod_name}x{quantity} 给{retailer['name']}，收入{total_revenue:.2f}金币")

        if profit > 0:
            rep_gain = max(1, int(profit / 50))
            self.reputation += rep_gain

        return True, f"成功向{retailer['name']}出售 {prod_name}x{quantity}，收入{total_revenue:.2f}金币，利润{profit:.2f}金币"

    def take_loan(self, amount):
        if amount <= 0:
            return False, "贷款金额必须大于0"

        max_loan = self.cash * config.LOAN_MAX_MULTIPLIER
        if amount > max_loan:
            return False, f"基于当前现金{self.cash:.2f}金币，最大可贷额度为{max_loan:.2f}金币"

        total_repay = amount * (1 + config.LOAN_DAILY_INTEREST_RATE * config.LOAN_DEFAULT_DAYS)
        loan = Loan(amount)
        self.loans.append(loan)
        self.cash += amount

        self._log("loan", f"获得贷款{amount:.2f}金币，{config.LOAN_DEFAULT_DAYS}天后需还{total_repay:.2f}金币（日利率{config.LOAN_DAILY_INTEREST_RATE*100}%）", amount)
        return True, f"贷款成功！获得{amount:.2f}金币，{config.LOAN_DEFAULT_DAYS}天内需归还{total_repay:.2f}金币"

    def repay_loan(self):
        if not self.loans:
            return False, "当前没有未还贷款"

        active_loans = [l for l in self.loans if not l.is_paid_off]
        if not active_loans:
            return False, "所有贷款已还清"

        active_loans.sort(key=lambda l: l.days_remaining)
        loan = active_loans[0]
        repay_amount = loan.total_to_repay

        if self.cash < repay_amount:
            return False, f"现金不足！需要{repay_amount:.2f}金币偿还贷款，当前仅有{self.cash:.2f}金币"

        self.cash -= repay_amount
        loan.total_to_repay = 0
        self.loans.remove(loan)
        self._log("repay", f"偿还贷款本息{repay_amount:.2f}金币", -repay_amount)
        return True, f"成功偿还贷款本息{repay_amount:.2f}金币"

    def get_weekly_report(self):
        if self.day == 0:
            return "游戏尚未开始，无法生成周报"

        weekly_logs = [e for e in self.log if e.day > max(0, self.day - 7)]
        gross_profit = self.week_revenue - self.week_cost

        report_lines = []
        report_lines.append(f"╔══════════════════════════════════════════╗")
        report_lines.append(f"║        第{self.day}天 · 本周经营报告            ║")
        report_lines.append(f"╠══════════════════════════════════════════╣")
        report_lines.append(f"║ 总营收：{self.week_revenue:>8.2f} 金币               ║")
        report_lines.append(f"║ 总成本：{self.week_cost:>8.2f} 金币               ║")
        report_lines.append(f"║ 毛利润：{gross_profit:>8.2f} 金币               ║")
        report_lines.append(f"║ 当前现金：{self.cash:>8.2f} 金币            ║")
        report_lines.append(f"╠══════════════════════════════════════════╣")
        report_lines.append(f"║ 本周关键事件：                              ║")
        if self.weekly_log:
            for event in self.weekly_log[-5:]:
                report_lines.append(f"║ • {event[:36]:36s} ║")
        else:
            report_lines.append(f"║ （本周无交易活动）                        ║")
        report_lines.append(f"╚══════════════════════════════════════════╝")

        self.week_revenue = 0
        self.week_cost = 0
        self.weekly_log = []

        return "\n".join(report_lines)

    def get_finance_report(self):
        total_liabilities = sum(
            l.total_to_repay for l in self.loans if not l.is_paid_off
        )

        raw_value = self.inventory.total_inventory_value(
            material_prices=self.market.material_prices
        )
        product_prices = {}
        for p in config.PRODUCTS:
            base = sum(config.get_material_base_price(rid) * qty for rid, qty in p["recipe"].items())
            product_prices[p["id"]] = base
        prod_value = self.inventory.total_inventory_value(
            product_prices=product_prices
        )
        total_assets = self.cash + raw_value + prod_value
        net_worth = total_assets - total_liabilities

        lines = []
        lines.append(f"╔══════════════════════════════════════════════╗")
        lines.append(f"║              财务报表 · 第{self.day}天             ║")
        lines.append(f"╠══════════════════════════════════════════════╣")
        lines.append(f"║ 当前现金：{self.cash:>10.2f} 金币               ║")
        lines.append(f"║ 原材料库存价值：{raw_value:>8.2f} 金币            ║")
        lines.append(f"║ 产成品库存价值：{prod_value:>8.2f} 金币            ║")
        lines.append(f"║ 总资产：{total_assets:>10.2f} 金币               ║")
        lines.append(f"║ 总负债：{total_liabilities:>10.2f} 金币               ║")
        lines.append(f"║ ────────────────────────────────────────── ║")
        lines.append(f"║ 净资产：{net_worth:>10.2f} 金币               ║")
        lines.append(f"║ 声望值：{self.reputation:>6d}                          ║")
        lines.append(f"╚══════════════════════════════════════════════╝")
        return "\n".join(lines)

    def get_market_info(self):
        lines = []
        lines.append(f"╔══════════════════════════════════════════════╗")
        lines.append(f"║               市场信息 · 第{self.day}天            ║")
        lines.append(f"╠══════════════════════════════════════════════╣")
        lines.append(f"║ 【原材料市场价格】                            ║")
        for m in config.RAW_MATERIALS:
            price = self.market.get_material_price(m["id"])
            lines.append(f"║  {m['id']:4s} {m['name']:4s}    {price:>8.2f} 金币/{m['unit']}        ║")
        lines.append(f"╠══════════════════════════════════════════════╣")
        lines.append(f"║ 【零售商收购价格】                            ║")
        for r in config.RETAILERS:
            lines.append(f"║  ─ {r['name']}（{r['description']}）─     ║")
            for p in config.PRODUCTS:
                price = self.market.get_product_buy_price(p["id"], r["id"])
                trend = self.market.get_demand_trend_text(p["id"])
                lines.append(f"║    {p['id']:4s} {p['name']:4s}    {price:>8.2f} 金币         ║")
                lines.append(f"║    ↳ {trend[:38]:38s} ║")
        lines.append(f"╚══════════════════════════════════════════════╝")
        return "\n".join(lines)

    def get_inventory_info(self):
        lines = []
        lines.append(f"╔══════════════════════════════════════════════╗")
        lines.append(f"║                  库存清单                      ║")
        lines.append(f"╠══════════════════════════════════════════════╣")
        lines.append(f"║ 【原材料库存】                                ║")
        has_raw = False
        for m in config.RAW_MATERIALS:
            qty = self.inventory.get_raw_material_qty(m["id"])
            if qty > 0:
                has_raw = True
                entry = self.inventory.raw_materials[m["id"]]
                lines.append(f"║  {m['id']:4s} {m['name']:4s}    x{qty:<4d}  均价{entry['avg_cost']:>6.2f}金币 ║")
        if not has_raw:
            lines.append(f"║  （暂无原材料库存）                          ║")
        lines.append(f"╠══════════════════════════════════════════════╣")
        lines.append(f"║ 【产成品库存】                                ║")
        has_prod = False
        for p in config.PRODUCTS:
            qty = self.inventory.get_product_qty(p["id"])
            if qty > 0:
                has_prod = True
                entry = self.inventory.products[p["id"]]
                lines.append(f"║  {p['id']:4s} {p['name']:4s}    x{qty:<4d}  成本{entry['avg_cost']:>6.2f}金币 ║")
        if not has_prod:
            lines.append(f"║  （暂无产成品库存）                          ║")
        lines.append(f"╚══════════════════════════════════════════════╝")
        return "\n".join(lines)

    def get_log(self, limit=50):
        if not self.log:
            return "暂无经营日志"
        lines = []
        lines.append(f"╔══════════════════════════════════════════════╗")
        lines.append(f"║                经营日志                        ║")
        lines.append(f"╠══════════════════════════════════════════════╣")
        entries = self.log[-limit:]
        for entry in entries:
            amt = ""
            if entry.amount > 0:
                amt = f"+{entry.amount:.2f}"
            elif entry.amount < 0:
                amt = f"{entry.amount:.2f}"
            if amt:
                lines.append(f"║  Day{entry.day:3d} [{amt:>10s}] {entry.description[:34]:34s} ║")
            else:
                lines.append(f"║  Day{entry.day:3d}  {'':10s} {entry.description[:34]:34s} ║")
        lines.append(f"╚══════════════════════════════════════════════╝")
        return "\n".join(lines)

    def to_dict(self):
        return {
            "player_name": self.player_name,
            "cash": self.cash,
            "day": self.day,
            "reputation": self.reputation,
            "inventory": self.inventory.to_dict(),
            "loans": [l.to_dict() for l in self.loans],
            "log": [entry.to_dict() for entry in self.log],
            "market": self.market.to_dict(),
            "week_revenue": self.week_revenue,
            "week_cost": self.week_cost,
            "weekly_log": self.weekly_log,
        }

    @classmethod
    def from_dict(cls, data):
        gs = cls()
        gs.player_name = data.get("player_name", "")
        gs.cash = data.get("cash", 0)
        gs.day = data.get("day", 0)
        gs.reputation = data.get("reputation", 0)
        gs.inventory = Inventory.from_dict(data.get("inventory", {}))
        gs.loans = [Loan.from_dict(l) for l in data.get("loans", [])]
        gs.log = [LogEntry.from_dict(e) for e in data.get("log", [])]
        gs.market = Market.from_dict(data.get("market", {}))
        gs.week_revenue = data.get("week_revenue", 0)
        gs.week_cost = data.get("week_cost", 0)
        gs.weekly_log = data.get("weekly_log", [])
        return gs