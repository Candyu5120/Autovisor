import configparser
import os
import threading
from tkinter import ttk, messagebox, filedialog
import tkinter as tk
import sv_ttk
from tkinter import font

# === 配置文件初始化 ===
config = configparser.ConfigParser()
config_file = 'configs.ini'
config.read(config_file, encoding="utf-8")

# === 默认配置 ===
default_driver = "Edge"
default_exepath = ""

# === 颜色主题 ===
PRIMARY_COLOR = "#1F6FEB"
SECONDARY_COLOR = "#F0F3F9"
TEXT_COLOR = "#2C3E50"
ACCENT_COLOR = "#0D47A1"


# === 事件函数 ===
def show_help():
    help_text = (
        "【必要配置说明】\n"
        "账号密码：可选项，如留空需手动登录\n"
        "课程链接：从智慧树课程页面复制链接（以 studyvideoh5.zhihuishu.com 开头）\n"
        "时长限制：程序运行的最大时间，0 表示不限\n"
        "倍速播放：最大 1.8（平台限制）\n\n"
        "【选填功能】\n"
        "自动跳过验证码：自动完成滑动验证\n"
        "隐藏浏览器窗口：运行时最小化浏览器\n"
        "静音播放：关闭视频声音\n\n"
        "输入 True 启用，留空或填 False 表示关闭\n\n"
        "【常见问题】\n"
        "Q: 浏览器启动失败？\n"
        "A: 请尝试双击 Autovisor.exe 运行。"
    )
    messagebox.showinfo('使用说明', help_text)


def launch_script():
    messagebox.showinfo('启动中', '准备刷课！')
    os.system('python Autovisor.py')


def launch_script_in_thread():
    threading.Thread(target=launch_script, daemon=True).start()


def launch_direct():
    def run():
        messagebox.showinfo('提示', '已记录配置，开始刷课')
        os.system('python Autovisor.py')

    threading.Thread(target=run, daemon=True).start()


def browse_exe_path():
    # Open native Windows picker for browser executable selection.
    selected_path = filedialog.askopenfilename(
        title="选择浏览器可执行文件",
        filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")],
        initialfile=os.path.basename(exe_path_entry.get().strip()) if exe_path_entry.get().strip() else "",
        initialdir=os.path.dirname(exe_path_entry.get().strip()) if exe_path_entry.get().strip() else os.getcwd()
    )
    if selected_path:
        exe_path_entry.delete(0, tk.END)
        exe_path_entry.insert(0, selected_path)


def read_inputs():
    return {
        "username": username_entry.get(),
        "password": password_entry.get(),
        "course_url": course_entry.get(),
        "limit_time": time_limit_entry.get(),
        "speed": speed_entry.get(),
        "auto_captcha": verify_var.get(),
        "hide_window": hide_var.get(),
        "mute": mute_var.get(),
        "driver": driver_var.get(),
        "exe_path": exe_path_entry.get()
    }


def save_and_run():
    inputs = read_inputs()
    config.set('course-url', 'URL1', inputs['course_url'])
    config.set('user-account', 'username', inputs['username'])
    config.set('user-account', 'password', inputs['password'])
    config.set('browser-option', 'driver', inputs['driver'])
    config.set('browser-option', 'exe_path', inputs['exe_path'])
    config.set('script-option', 'enableautocaptcha', inputs['auto_captcha'])
    config.set('script-option', 'enablehidewindow', inputs['hide_window'])
    config.set('course-option', 'limitmaxtime', inputs['limit_time'])
    config.set('course-option', 'limitspeed', inputs['speed'])
    config.set('course-option', 'soundoff', inputs['mute'])

    with open(config_file, 'w', encoding="utf-8") as f:
        config.write(f)

    launch_script_in_thread()


# === GUI 构建 ===
root = tk.Tk()
root.title("智慧树刷课助手")
root.geometry("700x790+50+30")
root.resizable(False, False)
sv_ttk.set_theme("light")

# 设置窗口背景颜色
root.configure(bg=SECONDARY_COLOR)

# === 标题区域 ===
title_frame = ttk.Frame(root)
title_frame.pack(fill=tk.X, padx=0, pady=0)
title_frame.configure(style="TFrame")

# 自定义标题样式
title_label = ttk.Label(root, text="🎓 智慧树刷课助手", font=("Microsoft YaHei", 24, "bold"))
title_label.pack(pady=20)

# 分隔线
separator1 = ttk.Separator(root, orient=tk.HORIZONTAL)
separator1.pack(fill=tk.X, padx=20, pady=5)

# === 主容器 ===
main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

# 从configs.ini读取默认值
def get_config(section, option, default=""):
    try:
        return config.get(section, option)
    except:
        return default

# === 必填项区域 ===
required_frame = ttk.LabelFrame(main_frame, text="📋 必要配置", padding=15)
required_frame.pack(fill=tk.X, pady=10)

ttk.Label(required_frame, text="手机号：", font=("Microsoft YaHei", 10)).grid(row=0, column=0, sticky="w", pady=8)
username_entry = ttk.Entry(required_frame, width=35, font=("Microsoft YaHei", 10))
username_entry.insert(0, get_config('user-account', 'username'))
username_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0))

ttk.Label(required_frame, text="密码：", font=("Microsoft YaHei", 10)).grid(row=1, column=0, sticky="w", pady=8)
password_entry = ttk.Entry(required_frame, show='*', width=35, font=("Microsoft YaHei", 10))
password_entry.insert(0, get_config('user-account', 'password'))
password_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0))

ttk.Label(required_frame, text="课程链接：", font=("Microsoft YaHei", 10)).grid(row=2, column=0, sticky="w", pady=8)
course_entry = ttk.Entry(required_frame, width=35, font=("Microsoft YaHei", 10))
course_entry.insert(0, get_config('course-url', 'url1'))
course_entry.grid(row=2, column=1, sticky="ew", padx=(10, 0))

