import random
import string
import time
from syb_game import config
from syb_game.config import (
    get_material_name, get_product_name, get_product_info,
    get_material_base_price, get_retailer_info,
    get_grade_info, get_grade_price, get_day_schedule,
    get_allowed_actions, get_shop_item, get_scenario_card
)


class Market:
    def __init__(self):
        self.material_prices = {}
        self.retailer_product_prices = {}
        self.demand_trends = {}
        self._init_prices()

    def _init_prices(self):
        random.seed()
        for m in config.RAW_MATERIALS:
            variance = random.uniform(-0.1, 0.1)
            self.material_prices[m["id"]] = round(m["base_price"] * (1 + variance), 2)
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
                price = round(base_product_cost * r["price_multiplier"] * (1 + change), 2)
                self.retailer_product_prices[p["id"]][r["id"]] = price

    def get_material_price(self, material_id):
        return self.material_prices.get(material_id, config.get_material_base_price(material_id))

    def get_product_buy_price(self, product_id, retailer_id):
        return self.retailer_product_prices.get(product_id, {}).get(retailer_id, 0)

    def get_demand_trend_text(self, product_id):
        info = config.get_product_info(product_id)
        if not info:
            return ""
        trend_idx = self.demand_trends.get(product_id, 1)
        return config.DEMAND_TRENDS[trend_idx].format(product=info["name"])


class Loan:
    def __init__(self, amount):
        self.amount = amount
        self.interest_rate = config.LOAN_DAILY_INTEREST_RATE
        self.days_remaining = config.LOAN_DEFAULT_DAYS
        self.total_to_repay = amount * (1 + self.interest_rate * self.days_remaining)

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


