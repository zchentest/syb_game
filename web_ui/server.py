import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from web_ui.game_room import create_room, get_room, save_room, load_all_rooms, get_player_games, get_room_summary
from syb_game import config

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


class SYBHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _send_static(self, filepath):
        ext = os.path.splitext(filepath)[1]
        mime_map = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "application/javascript; charset=utf-8", ".png": "image/png", ".jpg": "image/jpeg", ".ico": "image/x-icon"}
        try:
            with open(filepath, "rb") as f:
                self.send_response(200)
                self.send_header("Content-Type", mime_map.get(ext, "application/octet-stream"))
                self.end_headers()
                self.wfile.write(f.read())
        except FileNotFoundError:
            self._send_json({"error": "Not found"}, 404)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/" or path == "":
            idx = os.path.join(STATIC_DIR, "index.html")
            if os.path.exists(idx):
                self._send_static(idx)
            else:
                self._send_json({"error": "index.html not found"}, 404)
            return
        sf = os.path.join(STATIC_DIR, path.lstrip("/"))
        if os.path.exists(sf) and os.path.isfile(sf):
            self._send_static(sf)
            return
        self._send_json({"error": "Not found"}, 404)

    def _get_room_and_player(self, body, require_teacher=False):
        code = body.get("room_code", "").strip().upper()
        pid = body.get("player_id", "")
        room = get_room(code)
        if not room:
            return None, None, "房间不存在"
        player = room.get_player(pid)
        if not player:
            return None, None, "玩家不存在"
        if require_teacher and not player.is_teacher:
            return None, None, "仅老师可操作"
        return room, player, None

    def _check_day_action_allowed(self, room, player, action_type):
        if room.phase != "playing":
            return "游戏未开始"
        allowed = config.get_allowed_actions(room.day)
        if action_type not in allowed:
            sched = config.get_day_schedule(room.day)
            day_name = sched["name"] if sched else f"第{room.day}天"
            return f"今天是{day_name}，不能进行此操作"
        return None

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._read_body()

        if path == "/api/create_room":
            name = body.get("name", "").strip()
            if not name:
                self._send_json({"success": False, "message": "请输入教师名称"})
                return
            room = create_room(name)
            save_room(room)
            self._send_json({"success": True, "data": {"room_code": room.room_code, "player_id": room.teacher_id, "is_teacher": True, "room": room.to_dict(room.teacher_id)}})

        elif path == "/api/join_room":
            code = body.get("room_code", "").strip().upper()
            name = body.get("name", "").strip()
            if not code or not name:
                self._send_json({"success": False, "message": "请输入房间号和姓名"})
                return
            room = get_room(code)
            if not room:
                self._send_json({"success": False, "message": "房间不存在"})
                return
            if room.phase != "lobby":
                self._send_json({"success": False, "message": "游戏已开始，无法加入"})
                return
            pid = room.add_student(name)
            save_room(room)
            self._send_json({"success": True, "data": {"room_code": room.room_code, "player_id": pid, "is_teacher": False, "room": room.to_dict(pid)}})

        elif path == "/api/room_state":
            code = body.get("room_code", "").strip().upper()
            pid = body.get("player_id", "")
            room = get_room(code)
            if not room:
                self._send_json({"success": False, "message": "房间不存在"})
                return
            self._send_json({"success": True, "data": room.to_dict(pid)})

        elif path == "/api/reconnect":
            code = body.get("room_code", "").strip().upper()
            pid = body.get("player_id", "")
            room = get_room(code)
            if not room:
                self._send_json({"success": False, "message": "房间不存在"})
                return
            player = room.get_player(pid)
            if not player:
                self._send_json({"success": False, "message": "玩家身份已失效"})
                return
            self._send_json({"success": True, "data": {"room_code": room.room_code, "player_id": pid, "is_teacher": player.is_teacher, "room": room.to_dict(pid)}})

        elif path == "/api/my_games":
            pid = body.get("player_id", "")
            if not pid:
                self._send_json({"success": False, "message": "请提供玩家ID"})
                return
            games = get_player_games(pid)
            self._send_json({"success": True, "data": games})

        elif path == "/api/game_summary":
            code = body.get("room_code", "").strip().upper()
            summary = get_room_summary(code)
            if not summary:
                self._send_json({"success": False, "message": "房间不存在"})
                return
            self._send_json({"success": True, "data": summary})

        elif path == "/api/start_game":
            room, player, err = self._get_room_and_player(body, require_teacher=True)
            if err:
                self._send_json({"success": False, "message": err})
                return
            success, msg = room.start_game()
            if success:
                save_room(room)
            self._send_json({"success": success, "message": msg, "data": room.to_dict(player.player_id) if success else None})

        elif path == "/api/next_day":
            room, player, err = self._get_room_and_player(body, require_teacher=True)
            if err:
                self._send_json({"success": False, "message": err})
                return
            success, events = room.advance_day()
            if success:
                save_room(room)
            self._send_json({"success": success, "message": f"第{room.day}天" if success else "", "data": {"events": events if success else [], "room": room.to_dict(player.player_id)} if success else None})

        # === Student Actions (with day validation) ===
        elif path == "/api/buy_request":
            room, player, err = self._get_room_and_player(body)
            if err:
                self._send_json({"success": False, "message": err})
                return
            if player.is_teacher:
                self._send_json({"success": False, "message": "学生才能提交购买请求"})
                return
            day_err = self._check_day_action_allowed(room, player, "buy")
            if day_err:
                self._send_json({"success": False, "message": day_err})
                return
            quantity = int(body.get("quantity", 0))
            if quantity <= 0:
                self._send_json({"success": False, "message": "数量必须大于0"})
                return
            req = room.create_request("buy", player.player_id, {"quantity": quantity})
            if not req:
                self._send_json({"success": False, "message": "创建请求失败"})
                return
            save_room(room)
            self._send_json({"success": True, "message": f"已提交购买A4纸x{quantity}的请求，等待老师审批", "data": room.to_dict(player.player_id)})

        elif path == "/api/produce":
            room, player, err = self._get_room_and_player(body)
            if err:
                self._send_json({"success": False, "message": err})
                return
            if player.is_teacher:
                self._send_json({"success": False, "message": "学生才能生产"})
                return
            day_err = self._check_day_action_allowed(room, player, "produce")
            if day_err:
                self._send_json({"success": False, "message": day_err})
                return
            quantity = int(body.get("quantity", 0))
            if quantity <= 0:
                self._send_json({"success": False, "message": "数量必须大于0"})
                return
            player.current_day = room.day
            success, msg = player.produce(quantity)
            if success:
                save_room(room)
            self._send_json({"success": success, "message": msg, "data": room.to_dict(player.player_id) if success else None})

        elif path == "/api/sell_request":
            room, player, err = self._get_room_and_player(body)
            if err:
                self._send_json({"success": False, "message": err})
                return
            if player.is_teacher:
                self._send_json({"success": False, "message": "学生才能提交销售请求"})
                return
            day_err = self._check_day_action_allowed(room, player, "sell")
            if day_err:
                self._send_json({"success": False, "message": day_err})
                return
            quantity = int(body.get("quantity", 0))
            retailer_id = body.get("retailer_id", "RT2").upper()
            grade = body.get("grade", config.DEFAULT_GRADE).upper()
            if grade not in config.PRODUCT_GRADES:
                grade = config.DEFAULT_GRADE
            if quantity <= 0:
                self._send_json({"success": False, "message": "数量必须大于0"})
                return
            req = room.create_request("sell", player.player_id, {"quantity": quantity, "retailer_id": retailer_id, "grade": grade})
            if not req:
                gp=player.graded_products.get(grade,0)
                self._send_json({"success": False, "message": f"库存不足！当前{grade}级帽子仅有{gp}顶，无法提交{grade}级x{quantity}的出售请求"})
                return
            save_room(room)
            self._send_json({"success": True, "message": f"已提交出售{grade}级帽子x{quantity}的请求，等待老师审批", "data": room.to_dict(player.player_id)})

        elif path == "/api/shop_request":
            room, player, err = self._get_room_and_player(body)
            if err:
                self._send_json({"success": False, "message": err})
                return
            if player.is_teacher:
                self._send_json({"success": False, "message": "学生才能购买"})
                return
            day_err = self._check_day_action_allowed(room, player, "shop")
            if day_err:
                self._send_json({"success": False, "message": day_err})
                return
            item_id = body.get("item_id", "").upper()
            if not config.get_shop_item(item_id):
                self._send_json({"success": False, "message": "商品不存在"})
                return
            req = room.create_request("shop", player.player_id, {"item_id": item_id})
            if not req:
                self._send_json({"success": False, "message": "创建请求失败"})
                return
            save_room(room)
            self._send_json({"success": True, "message": "已提交购买请求，等待老师审批", "data": room.to_dict(player.player_id)})

        elif path == "/api/loan":
            room, player, err = self._get_room_and_player(body)
            if err:
                self._send_json({"success": False, "message": err})
                return
            if player.is_teacher:
                self._send_json({"success": False, "message": "学生才能贷款"})
                return
            day_err = self._check_day_action_allowed(room, player, "loan")
            if day_err:
                self._send_json({"success": False, "message": day_err})
                return
            amount = float(body.get("amount", 0))
            if amount <= 0:
                self._send_json({"success": False, "message": "金额必须大于0"})
                return
            player.current_day = room.day
            success, msg = player.take_loan(amount)
            if success:
                save_room(room)
            self._send_json({"success": success, "message": msg, "data": room.to_dict(player.player_id) if success else None})

        elif path == "/api/repay":
            room, player, err = self._get_room_and_player(body)
            if err:
                self._send_json({"success": False, "message": err})
                return
            if player.is_teacher:
                self._send_json({"success": False, "message": "学生才能还款"})
                return
            day_err = self._check_day_action_allowed(room, player, "repay")
            if day_err:
                self._send_json({"success": False, "message": day_err})
                return
            player.current_day = room.day
            success, msg = player.repay_loan()
            if success:
                save_room(room)
            self._send_json({"success": success, "message": msg, "data": room.to_dict(player.player_id) if success else None})

        # === Teacher Actions ===
        elif path == "/api/approve_request":
            room, player, err = self._get_room_and_player(body, require_teacher=True)
            if err:
                self._send_json({"success": False, "message": err})
                return
            req_id = body.get("request_id", "")
            if not req_id:
                self._send_json({"success": False, "message": "请指定请求ID"})
                return
            success, msg = room.approve_request(req_id)
            if success:
                save_room(room)
            self._send_json({"success": success, "message": msg, "data": room.to_dict(player.player_id) if success else None})

        elif path == "/api/reject_request":
            room, player, err = self._get_room_and_player(body, require_teacher=True)
            if err:
                self._send_json({"success": False, "message": err})
                return
            req_id = body.get("request_id", "")
            success, msg = room.reject_request(req_id)
            save_room(room)
            self._send_json({"success": success, "message": msg, "data": room.to_dict(player.player_id)})

        elif path == "/api/grade_products":
            room, player, err = self._get_room_and_player(body, require_teacher=True)
            if err:
                self._send_json({"success": False, "message": err})
                return
            target_id = body.get("target_player_id", "")
            quantity = int(body.get("quantity", 0))
            grade = body.get("grade", "B").upper()
            if grade not in config.PRODUCT_GRADES:
                self._send_json({"success": False, "message": f"无效评级，可选：{','.join(config.PRODUCT_GRADES.keys())}"})
                return
            if quantity <= 0:
                self._send_json({"success": False, "message": "数量必须大于0"})
                return
            success, msg = room.grade_products(target_id, quantity, grade)
            if success:
                save_room(room)
            self._send_json({"success": success, "message": msg, "data": room.to_dict(player.player_id) if success else None})

        elif path == "/api/issue_scenario":
            room, player, err = self._get_room_and_player(body, require_teacher=True)
            if err:
                self._send_json({"success": False, "message": err})
                return
            card_id = body.get("card_id", "")
            target_id = body.get("target_player_id", "")
            note = body.get("note", "")
            success, msg = room.issue_scenario(card_id, target_id, note)
            if success:
                save_room(room)
            self._send_json({"success": success, "message": msg, "data": room.to_dict(player.player_id) if success else None})

        elif path == "/api/teacher_collect":
            room, player, err = self._get_room_and_player(body, require_teacher=True)
            if err:
                self._send_json({"success": False, "message": err})
                return
            target_id = body.get("target_player_id", "")
            amount = float(body.get("amount", 0))
            reason = body.get("reason", "")
            if amount <= 0:
                self._send_json({"success": False, "message": "金额必须大于0"})
                return
            success, msg = room.teacher_collect(target_id, amount, reason)
            if success:
                save_room(room)
            self._send_json({"success": success, "message": msg, "data": room.to_dict(player.player_id) if success else None})

        elif path == "/api/teacher_give":
            room, player, err = self._get_room_and_player(body, require_teacher=True)
            if err:
                self._send_json({"success": False, "message": err})
                return
            target_id = body.get("target_player_id", "")
            amount = float(body.get("amount", 0))
            reason = body.get("reason", "")
            if amount <= 0:
                self._send_json({"success": False, "message": "金额必须大于0"})
                return
            success, msg = room.teacher_give(target_id, amount, reason)
            if success:
                save_room(room)
            self._send_json({"success": success, "message": msg, "data": room.to_dict(player.player_id) if success else None})

        else:
            self._send_json({"error": "Unknown endpoint"}, 404)

    def log_message(self, format, *args):
        pass


def run_server(port=5000):
    loaded = load_all_rooms()
    server = HTTPServer(("0.0.0.0", port), SYBHandler)
    print(f"╔══════════════════════════════════════════════════════╗")
    print(f"║    SYB 沙盘模拟 · 课堂教学版                        ║")
    print(f"║                                                    ║")
    print(f"║  → http://localhost:{port}                        ║")
    print(f"║                                                    ║")
    print(f"║  已加载 {loaded} 个历史游戏记录                      ║")
    print(f"║  【重要】游戏数据自动保存，刷新不丢失                ║")
    print(f"║  【限制】对应日子只能做对应操作                      ║")
    print(f"║  周周期：周一采购 周二生产 周三销售 周四贷款         ║")
    print(f"║          周五计划 周六消费 周日休息                 ║")
    print(f"║                                                    ║")
    print(f"║  按 Ctrl+C 停止服务器                                ║")
    print(f"╚══════════════════════════════════════════════════════╝")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")


if __name__ == "__main__":
    run_server()