ttk.Label(required_frame, text="时长限制(秒)：", font=("Microsoft YaHei", 10)).grid(row=3, column=0, sticky="w", pady=8)
time_limit_entry = ttk.Entry(required_frame, width=35, font=("Microsoft YaHei", 10))
time_limit_entry.insert(0, get_config('course-option', 'limitmaxtime'))
time_limit_entry.grid(row=3, column=1, sticky="ew", padx=(10, 0))

ttk.Label(required_frame, text="倍速播放：", font=("Microsoft YaHei", 10)).grid(row=4, column=0, sticky="w", pady=8)
speed_entry = ttk.Entry(required_frame, width=35, font=("Microsoft YaHei", 10))
speed_entry.insert(0, get_config('course-option', 'limitspeed'))
speed_entry.grid(row=4, column=1, sticky="ew", padx=(10, 0))

# 设置列权重，使Entry充满宽度
required_frame.columnconfigure(1, weight=1)

# 初始化选项变量（从configs.ini读取）
verify_var = tk.StringVar(value=get_config('script-option', 'enableautocaptcha', 'False'))
hide_var = tk.StringVar(value=get_config('script-option', 'enablehidewindow', 'False'))
mute_var = tk.StringVar(value=get_config('course-option', 'soundoff', 'False'))
driver_var = tk.StringVar(value=get_config('browser-option', 'driver', 'Edge'))

# === 浏览器配置区域 ===
browser_frame = ttk.LabelFrame(main_frame, text="🌐 浏览器配置", padding=15)
browser_frame.pack(fill=tk.X, pady=10)

# 浏览器驱动选择
ttk.Label(browser_frame, text="浏览器驱动：", font=("Microsoft YaHei", 10)).grid(row=0, column=0, sticky="w", pady=8)
driver_combo = ttk.Combobox(browser_frame, textvariable=driver_var, values=["Chrome", "Edge", "Firefox"], state="readonly", width=32, font=("Microsoft YaHei", 10))
driver_combo.grid(row=0, column=1, sticky="ew", padx=(10, 0))

# 浏览器exe路径
ttk.Label(browser_frame, text="浏览器路径：", font=("Microsoft YaHei", 10)).grid(row=1, column=0, sticky="w", pady=8)
path_input_frame = ttk.Frame(browser_frame)
path_input_frame.grid(row=1, column=1, sticky="ew", padx=(10, 0))

exe_path_entry = ttk.Entry(path_input_frame, width=30, font=("Microsoft YaHei", 10))
exe_path_entry.insert(0, get_config('browser-option', 'exe_path'))
exe_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

browse_button = ttk.Button(path_input_frame, text="浏览...", command=browse_exe_path, width=10)
browse_button.pack(side=tk.LEFT, padx=(8, 0))

# 提示文本
hint_label = ttk.Label(browser_frame, text="（留空则使用系统默认路径）", font=("Microsoft YaHei", 8))
hint_label.grid(row=2, column=1, sticky="w", padx=(10, 0), pady=(0, 5))

# 设置列权重
browser_frame.columnconfigure(1, weight=1)

# === 可选配置区域 ===
optional_frame = ttk.LabelFrame(main_frame, text="⚙️ 可选配置", padding=15)
optional_frame.pack(fill=tk.X, pady=10)

# 自动跳过验证码
ttk.Label(optional_frame, text="自动跳过验证码：", font=("Microsoft YaHei", 10)).grid(row=0, column=0, sticky="w", pady=8)
verify_frame = ttk.Frame(optional_frame)
verify_frame.grid(row=0, column=1, sticky="w", padx=(10, 0))
ttk.Radiobutton(verify_frame, text="启用", variable=verify_var, value="True").pack(side=tk.LEFT, padx=5)
ttk.Radiobutton(verify_frame, text="禁用", variable=verify_var, value="False").pack(side=tk.LEFT, padx=5)

# 隐藏浏览器窗口
ttk.Label(optional_frame, text="隐藏浏览器窗口：", font=("Microsoft YaHei", 10)).grid(row=1, column=0, sticky="w", pady=8)
hide_frame = ttk.Frame(optional_frame)
hide_frame.grid(row=1, column=1, sticky="w", padx=(10, 0))
ttk.Radiobutton(hide_frame, text="启用", variable=hide_var, value="True").pack(side=tk.LEFT, padx=5)
ttk.Radiobutton(hide_frame, text="禁用", variable=hide_var, value="False").pack(side=tk.LEFT, padx=5)

# 静音播放
ttk.Label(optional_frame, text="静音播放：", font=("Microsoft YaHei", 10)).grid(row=2, column=0, sticky="w", pady=8)
mute_frame = ttk.Frame(optional_frame)
mute_frame.grid(row=2, column=1, sticky="w", padx=(10, 0))
ttk.Radiobutton(mute_frame, text="启用", variable=mute_var, value="True").pack(side=tk.LEFT, padx=5)
ttk.Radiobutton(mute_frame, text="禁用", variable=mute_var, value="False").pack(side=tk.LEFT, padx=5)

# === 按钮区域 ===
button_frame = ttk.Frame(main_frame)
button_frame.pack(fill=tk.X, pady=20)

# 开始刷课按钮
start_button = ttk.Button(button_frame, text="▶️ 开始刷课", command=save_and_run)
start_button.pack(side=tk.LEFT, padx=5)

# 查看帮助按钮
help_button = ttk.Button(button_frame, text="❓ 查看帮助", command=show_help)
help_button.pack(side=tk.LEFT, padx=5)

# 回车绑定
root.bind('<Return>', lambda event: save_and_run())

root.mainloop()