class PlayerState:
    def __init__(self, player_id, name, is_teacher=False):
        self.player_id = player_id
        self.name = name
        self.is_teacher = is_teacher
        self.cash = config.INITIAL_CASH
        self.reputation = config.INITIAL_REPUTATION
        self.raw_materials = 0
        self.products = 0
        self.product_avg_cost = 0
        self.loans = []
        self.log = []
        self.pending_products = 0
        self.graded_products = {"A": 0, "B": 0, "C": 0, "D": 0}
        self.shop_items = []
        self.current_day = 0

    def _log(self, day, entry_type, description, amount=0):
        self.log.append({
            "day": day, "type": entry_type,
            "description": description, "amount": amount
        })

    def buy_raw_material(self, material_id, quantity, unit_price):
        total_cost = unit_price * quantity
        if self.cash < total_cost:
            return False, f"现金不足！需要{total_cost:.2f}，当前只有{self.cash:.2f}"
        self.cash -= total_cost
        self.raw_materials += quantity
        name = config.get_material_name(material_id)
        self._log(self.current_day, "buy", f"购买 {name}x{quantity}，单价{unit_price:.2f}，总价{total_cost:.2f}", -total_cost)
        return True, f"成功购买 {name}x{quantity}，花费{total_cost:.2f}"

    def produce(self, quantity):
        if self.raw_materials < quantity:
            return False, f"A4纸不足！需要{quantity}张，当前仅有{self.raw_materials}"
        self.raw_materials -= quantity
        cost_per_unit = config.get_material_base_price("RC")
        new_avg = ((self.products * self.product_avg_cost) + (quantity * cost_per_unit)) / (self.products + quantity) if (self.products + quantity) > 0 else cost_per_unit
        self.products += quantity
        self.product_avg_cost = new_avg
        self.pending_products += quantity
        self._log(self.current_day, "produce", f"生产帽子x{quantity}，等待老师检验评级", 0)
        return True, f"成功生产帽子x{quantity}，请找老师检验评级"

    def sell(self, quantity, grade_price, grade="B"):
        if self.products < quantity:
            return False, f"帽子库存不足！当前仅有{self.products}顶"
        graded_at_grade = self.graded_products.get(grade, 0)
        if graded_at_grade < quantity:
            return False, f"{grade}级帽子库存不足！当前仅有{graded_at_grade}顶"
        total_revenue = grade_price * quantity
        cost = self.product_avg_cost * quantity
        profit = total_revenue - cost
        self.cash += total_revenue
        self.products -= quantity
        self.graded_products[grade] = graded_at_grade - quantity
        self._log(self.current_day, "sell", f"出售{grade}级帽子x{quantity}，收入{total_revenue:.2f}，利润{profit:.2f}", total_revenue)
        if profit > 0:
            self.reputation += max(1, int(profit / 50))
        return True, f"成功出售{grade}级帽子x{quantity}，收入{total_revenue:.2f}"

    def take_loan(self, amount):
        if amount <= 0:
            return False, "贷款金额必须大于0"
        max_loan = self.cash * config.LOAN_MAX_MULTIPLIER
        if amount > max_loan:
            return False, f"最大可贷额度为{max_loan:.2f}"
        loan = Loan(amount)
        self.loans.append(loan)
        self.cash += amount
        self._log(self.current_day, "loan", f"获得贷款{amount:.2f}，{config.LOAN_DEFAULT_DAYS}天周期", amount)
        return True, f"贷款成功！获得{amount:.2f}"

    def repay_loan(self):
        active = [l for l in self.loans if not l.is_paid_off]
        if not active:
            return False, "没有未还贷款"
        active.sort(key=lambda l: l.days_remaining)
        loan = active[0]
        repay_amount = loan.total_to_repay
        if self.cash < repay_amount:
            return False, f"现金不足！需要{repay_amount:.2f}"
        self.cash -= repay_amount
        loan.total_to_repay = 0
        self.loans.remove(loan)
        self._log(self.current_day, "repay", f"偿还贷款本息{repay_amount:.2f}", -repay_amount)
        return True, f"成功偿还贷款"

    def buy_shop_item(self, item_id):
        item = config.get_shop_item(item_id)
        if not item:
            return False, "商品不存在"
        if self.cash < item["price"]:
            return False, f"现金不足！需要{item['price']}金币买{item['name']}"
        self.cash -= item["price"]
        self.shop_items.append(item_id)
        self._log(self.current_day, "shop", f"从诚信商店购买 {item['emoji']}{item['name']}，花费{item['price']}金币", -item["price"])
        return True, f"成功购买 {item['emoji']}{item['name']}，花费{item['price']}金币"

    def apply_daily_costs(self, day):
        cost = config.FIXED_COST_TOTAL
        self.cash -= cost
        self._log(day, "expense", f"支付固定开销{cost}金币", -cost)
        events = [f"支付固定开销 {cost} 金币"]
        interest_total = 0
        for loan in self.loans[:]:
            if not loan.is_paid_off:
                interest = loan.apply_daily_interest()
                interest_total += interest
        if interest_total > 0:
            events.append(f"贷款利息 {interest_total:.2f}")
        return events

    @property
    def total_liabilities(self):
        return sum(l.total_to_repay for l in self.loans if not l.is_paid_off)

    @property
    def total_assets(self):
        raw_val = self.raw_materials * config.get_material_base_price("RC")
        prod_val = self.products * self.product_avg_cost
        return self.cash + raw_val + prod_val

    @property
    def net_worth(self):
        return self.total_assets - self.total_liabilities

    def to_dict(self):
        return {
            "player_id": self.player_id,
            "name": self.name,
            "is_teacher": self.is_teacher,
            "cash": self.cash,
            "reputation": self.reputation,
            "raw_materials": self.raw_materials,
            "products": self.products,
            "pending_products": self.pending_products,
            "graded_products": dict(self.graded_products),
            "product_avg_cost": round(self.product_avg_cost, 2),
            "liabilities": round(self.total_liabilities, 2),
            "net_worth": round(self.net_worth, 2),
        }


class PendingRequest:
    def __init__(self, req_id, req_type, player_id, player_name, data):
        self.id = req_id
        self.type = req_type
        self.player_id = player_id
        self.player_name = player_name
        self.data = data
        self.status = "pending"

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "player_id": self.player_id,
            "player_name": self.player_name,
            "data": self.data,
            "status": self.status,
        }


def generate_room_code():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=4))


