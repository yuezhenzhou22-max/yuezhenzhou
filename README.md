# 时间提醒小飞机

一个 Windows 托盘小程序：平时藏在右下角，需要时打开提醒管理窗口；整点时小飞机会拉着彩旗飞过屏幕，手工会议提醒会提前 3 分钟飞 3 次。

## 已实现的规则

- 默认启动后最小化到右下角托盘。
- 托盘菜单包含：打开提醒管理、测试小飞机、暂停/恢复整点提醒、退出。
- 整点提醒默认开启，只在 08:00 到 23:00 生效，23:00 也会提醒。
- 每个整点有不同的俏皮文案，并显示当前时间。
- 手工会议提醒支持日期、时间、提醒文字。
- 会议提醒会在会议前 3 分钟开始飞行，间隔 10 秒，共飞 3 次。
- 错过的提醒不会补飞，会保留在记录里。
- 提醒文字最多 20 个字，超过会禁止保存。
- 记录保存在程序旁边的 `reminders.json`。

## 安装 Python

你当前电脑还没有检测到 `python` 或 `py` 命令。先安装 Python：

1. 打开 [Python 官网下载页](https://www.python.org/downloads/windows/)。
2. 下载 Python 3.11 或更新版本。
3. 安装时勾选 `Add python.exe to PATH`。
4. 安装完成后重新打开 PowerShell。
5. 运行：

```powershell
python --version
```

能看到版本号就可以继续。

## 安装依赖

在本项目目录运行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

如果下载 PySide6 很慢，可以换清华源：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 启动程序

```powershell
.\.venv\Scripts\python.exe run.py
```

启动后不会弹主窗口，只会出现在右下角托盘。右键托盘图标可以打开提醒管理，或者点击“测试小飞机”看动画。

## 文件说明

- `run.py`：启动入口。
- `meeting_reminder/app.py`：托盘程序入口。
- `meeting_reminder/manager_window.py`：提醒管理窗口。
- `meeting_reminder/scheduler.py`：整点和会议提醒调度。
- `meeting_reminder/flyer.py`：小飞机和彩旗动画。
- `meeting_reminder/quotes.py`：每个整点的文案。
- `meeting_reminder/storage.py`：JSON 数据保存。
- `reminders.json`：运行后自动生成的数据文件。
