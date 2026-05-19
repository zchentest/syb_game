---
title: SYB 沙盘模拟 · 课堂教学版
emoji: 🎲
colorFrom: indigo
colorTo: blue
sdk: docker
pinned: false
---

# SYB 沙盘模拟 · 课堂教学版

> **零依赖 · 浏览器即开即用 · 专为创业培训课堂设计**

本系统使用 [Trae](https://trae.ai) AI 编程助手开发，是一款**完全免费的创业培训沙盘模拟教学工具**。教师和学生只需打开浏览器，即可开展一堂生动的企业经营模拟课。

---

## 功能特色

### 🎯 双角色设计
- **教师端**：创建教室、控制游戏进度、审批学生请求、检验帽子评级、发放/收取金币、发放情景卡
- **学生端**：加入教室、购买原料(A4纸)、生产帽子、按等级出售产品、贷款/还款、诚信商店消费

### 📅 周周期经营
| 星期 | 活动 | 说明 |
|------|------|------|
| 周一 | 采购日 | 购买 A4 纸原料 |
| 周二 | 生产日 | 制作帽子 |
| 周三 | 销售日 | 出售帽子（需老师审批） |
| 周四 | 收款/贷款日 | 申请或偿还贷款 |
| 周五 | 计划日 | 制定下周计划 |
| 周六 | 消费日 | 诚信商店购物 |
| 周日 | 休息日 | 无经营活动 |

### 🏆 产品分级
学生制作的帽子由老师检验评级：
- **A级（优秀）** × 1.5 倍售价
- **B级（良好）** × 1.2 倍售价
- **C级（合格）** × 0.8 倍售价
- **D级（待改进）** × 0.5 倍售价

### 🎴 情景卡系统
老师可根据学生表现发放情景卡（奖励或惩罚），即时增减现金。

### 🏪 诚信商店
可乐🥤、冰淇淋🍦、薯片🥨、棒棒糖🍭、矿泉水💧、巧克力🍫、饼干🍪

---

## 快速开始

### 本地运行

#### 方法一：Git Bash / Linux / macOS

```bash
cd syb-game
python web_ui/server.py
```

#### 方法二：Windows 双击脚本

直接双击 `syb.bat`

#### 方法三：Docker

```bash
docker build -t syb-game .
docker run -p 5000:5000 syb-game
```

启动后浏览器访问 `http://localhost:5000`

---

## 部署到云端

### 方案一：Hugging Face Spaces（推荐 - 最稳定免费）

1. 在 [huggingface.co](https://huggingface.co) 注册账号
2. 点击右上角头像 → New Space
3. 选择 **Docker** 作为 Space SDK
4. 将本仓库代码上传（或关联 GitHub 仓库）
5. 项目已预置 `Dockerfile`，Spaces 会自动构建
6. 部署完成后即可通过 `https://你的用户名-syb-game.hf.space` 访问

**免费额度**：2 vCPU、16GB RAM、50GB 磁盘，无需绑定信用卡

### 方案二：Zeabur（中国大陆访问最佳）

1. 在 [zeabur.com](https://zeabur.com) 注册（支持 GitHub 登录）
2. 创建新项目 → 选择 GitHub 部署
3. 关联本仓库，Zeabur 会自动识别为 Python 项目
4. 启动命令设为：`python web_ui/server.py`
5. 部署完成后自动生成 `.zeabur.app` 域名

**免费额度**：每月赠送额度，足以运行本应用，中国大陆访问速度快

### 方案三：PythonAnywhere（最简单）

1. 在 [pythonanywhere.com](https://pythonanywhere.com) 注册免费账号
2. 上传代码 → 配置 Web 应用 → 选择手动配置（Flask 模板，修改为运行 `server.py`）
3. 免费域名：`你的用户名.pythonanywhere.com`

**注意**：免费版文件存储有限，适合教学演示

---

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | Python 标准库 http.server |
| 前端 | 纯 HTML/CSS/JavaScript（单页应用） |
| 存储 | JSON 文件（`web_ui/saves/rooms/`） |
| 依赖 | **零外部依赖**（仅使用 Python 标准库） |

## 游戏规则

### 初始设置
- 每位学生启动资金：根据教师设置
- 初始声望：100

### 原材料
- A4 纸：市场价格波动，周一采购日购买

### 生产
- 1 张 A4 纸 → 1 顶帽子
- 生产后帽子进入「待检验」状态，需老师评级

### 销售
- 只能出售经老师评级的帽子
- 不同等级对应不同售价倍率
- 学生提交出售请求 → 老师审批确认

### 贷款
- 日利率 0.5%
- 10 天周期
- 可贷额度：现金 × 3

### 游戏结束
- 第 31 天游戏结束
- 按「现金 - 负债 = 净资产」排名

---

## 项目结构

```
syb-game/
├── web_ui/
│   ├── server.py          # HTTP API 服务器
│   ├── game_room.py       # 游戏核心逻辑
│   ├── static/
│   │   └── index.html     # 前端界面
│   └── saves/rooms/       # 游戏存档（自动生成）
├── syb_game/
│   ├── config.py          # 游戏配置
│   └── ...
├── syb.bat                # Windows 启动脚本
├── Dockerfile             # Docker 部署配置
└── README.md
```

---

## 许可证

本项目完全免费，仅供教学使用。欢迎 Fork、修改和分享。

---

## 使用 AI 构建的其他应用

以下应用同样使用 AI 编程助手（Trae）构建，已在 [帽子云](https://maozi.io) 免费部署，欢迎体验：

| 应用 | 链接 | 说明 |
|------|------|------|
| 🧩 PerinTool | [perinfool.maozi.io](https://roqmidxgq-perinfool-y0qkg01ht.maozi.io/) | 多功能小工具集合 |
| 🤖 PixelMechaBattle | [pixelmechabattle.maozi.io](https://jylj5ikoc-pixelmechabattle-2ouxr01ht.maozi.io/) | 像素机甲对战游戏 |
| 📊 BMI by Trae | [bmibytrae.maozi.io](https://9rbjcw12p-bmibytrae-3bk7u01ht.maozi.io/) | BMI 健康计算器 |
| 🕐 Kawaii Clock | [kawaiiclock.maozi.io](https://y1exnxj66-kawaiiclock-k5ntq01ht.maozi.io/) | 可爱风格桌面时钟 |

---

## 开发致谢

- 使用 [Trae](https://trae.ai) AI 编程助手开发
- 仅使用 Python 标准库，零外部依赖
- 适合创业培训（SYB）课堂教学场景