class GameRoom:
    def __init__(self, room_code, teacher_name):
        self.room_code = room_code
        self.day = 0
        self.phase = "lobby"
        self.market = Market()
        self.players = {}
        self.teacher_id = None
        self.pending_requests = []
        self.scenario_log = []
        self.created_at = time.time()
        self.last_event = ""

        teacher_id = self._generate_player_id()
        teacher = PlayerState(teacher_id, teacher_name, is_teacher=True)
        self.players[teacher_id] = teacher
        self.teacher_id = teacher_id

    def _generate_player_id(self):
        chars = string.ascii_lowercase + string.digits
        while True:
            pid = ''.join(random.choices(chars, k=8))
            if pid not in self.players:
                return pid

    def add_student(self, name):
        pid = self._generate_player_id()
        player = PlayerState(pid, name)
        self.players[pid] = player
        return pid

    def get_player(self, player_id):
        return self.players.get(player_id)

    def start_game(self):
        if self.phase != "lobby":
            return False, "游戏已开始"
        self.phase = "playing"
        self.day = 0
        self.last_event = "游戏开始！"
        return True, "游戏开始！"

    def advance_day(self):
        if self.phase == "ended":
            return False, "🎉 游戏已结束，所有天数已完成"
        if self.phase != "playing":
            return False, "游戏未开始"
        self.day += 1
        all_events = []
        schedule = config.get_day_schedule(self.day)
        day_name = schedule["name"] if schedule else f"第{self.day}天"
        day_action = schedule["action"] if schedule else ""
        all_events.insert(0, f"📅 {day_name} · {day_action}")

        for pid, player in self.players.items():
            if not player.is_teacher:
                evts = player.apply_daily_costs(self.day)
                all_events.extend([f"[{player.name}] {e}" for e in evts])

        self.market.update_prices()
        self.last_event = f"第{self.day}天 ({day_name})"
        if self.day >= config.GAME_DAYS:
            self.phase = "ended"
            all_events.append(f"🎉 游戏结束！{config.GAME_DAYS}天已到")
            winner = self.get_leaderboard()[0]
            net = winner.get('net_worth', winner['cash'])
            all_events.append(f"🏆 冠军：{winner['name']} | 现金：{winner['cash']:.0f}💰 | 净资产：{net:.0f}💰")
        return True, all_events

    def get_allowed_actions_for_student(self):
        if self.phase == "lobby":
            return []
        return config.get_allowed_actions(self.day)

    def create_request(self, req_type, player_id, data):
        player = self.players.get(player_id)
        if not player or player.is_teacher:
            return None
        # Validate sell request - check graded product availability
        if req_type == "sell":
            grade = data.get("grade", config.DEFAULT_GRADE).upper()
            quantity = int(data.get("quantity", 0))
            available = player.graded_products.get(grade, 0)
            if available < quantity:
                return None
        req_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        req = PendingRequest(req_id, req_type, player_id, player.name, data)
        self.pending_requests.append(req)
        return req

    def approve_request(self, req_id):
        req = next((r for r in self.pending_requests if r.id == req_id and r.status == "pending"), None)
        if not req:
            return False, "请求不存在或已处理"
        player = self.players.get(req.player_id)
        if not player:
            return False, "玩家不存在"
        player.current_day = self.day

        if req.type == "buy":
            quantity = req.data.get("quantity", 0)
            unit_price = self.market.get_material_price("RC")
            success, msg = player.buy_raw_material("RC", quantity, unit_price)
            if success:
                req.status = "approved"
                return True, f"批准 {player.name} 购买A4纸x{quantity}"
            return False, msg

        elif req.type == "sell":
            quantity = req.data.get("quantity", 0)
            grade = req.data.get("grade", config.DEFAULT_GRADE)
            retailer_id = req.data.get("retailer_id", "RT2")
            base_price = self.market.get_product_buy_price("CP", retailer_id)
            grade_price = config.get_grade_price(base_price, grade)
            success, msg = player.sell(quantity, grade_price, grade)
            if success:
                req.status = "approved"
                return True, f"批准 {player.name} 出售{grade}级帽子x{quantity}，单价{grade_price:.2f}"
            return False, msg

        elif req.type == "shop":
            item_id = req.data.get("item_id", "")
            success, msg = player.buy_shop_item(item_id)
            if success:
                req.status = "approved"
                item = config.get_shop_item(item_id)
                return True, f"批准 {player.name} 购买 {item['emoji']}{item['name']}"
            return False, msg

        return False, "未知请求类型"

    def reject_request(self, req_id):
        req = next((r for r in self.pending_requests if r.id == req_id and r.status == "pending"), None)
        if not req:
            return False, "请求不存在或已处理"
        req.status = "rejected"
        return True, f"已拒绝 {req.player_name} 的请求"

    def grade_products(self, player_id, quantity, grade):
        player = self.players.get(player_id)
        if not player or player.is_teacher:
            return False, "玩家不存在"
        if player.pending_products < quantity:
            return False, f"该玩家待检验的帽子不足{quantity}顶"
        player.pending_products -= quantity
        player.graded_products[grade] = player.graded_products.get(grade, 0) + quantity
        grade_info = config.get_grade_info(grade)
        player._log(self.day, "grade", f"老师检验帽子x{quantity}，评级：{grade_info['label']}（{grade}级）", 0)
        return True, f"{player.name}的帽子x{quantity} 评级为 {grade_info['label']}（{grade}级）"

    def issue_scenario(self, card_id, target_player_id, note=""):
        card = config.get_scenario_card(card_id)
        if not card:
            return False, "情景卡不存在"
        player = self.players.get(target_player_id)
        if not player or player.is_teacher:
            return False, "玩家不存在"
        player.cash += card["amount"]
        card_type_cn = "奖励" if card["type"] == "reward" else "惩罚"
        player._log(self.day, "scenario", f"老师发放情景卡「{card['name']}」：{card['desc']}（{card_type_cn}{card['amount']}金币）", card["amount"])
        record = {
            "day": self.day,
            "card": card,
            "target": player.name,
            "target_id": target_player_id,
            "note": note,
            "time": time.time(),
        }
        self.scenario_log.append(record)
        return True, f"向 {player.name} 发放情景卡「{card['name']}」{card_type_cn}{card['amount']}金币"

    def teacher_collect(self, player_id, amount, reason=""):
        player = self.players.get(player_id)
        if not player or player.is_teacher:
            return False, "玩家不存在"
        if player.cash < amount:
            return False, f"{player.name}现金不足，仅有{player.cash:.2f}"
        player.cash -= amount
        teacher = self.players.get(self.teacher_id)
        if teacher:
            teacher.cash += amount
        player._log(self.day, "collect", f"老师收取{amount:.2f}金币{'（'+reason+'）' if reason else ''}", -amount)
        return True, f"已收取 {player.name} {amount:.2f}金币"

    def teacher_give(self, player_id, amount, reason=""):
        player = self.players.get(player_id)
        if not player or player.is_teacher:
            return False, "玩家不存在"
        player.cash += amount
        teacher = self.players.get(self.teacher_id)
        if teacher:
            teacher.cash -= amount
        player._log(self.day, "give", f"老师发放{amount:.2f}金币{'（'+reason+'）' if reason else ''}", amount)
        return True, f"已发放 {player.name} {amount:.2f}金币"

    def get_leaderboard(self):
        students = [p for p in self.players.values() if not p.is_teacher]
        sorted_players = sorted(students, key=lambda p: p.cash, reverse=True)
        return [p.to_dict() for p in sorted_players]

    def to_dict(self, for_player_id=None):
        player = self.players.get(for_player_id) if for_player_id else None
        is_teacher_view = player and player.is_teacher
        schedule = config.get_day_schedule(self.day)

        data = {
            "room_code": self.room_code,
            "day": self.day,
            "phase": self.phase,
            "max_days": config.GAME_DAYS,
            "teacher_id": self.teacher_id,
            "player_count": len([p for p in self.players.values() if not p.is_teacher]),
            "players": [p.to_dict() for p in self.players.values()],
            "leaderboard": self.get_leaderboard(),
            "last_event": self.last_event,
            "market": self._market_dict(),
            "schedule": {
                "weekday": schedule["name"] if schedule else "",
                "action": schedule["action"] if schedule else "",
                "desc": schedule["desc"] if schedule else "",
                "allowed": schedule["allowed"] if schedule else [],
            } if schedule else None,
        }

        if is_teacher_view:
            data["pending_requests"] = []
            for r in self.pending_requests:
                if r.status != "pending":
                    continue
                rd = r.to_dict()
                if r.type == "sell":
                    target = self.players.get(r.player_id)
                    if target and not target.is_teacher:
                        rd["graded_products"] = dict(target.graded_products)
                        rd["grade_prices"] = {}
                        retailer_id = r.data.get("retailer_id", "RT2")
                        base_price = self.market.get_product_buy_price("CP", retailer_id)
                        for g in config.PRODUCT_GRADES:
                            rd["grade_prices"][g] = round(config.get_grade_price(base_price, g), 2)
                data["pending_requests"].append(rd)
            data["scenario_cards"] = [c for c in config.SCENARIO_CARDS]
            data["honesty_shop"] = config.HONESTY_SHOP
            data["product_grades"] = {k: v for k, v in config.PRODUCT_GRADES.items()}
            data["scenario_log"] = self.scenario_log[-20:]
            students_with_pending = []
            for p in self.players.values():
                if not p.is_teacher and p.pending_products > 0:
                    students_with_pending.append(p.to_dict())
            data["pending_grading"] = students_with_pending
            students_all = [p.to_dict() for p in self.players.values() if not p.is_teacher]
            data["all_students"] = students_all

        if for_player_id and player:
            data["me"] = player.to_dict()
            data["my_log"] = player.log[-30:]
            if not is_teacher_view:
                data["allowed_actions"] = config.get_allowed_actions(self.day)
                data["schedule"] = {
                    "weekday": schedule["name"] if schedule else "",
                    "action": schedule["action"] if schedule else "",
                    "desc": schedule["desc"] if schedule else "",
                } if schedule else None
                data["my_pending_requests"] = [
                    r.to_dict() for r in self.pending_requests
                    if r.player_id == for_player_id
                ]
                data["honesty_shop"] = config.HONESTY_SHOP

        return data

    def _market_dict(self):
        materials = []
        for m in config.RAW_MATERIALS:
            materials.append({
                "id": m["id"], "name": m["name"],
                "price": self.market.get_material_price(m["id"]),
            })
        retailers = []
        for r in config.RETAILERS:
            products = []
            for p in config.PRODUCTS:
                price = self.market.get_product_buy_price(p["id"], r["id"])
                products.append({
                    "id": p["id"], "name": p["name"],
                    "price": price,
                    "trend": self.market.get_demand_trend_text(p["id"]),
                })
            retailers.append({
                "id": r["id"], "name": r["name"],
                "description": r["description"],
                "products": products,
            })
        return {"materials": materials, "retailers": retailers}


