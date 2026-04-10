import configparser
import os
import threading
import subprocess
import sys
import re
import flet as ft

if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')
if sys.stdin is None:
    sys.stdin = open(os.devnull, 'r')

# === 配置文件初始化 ===
config = configparser.ConfigParser()
config_file = 'configs.ini'
config.read(config_file, encoding="utf-8")

ANSI_ESCAPE_RE = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')

# worker 模式：不创建 GUI，直接执行 Autovisor 主流程。
def run_worker_mode():
    from Autovisor import run as run_autovisor
    run_autovisor()

if '--worker' in sys.argv:
    run_worker_mode()
    sys.exit(0)

# === Flet GUI 构建 ===
def main(page: ft.Page):
    # 页面基础配置
    page.title = "智慧树刷课助手"
    page.window.width = 1100
    page.window.height = 800
    page.window.min_width = 950
    page.window.min_height = 650
    page.theme_mode = ft.ThemeMode.SYSTEM

    # 去掉全局窗口透明度（Windows下强制透明度会导致ClearType字体平滑失效，从而导致文字发虚变形）
    # try:
    #     page.window.opacity = 0.94
    # except:
    #     pass

    def get_config(section, option, default=""):
        try:
            return config.get(section, option)
        except:
            return default

    # ====================
    # 左侧：控制台日志区域
    # ====================
    log_list = ft.ListView(expand=True, spacing=4, auto_scroll=True)
    log_panel = ft.Container(
        content=log_list,
        expand=True,
        bgcolor="#1E1E1E",
        border_radius=12,
        padding=15,
        border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
    )

    log_buffer = []
    buffer_lock = threading.Lock()

    def flush_all_logs():
        with buffer_lock:
            if not log_buffer:
                return
            lines = log_buffer[:]
            log_buffer.clear()
        for line in lines:
            log_list.controls.append(ft.Text(line, font_family="Consolas", color="#10B981", size=13))
        page.update()

    def log_updater():
        import time
        while True:
            # 低延迟批量刷新，避免日志堆积后出现“延后清空感”。
            time.sleep(0.1)
            flush_all_logs()

    # 启动后台日志刷新线程
    threading.Thread(target=log_updater, daemon=True).start()

    def append_log(text):
        # 去除额外的换行符，避免日志中出现不必要的空白行
        clean = ANSI_ESCAPE_RE.sub('', text).replace('\r', '').rstrip('\n')
        if clean:
            with buffer_lock:
                log_buffer.append(clean)

    def launch_script():
        def run_process():
            try:
                if getattr(sys, 'frozen', False):
                    command = [sys.executable, '--worker']
                    work_dir = os.path.dirname(sys.executable)
                else:
                    command = [sys.executable, '-u', os.path.abspath(__file__), '--worker']
                    work_dir = os.path.dirname(os.path.abspath(__file__))

                env = os.environ.copy()
                env['AUTOVISOR_NO_PROMPT'] = '1'
                env.setdefault('PYTHONIOENCODING', 'utf-8')
                env.setdefault('PYTHONUTF8', '1')
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    cwd=work_dir,
                    env=env,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                for line in process.stdout:
                    try:
                        decoded_line = line.decode('utf-8')
                    except UnicodeDecodeError:
                        decoded_line = line.decode('gbk', errors='replace')
                    append_log(decoded_line)
                process.stdout.close()
                process.wait()
                append_log(f"[程序退出，状态码：{process.returncode}]")
                flush_all_logs()  # 结束时立刻把剩下的全刷出来
            except Exception as e:
                append_log(f"[启动错误]: {str(e)}")
                flush_all_logs()

        threading.Thread(target=run_process, daemon=True).start()

    # ====================
    # 右侧：配置与控制区域
    # ====================
    # --- 变量与控件定义 ---
    username_tf = ft.TextField(label="手机号 (留空则手动登录)", value=get_config('user-account', 'username'), height=50)
    password_tf = ft.TextField(label="密码", value=get_config('user-account', 'password'), password=True, can_reveal_password=True, height=50)
    course_tf = ft.TextField(label="课程链接 (以 studyvideoh5... 开头)", value=get_config('course-url', 'url1'), height=50)
    limit_time_tf = ft.TextField(label="时长限制 (秒，0表示不限)", value=get_config('course-option', 'limitmaxtime'), height=50)
    speed_tf = ft.TextField(label="倍速播放 (最大 1.8)", value=get_config('course-option', 'limitspeed'), height=50)

    driver_dp = ft.Dropdown(
        label="浏览器驱动",
        value=get_config('browser-option', 'driver', 'Edge'),
        options=[ft.dropdown.Option("Chrome"), ft.dropdown.Option("Edge"), ft.dropdown.Option("Firefox")]
    )
    exe_path_tf = ft.TextField(label="浏览器路径", value=get_config('browser-option', 'exe_path'), expand=True, height=50)

    def pick_exe_result(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            exe_path_tf.value = e.files[0].path
            page.update()

    exe_picker = ft.FilePicker(on_result=pick_exe_result)
    page.overlay.append(exe_picker)

    def clear_exe(e):
        exe_path_tf.value = ""
        page.update()

    browse_row = ft.Row([
        exe_path_tf,
        ft.ElevatedButton("浏览", height=50, on_click=lambda _: exe_picker.pick_files(allowed_extensions=["exe"])),
        ft.OutlinedButton("清空", height=50, on_click=clear_exe)
    ])

    auto_captcha_sw = ft.Switch(label="自动跳过验证码", value=(get_config('script-option', 'enableautocaptcha', 'False') == 'True'))
    hide_window_sw = ft.Switch(label="隐藏浏览器窗口", value=(get_config('script-option', 'enablehidewindow', 'False') == 'True'))
    mute_sw = ft.Switch(label="静音播放", value=(get_config('course-option', 'soundoff', 'False') == 'True'))

    # --- 动作与事件 ---
    def save_and_run(e=None):
        config.set('course-url', 'URL1', course_tf.value)
        config.set('user-account', 'username', username_tf.value)
        config.set('user-account', 'password', password_tf.value)
        config.set('browser-option', 'driver', driver_dp.value)
        config.set('browser-option', 'exe_path', exe_path_tf.value)
        config.set('script-option', 'enableautocaptcha', str(auto_captcha_sw.value))
        config.set('script-option', 'enablehidewindow', str(hide_window_sw.value))
        config.set('course-option', 'limitmaxtime', limit_time_tf.value)
        config.set('course-option', 'limitspeed', speed_tf.value)
        config.set('course-option', 'soundoff', str(mute_sw.value))

        with open(config_file, 'w', encoding="utf-8") as f:
            config.write(f)

        launch_script()

    def close_dlg(e):
        help_dlg.open = False
        page.update()

    help_text = (
        "【必要配置说明】\n"
        "1. 账号密码：可选项，如留空需手动登录。\n"
        "2. 课程链接：从智慧树页面复制链接（以 studyvideo 开头）。\n"
        "3. 时长限制：为 0 则不限制。\n\n"
        "【常见问题】\n"
        "Q: 浏览器启动失败怎么办？\n"
        "A: 程序需要对应浏览器的支持或放置正确版本的驱动。\n"
    )
    help_dlg = ft.AlertDialog(
        title=ft.Text("❓ 使用说明"),
        content=ft.Text(help_text),
        actions=[ft.TextButton("我了解了", on_click=close_dlg)],
    )
    page.overlay.append(help_dlg)

    def show_help(e):
        help_dlg.open = True
        page.update()

    # --- 模块化 UI 组装 ---
    def create_card(title, icon, *controls):
        return ft.Card(
            elevation=0,
            margin=ft.margin.only(bottom=20),
            color=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            content=ft.Container(
                padding=20,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                content=ft.Column([
                    ft.Row([ft.Icon(icon, color=ft.Colors.PRIMARY, size=24), ft.Text(title, size=16, weight=ft.FontWeight.W_600)]),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    *controls
                ], spacing=15)
            )
        )

    right_panel = ft.Container(
        expand=True,
        content=ft.ListView(
            expand=True,
            spacing=0,
            controls=[
                ft.Text("🎓 智慧树刷课助手", size=24, weight=ft.FontWeight.W_800, color=ft.Colors.PRIMARY, text_align=ft.TextAlign.CENTER),
                ft.Divider(height=25, color=ft.Colors.TRANSPARENT),

                create_card("基本配置", ft.Icons.SETTINGS, username_tf, password_tf, course_tf, limit_time_tf, speed_tf),
                create_card("浏览器配置", ft.Icons.WEB, driver_dp, browse_row),
                create_card("附加功能", ft.Icons.EXTENSION, auto_captcha_sw, hide_window_sw, mute_sw),

                ft.Container(
                    margin=ft.margin.only(top=10, bottom=20),
                    content=ft.Row([
                        ft.ElevatedButton(
                            content=ft.Row(
                                [ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, size=24), ft.Text("开始刷课", size=16, weight=ft.FontWeight.W_600)],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=8
                            ),
                            expand=True,
                            height=55,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=12),
                                bgcolor=ft.Colors.PRIMARY,
                                color=ft.Colors.ON_PRIMARY
                            ),
                            on_click=save_and_run
                        ),
                        ft.OutlinedButton(
                            content=ft.Text("使用说明", size=16, weight=ft.FontWeight.W_600),
                            expand=True,
                            height=55,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                            on_click=show_help
                        )
                    ], spacing=15)
                )
            ],
            padding=ft.padding.only(right=15, left=10)
        )
    )

    left_side = ft.Column([
        ft.Row([ft.Icon(ft.Icons.TERMINAL, size=28), ft.Text("控制台日志", size=20, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.START),
        log_panel
    ], expand=5)

    right_side = ft.Column([right_panel], expand=4)

    # 加入主框架
    page.add(
        ft.Container(
            content=ft.Row(
                controls=[left_side, right_side],
                expand=True,
                spacing=25
            ),
            padding=10,
            expand=True
        )
    )


if __name__ == '__main__':
    # 既然已经通过镜像源装好了完整的 flet-desktop 依赖，
    # 现在可以直接以原生的 Windows 桌面视窗模式启动了！
    ft.app(target=main)
