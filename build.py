import os
import shutil
name = "Autovisor"

cmd = (
    f"pyinstaller "
    f"--log-level=INFO "
    f"--noconfirm "
    f"-w "
    f"-i ./res/zhs.ico "
    f"--onedir "
    f"--contents-directory=internal "
    f"--name={name} "
    f"--collect-all cv2 "          # 确保 OpenCV 的所有 DLL 和元数据被抓取
    f"--collect-all numpy "        # 确保 numpy 的元数据被抓取
    f"./GUI.py "
)
os.system(cmd)

os.mkdir(f"./dist/{name}/res")
open(f"./dist/{name}/为防止启动失败, 建议使用Chrome浏览器", "w").close()
shutil.copyfile("./configs.ini", f"./dist/{name}/configs.ini")
shutil.copyfile("./res/stealth.min.js", f"./dist/{name}/res/stealth.min.js")
shutil.rmtree("./build", ignore_errors=True)
os.remove("./Autovisor.spec")