_rooms = {}

def create_room(teacher_name):
    while True:
        code = generate_room_code()
        if code not in _rooms:
            break
    room = GameRoom(code, teacher_name)
    _rooms[code] = room
    return room

def get_room(room_code):
    return _rooms.get(room_code)

def cleanup_old_rooms(max_age=3600):
    now = time.time()
    to_remove = [code for code, room in _rooms.items() if now - room.created_at > max_age]
    for code in to_remove:
        del _rooms[code]


# === Persistence (Save/Load) ===

import json
import os

SAVES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves", "rooms")


def _ensure_saves_dir():
    os.makedirs(SAVES_DIR, exist_ok=True)


def _room_to_dict(room):
    players_dict = {}
    for pid, p in room.players.items():
        players_dict[pid] = {
            "player_id": p.player_id,
            "name": p.name,
            "is_teacher": p.is_teacher,
            "cash": p.cash,
            "reputation": p.reputation,
            "raw_materials": p.raw_materials,
            "products": p.products,
            "product_avg_cost": p.product_avg_cost,
            "pending_products": p.pending_products,
            "graded_products": dict(p.graded_products),
            "shop_items": list(p.shop_items),
            "current_day": p.current_day,
            "loans": [{"amount": l.amount, "interest_rate": l.interest_rate, "days_remaining": l.days_remaining, "total_to_repay": l.total_to_repay} for l in p.loans],
            "log": list(p.log),
        }
    return {
        "room_code": room.room_code,
        "day": room.day,
        "phase": room.phase,
        "teacher_id": room.teacher_id,
        "created_at": room.created_at,
        "last_event": room.last_event,
        "players": players_dict,
        "pending_requests": [{"id": r.id, "type": r.type, "player_id": r.player_id, "player_name": r.player_name, "data": dict(r.data), "status": r.status} for r in room.pending_requests],
        "scenario_log": list(room.scenario_log),
        "market": {
            "material_prices": dict(room.market.material_prices),
            "retailer_product_prices": {k: dict(v) for k, v in room.market.retailer_product_prices.items()},
            "demand_trends": dict(room.market.demand_trends),
        },
    }


