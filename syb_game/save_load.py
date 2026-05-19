import json
import os
from syb_game import config
from syb_game.game_state import GameState


def save_game(state, save_name):
    if not os.path.exists(config.SAVES_DIR):
        os.makedirs(config.SAVES_DIR)

    filename = f"{save_name}.json"
    filepath = os.path.join(config.SAVES_DIR, filename)

    data = state.to_dict()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return filepath


def load_game(save_name):
    filename = f"{save_name}.json"
    filepath = os.path.join(config.SAVES_DIR, filename)

    if not os.path.exists(filepath):
        return None, f"存档文件不存在：{filepath}"

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return None, f"存档文件损坏：{e}"

    state = GameState.from_dict(data)
    return state, f"成功加载存档 [{save_name}]，当前玩家：{state.player_name}，第{state.day}天"


def list_saves():
    if not os.path.exists(config.SAVES_DIR):
        return []

    saves = []
    for f in os.listdir(config.SAVES_DIR):
        if f.endswith(".json"):
            save_name = f[:-5]
            filepath = os.path.join(config.SAVES_DIR, f)
            mtime = os.path.getmtime(filepath)
            try:
                with open(filepath, "r", encoding="utf-8") as sf:
                    data = json.load(sf)
                info = {
                    "name": save_name,
                    "player": data.get("player_name", "未知"),
                    "day": data.get("day", 0),
                    "cash": data.get("cash", 0),
                    "mtime": mtime,
                }
            except Exception:
                info = {
                    "name": save_name,
                    "player": "损坏",
                    "day": 0,
                    "cash": 0,
                    "mtime": mtime,
                }
            saves.append(info)

    saves.sort(key=lambda s: s["mtime"], reverse=True)
    return saves