def _dict_to_room(data):
    room = GameRoom.__new__(GameRoom)
    room.room_code = data["room_code"]
    room.day = data["day"]
    room.phase = data["phase"]
    room.teacher_id = data["teacher_id"]
    room.created_at = data["created_at"]
    room.last_event = data.get("last_event", "")
    room.players = {}
    room.pending_requests = []
    room.scenario_log = list(data.get("scenario_log", []))

    # Restore market
    room.market = Market.__new__(Market)
    room.market.material_prices = dict(data["market"]["material_prices"])
    room.market.retailer_product_prices = {}
    for k, v in data["market"]["retailer_product_prices"].items():
        room.market.retailer_product_prices[k] = dict(v)
    room.market.demand_trends = dict(data["market"]["demand_trends"])

    # Restore players
    for pid, pdata in data["players"].items():
        player = PlayerState.__new__(PlayerState)
        player.player_id = pdata["player_id"]
        player.name = pdata["name"]
        player.is_teacher = pdata["is_teacher"]
        player.cash = pdata["cash"]
        player.reputation = pdata["reputation"]
        player.raw_materials = pdata["raw_materials"]
        player.products = pdata["products"]
        player.product_avg_cost = pdata["product_avg_cost"]
        player.pending_products = pdata["pending_products"]
        player.graded_products = dict(pdata.get("graded_products", {"A": 0, "B": 0, "C": 0, "D": 0}))
        player.shop_items = list(pdata.get("shop_items", []))
        player.current_day = pdata.get("current_day", 0)
        player.loans = []
        for ld in pdata.get("loans", []):
            loan = Loan.__new__(Loan)
            loan.amount = ld["amount"]
            loan.interest_rate = ld["interest_rate"]
            loan.days_remaining = ld["days_remaining"]
            loan.total_to_repay = ld["total_to_repay"]
            player.loans.append(loan)
        player.log = list(pdata.get("log", []))
        room.players[pid] = player

    # Restore pending requests
    for rd in data.get("pending_requests", []):
        req = PendingRequest.__new__(PendingRequest)
        req.id = rd["id"]
        req.type = rd["type"]
        req.player_id = rd["player_id"]
        req.player_name = rd["player_name"]
        req.data = dict(rd["data"])
        req.status = rd["status"]
        room.pending_requests.append(req)

    return room


def save_room(room):
    _ensure_saves_dir()
    filepath = os.path.join(SAVES_DIR, f"{room.room_code}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(_room_to_dict(room), f, ensure_ascii=False, indent=2)


def load_room(room_code):
    filepath = os.path.join(SAVES_DIR, f"{room_code}.json")
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return _dict_to_room(data)


def load_all_rooms():
    _ensure_saves_dir()
    count = 0
    for fname in os.listdir(SAVES_DIR):
        if fname.endswith(".json"):
            code = fname[:-5]
            room = load_room(code)
            if room and code not in _rooms:
                _rooms[code] = room
                count += 1
    return count


def get_player_games(player_id):
    games = []
    for code, room in _rooms.items():
        if player_id in room.players:
            player = room.players[player_id]
            games.append({
                "room_code": code,
                "player_name": player.name,
                "is_teacher": player.is_teacher,
                "phase": room.phase,
                "day": room.day,
                "max_days": config.GAME_DAYS,
                "created_at": room.created_at,
                "player_cash": player.cash,
            })
    games.sort(key=lambda g: g["created_at"], reverse=True)
    return games


def get_room_summary(room_code):
    room = _rooms.get(room_code)
    if not room:
        return None
    students = [p.to_dict() for p in room.players.values() if not p.is_teacher]
    return {
        "room_code": room.room_code,
        "phase": room.phase,
        "day": room.day,
        "max_days": config.GAME_DAYS,
        "teacher_name": room.players[room.teacher_id].name if room.teacher_id in room.players else "",
        "student_count": len(students),
        "students": students,
        "scenario_log": room.scenario_log[-50:],
        "created_at": room.created_at,
    }