import customtkinter as ctk
from tkinter import filedialog, messagebox
import subprocess
import os
import sys
import threading
import json
from datetime import datetime

# ==================== الثيم ====================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def get_tool(name):
    base = os.path.dirname(os.path.abspath(sys.argv[0]))
    local = os.path.join(base, name)
    if os.path.exists(local):
        return local
    if hasattr(sys, '_MEIPASS'):
        temp = os.path.join(sys._MEIPASS, name)
        if os.path.exists(temp):
            return temp
    return name


ADB = get_tool("adb.exe")
FASTBOOT = get_tool("fastboot.exe")


class MyToolApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MyTool - Professional Edition v2.0")
        self.geometry("1200x780")
        self.minsize(1000, 650)

        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        try:
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except:
            pass

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main()

        self._log("مرحبًا! MyTool v2.0 جاهز.", "success")
        self._log(f"ADB: {ADB}", "info")
        self._log(f"Fastboot: {FASTBOOT}", "info")

        self.after(500, self._refresh_device_status)
        self.after(5000, self._auto_refresh_loop)

        self.bind("<F5>", lambda e: self._refresh_device_status())
        self.bind("<Control-l>", lambda e: self._clear_log())

    # ==================== الشريط الجانبي ====================
    def _build_sidebar(self):
        self.sidebar = ctk.CTkScrollableFrame(self, width=230, corner_radius=0, fg_color="#181825")
        self.sidebar.grid(row=0, column=0, sticky="ns")

        ctk.CTkLabel(self.sidebar, text="🔧 MyTool", font=("Segoe UI", 22, "bold"),
                     text_color="#89b4fa").pack(pady=(20, 0), padx=20, anchor="w")
        ctk.CTkLabel(self.sidebar, text="v2.0 Professional", font=("Segoe UI", 10),
                     text_color="#6c7086").pack(pady=(0, 15), padx=20, anchor="w")

        self.nav_buttons = {}

        def section(label):
            ctk.CTkLabel(self.sidebar, text=label, font=("Segoe UI", 11, "bold"),
                         text_color="#6c7086").pack(pady=(12, 2), padx=20, anchor="w")

        def nav(key, label):
            btn = ctk.CTkButton(self.sidebar, text=label, anchor="w",
                                font=("Segoe UI", 13), height=36,
                                fg_color="transparent", hover_color="#313244",
                                text_color="#cdd6f4",
                                command=lambda k=key: self._show_page(k))
            btn.pack(padx=10, pady=1, fill="x")
            self.nav_buttons[key] = btn

        section("أدوات عامة")
        nav("adb", "📱  ADB")
        nav("fastboot", "⚡  Fastboot")
        nav("mtk", "🔩  MediaTek")
        nav("qc", "🔧  Qualcomm / EDL")

        section("الشركات المصنعة")
        nav("samsung", "🇰🇷 Samsung")
        nav("xiaomi", "🇨🇳 Xiaomi / Redmi")
        nav("huawei", "🇨🇳 Huawei / Honor")
        nav("pixel", "🇺🇸 Google Pixel")
        nav("oneplus", "🇨🇳 OnePlus")
        nav("motorola", "🇺🇸 Motorola")
        nav("sony", "🇯🇵 Sony")
        nav("lg", "🇰🇷 LG")
        nav("oppo", "🇨🇳 Oppo / Realme")
        nav("vivo", "🇨🇳 Vivo / iQOO")

        section("معلومات")
        nav("about", "ℹ️  حول البرنامج")

        # حالة الجهاز
        self.device_frame = ctk.CTkFrame(self.sidebar, fg_color="#11111b", corner_radius=8)
        self.device_frame.pack(padx=10, pady=15, fill="x")

        self.device_status_dot = ctk.CTkLabel(self.device_frame, text="●",
                                              font=("Segoe UI", 20), text_color="#f38ba8")
        self.device_status_dot.pack(side="left", padx=(10, 5))

        self.device_status_text = ctk.CTkLabel(self.device_frame, text="لا يوجد جهاز",
                                               font=("Segoe UI", 11), text_color="#cdd6f4")
        self.device_status_text.pack(side="left", padx=(0, 8), pady=8)

    # ==================== المحتوى الرئيسي ====================
    def _build_main(self):
        self.main = ctk.CTkFrame(self, fg_color="#1e1e2e", corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        self.header = ctk.CTkFrame(self.main, height=55, fg_color="#181825", corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew")
        self.header_label = ctk.CTkLabel(self.header, text="ADB Commands",
                                         font=("Segoe UI", 17, "bold"), text_color="#cdd6f4")
        self.header_label.pack(side="left", padx=25, pady=15)

        self.progress = ctk.CTkProgressBar(self.header, width=200)
        self.progress.set(0)
        self.progress.pack(side="right", padx=15)

        self.page_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        self.page_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        self.page_frame.grid_columnconfigure(0, weight=1)
        self.page_frame.grid_rowconfigure(0, weight=1)

        self.log_frame = ctk.CTkFrame(self.main, fg_color="#181825", corner_radius=0)
        self.log_frame.grid(row=2, column=0, sticky="ew")
        self.log_frame.grid_columnconfigure(0, weight=1)

        log_header = ctk.CTkFrame(self.log_frame, fg_color="transparent")
        log_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(6, 0))
        ctk.CTkLabel(log_header, text="📜 السجل", font=("Segoe UI", 12, "bold"),
                     text_color="#89b4fa").pack(side="left")
        ctk.CTkButton(log_header, text="مسح", width=55, height=22, font=("Segoe UI", 10),
                      fg_color="#313244", hover_color="#45475a",
                      command=self._clear_log).pack(side="right", padx=3)
        ctk.CTkButton(log_header, text="نسخ", width=55, height=22, font=("Segoe UI", 10),
                      fg_color="#313244", hover_color="#45475a",
                      command=self._copy_log).pack(side="right", padx=3)

        self.log_box = ctk.CTkTextbox(self.log_frame, height=150,
                                      font=("Consolas", 11), fg_color="#11111b",
                                      text_color="#cdd6f4")
        self.log_box.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 8))
        self.log_box.configure(state="disabled")

        # كل الصفحات
        self.pages = {}
        self._build_adb_page()
        self._build_fastboot_page()
        self._build_mtk_page()
        self._build_qc_page()
        self._build_samsung_page()
        self._build_xiaomi_page()
        self._build_huawei_page()
        self._build_pixel_page()
        self._build_oneplus_page()
        self._build_motorola_page()
        self._build_sony_page()
        self._build_lg_page()
        self._build_oppo_page()
        self._build_vivo_page()
        self._build_about_page()

        self._show_page("adb")

    def _make_button_grid(self, page, buttons, cols=2):
        for c in range(cols):
            page.grid_columnconfigure(c, weight=1)
        for i, (text, cmd, color) in enumerate(buttons):
            ctk.CTkButton(page, text=text, height=48, font=("Segoe UI", 12, "bold"),
                          fg_color=color, text_color="#11111b", hover_color="#b4befe",
                          command=cmd).grid(row=i // cols, column=i % cols,
                                            padx=6, pady=6, sticky="ew")

    # ==================== الصفحات ====================
    def _build_adb_page(self):
        page = ctk.CTkScrollableFrame(self.page_frame, fg_color="transparent")
        buttons = [
            ("📱 عرض الأجهزة", self._adb_devices, "#89b4fa"),
            ("ℹ️ معلومات الجهاز", self._adb_info, "#89b4fa"),
            ("🔋 البطارية", self._adb_battery, "#89b4fa"),
            ("📦 الحزم المثبتة", self._adb_packages, "#89b4fa"),
            ("💿 مساحة التخزين", self._adb_storage, "#89b4fa"),
            ("🖥️ معلومات العتاد", self._adb_hardware, "#89b4fa"),
            ("📸 لقطة شاشة", self._adb_screenshot, "#a6e3a1"),
            ("🎥 تسجيل شاشة 30ث", self._adb_record, "#a6e3a1"),
            ("📥 سحب ملف", self._adb_pull, "#f9e2af"),
            ("📤 إرسال ملف", self._adb_push, "#f9e2af"),
            ("💾 نسخة احتياطية", self._adb_backup, "#a6e3a1"),
            ("📋 تقرير JSON", self._adb_report, "#a6e3a1"),
            ("📲 تثبيت APK", self._adb_install, "#a6e3a1"),
            ("🗑️ إزالة تطبيق", self._adb_uninstall, "#f9e2af"),
            ("🚫 تعطيل نظام", self._adb_disable_bloat, "#f9e2af"),
            ("✅ تفعيل نظام", self._adb_enable_bloat, "#a6e3a1"),
            ("🔄 إعادة تشغيل", self._adb_reboot, "#f9e2af"),
            ("⚠️ Bootloader", self._adb_bootloader, "#f38ba8"),
            ("⚠️ Recovery", self._adb_recovery, "#f38ba8"),
            ("🚨 ضبط المصنع", self._adb_factory_reset, "#f38ba8"),
        ]
        self._make_button_grid(page, buttons)
        self.pages["adb"] = page

    def _build_fastboot_page(self):
        page = ctk.CTkScrollableFrame(self.page_frame, fg_color="transparent")
        buttons = [
            ("⚡ عرض الأجهزة", self._fb_devices, "#89b4fa"),
            ("🔍 متغير المنتج", self._fb_getvar, "#89b4fa"),
            ("🔍 جميع المتغيرات", self._fb_all_vars, "#89b4fa"),
            ("🔄 إعادة تشغيل", self._fb_reboot, "#f9e2af"),
            ("⚠️ Recovery", self._fb_recovery, "#f38ba8"),
            ("⚙️ Bootloader", self._fb_bootloader, "#f38ba8"),
        ]
        self._make_button_grid(page, buttons)
        self.pages["fastboot"] = page

    def _build_mtk_page(self):
        page = ctk.CTkScrollableFrame(self.page_frame, fg_color="transparent")
        ctk.CTkLabel(page, text="🔩 MediaTek — pip install mtkclient",
                     font=("Segoe UI", 14, "bold"), text_color="#f9e2af").pack(pady=(5, 10), anchor="w")
        frame = ctk.CTkFrame(page, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        buttons = [
            ("ℹ️ قراءة GPT", self._mtk_info, "#89b4fa"),
            ("📥 سحب boot", self._mtk_dump_boot, "#f9e2af"),
            ("⚡ أمر مخصص", self._mtk_custom, "#89b4fa"),
            ("🔓 فك Bootloader (خطير)", self._mtk_unlock, "#f38ba8"),
        ]
        self._make_button_grid(frame, buttons)
        self.pages["mtk"] = page

    def _build_qc_page(self):
        page = ctk.CTkScrollableFrame(self.page_frame, fg_color="transparent")
        ctk.CTkLabel(page, text="🔧 Qualcomm / EDL — pip install edl",
                     font=("Segoe UI", 14, "bold"), text_color="#f9e2af").pack(pady=(5, 10), anchor="w")
        frame = ctk.CTkFrame(page, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        buttons = [
            ("ℹ️ قراءة GPT (EDL)", self._edl_gpt, "#89b4fa"),
            ("📥 سحب boot (EDL)", self._edl_dump_boot, "#f9e2af"),
            ("⚙️ دخول EDL من ADB", self._adb_edl, "#f38ba8"),
        ]
        self._make_button_grid(frame, buttons)
        self.pages["qc"] = page

    def _make_vendor_page(self, key, title, buttons):
        page = ctk.CTkScrollableFrame(self.page_frame, fg_color="transparent")
        ctk.CTkLabel(page, text=title, font=("Segoe UI", 14, "bold"),
                     text_color="#89b4fa").pack(pady=(5, 10), anchor="w")
        frame = ctk.CTkFrame(page, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        self._make_button_grid(frame, buttons)
        self.pages[key] = page

    def _build_samsung_page(self):
        self._make_vendor_page("samsung", "🇰🇷 Samsung — أوامر ADB/Fastboot", [
            ("ℹ️ معلومات الجهاز", self._samsung_info, "#89b4fa"),
            ("📱 عرض CSC", self._samsung_csc, "#89b4fa"),
            ("🔢 Serial", self._samsung_serial, "#89b4fa"),
            ("📲 وضع Download", self._samsung_download, "#f9e2af"),
            ("⚠️ Bootloader", self._samsung_bootloader, "#f38ba8"),
            ("⚠️ Recovery", self._samsung_recovery, "#f38ba8"),
        ])

    def _build_xiaomi_page(self):
        self._make_vendor_page("xiaomi", "🇨🇳 Xiaomi / Redmi / POCO", [
            ("ℹ️ معلومات MIUI", self._xiaomi_info, "#89b4fa"),
            ("🔍 حالة Bootloader", self._xiaomi_bl_status, "#89b4fa"),
            ("⚡ Fastboot", self._xiaomi_fastboot, "#f9e2af"),
            ("⚙️ EDL (خطير)", self._xiaomi_edl, "#f38ba8"),
        ])

    def _build_huawei_page(self):
        self._make_vendor_page("huawei", "🇨🇳 Huawei / Honor", [
            ("ℹ️ معلومات", self._huawei_info, "#89b4fa"),
            ("🔍 حالة Bootloader", self._huawei_bl_info, "#89b4fa"),
            ("⚡ Fastboot", self._huawei_fastboot, "#f9e2af"),
        ])

    def _build_pixel_page(self):
        self._make_vendor_page("pixel", "🇺🇸 Google Pixel", [
            ("ℹ️ معلومات", self._pixel_info, "#89b4fa"),
            ("🔍 كل المتغيرات", self._pixel_bl_status, "#89b4fa"),
            ("⚡ Fastboot", self._pixel_fastboot, "#f9e2af"),
        ])

    def _build_oneplus_page(self):
        self._make_vendor_page("oneplus", "🇨🇳 OnePlus", [
            ("ℹ️ معلومات", self._oneplus_info, "#89b4fa"),
            ("🔍 حالة Bootloader", self._oneplus_bl_status, "#89b4fa"),
            ("⚡ Fastboot", self._oneplus_fastboot, "#f9e2af"),
        ])

    def _build_motorola_page(self):
        self._make_vendor_page("motorola", "🇺🇸 Motorola", [
            ("ℹ️ معلومات", self._motorola_info, "#89b4fa"),
            ("🔍 بيانات فك القفل", self._motorola_unlock_data, "#89b4fa"),
            ("⚡ Fastboot", self._motorola_fastboot, "#f9e2af"),
        ])

    def _build_sony_page(self):
        self._make_vendor_page("sony", "🇯🇵 Sony Xperia", [
            ("ℹ️ معلومات", self._sony_info, "#89b4fa"),
            ("🔍 حالة Bootloader", self._sony_bl_status, "#89b4fa"),
            ("⚡ Fastboot", self._sony_fastboot, "#f9e2af"),
        ])

    def _build_lg_page(self):
        self._make_vendor_page("lg", "🇰🇷 LG", [
            ("ℹ️ معلومات", self._lg_info, "#89b4fa"),
            ("📲 Download Mode", self._lg_download, "#f9e2af"),
        ])

    def _build_oppo_page(self):
        self._make_vendor_page("oppo", "🇨🇳 Oppo / Realme", [
            ("ℹ️ معلومات", self._oppo_info, "#89b4fa"),
            ("⚡ Fastboot", self._oppo_fastboot, "#f9e2af"),
            ("⚙️ EDL (خطير)", self._oppo_edl, "#f38ba8"),
        ])

    def _build_vivo_page(self):
        self._make_vendor_page("vivo", "🇨🇳 Vivo / iQOO", [
            ("ℹ️ معلومات", self._vivo_info, "#89b4fa"),
            ("⚡ Fastboot", self._vivo_fastboot, "#f9e2af"),
        ])

    def _build_about_page(self):
        page = ctk.CTkScrollableFrame(self.page_frame, fg_color="transparent")
        ctk.CTkLabel(page, text="MyTool - Professional Edition v2.0",
                     font=("Segoe UI", 22, "bold"), text_color="#89b4fa").pack(pady=(10, 5))
        ctk.CTkLabel(page, text="أداة مفتوحة المصدر لإدارة هواتف أندرويد",
                     font=("Segoe UI", 13), text_color="#6c7086").pack(pady=(0, 20))

        warn = ctk.CTkFrame(page, fg_color="#2a1a1a", corner_radius=8,
                            border_width=1, border_color="#f38ba8")
        warn.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(warn, text=("⚠️ تحذير قانوني\n\n"
                                 "هذه الأداة مخصصة فقط للاستخدام على الأجهزة التي تملكها.\n"
                                 "أي استخدام على أجهزة لا تملكها يعتبر جريمة إلكترونية.\n"
                                 "المطور غير مسؤول عن أي سوء استخدام."),
                     font=("Segoe UI", 12), text_color="#f38ba8",
                     justify="right").pack(padx=15, pady=15)

        ctk.CTkLabel(page, text="📚 مصادر:", font=("Segoe UI", 14, "bold"),
                     text_color="#89b4fa").pack(pady=(15, 5), anchor="e", padx=25)
        for t in ["developer.android.com/tools/adb", "github.com/bkerler/mtkclient",
                  "github.com/amonet-kaminski/edl"]:
            ctk.CTkLabel(page, text="• " + t, font=("Consolas", 11),
                         text_color="#94e2d5").pack(anchor="e", padx=35)

        self.pages["about"] = page

    def _show_page(self, key):
        for p in self.pages.values():
            p.grid_forget()
        self.pages[key].grid(row=0, column=0, sticky="nsew")
        for k, btn in self.nav_buttons.items():
            btn.configure(fg_color="#313244" if k == key else "transparent")
        titles = {
            "adb": "ADB Commands", "fastboot": "Fastboot Commands",
            "mtk": "MediaTek Tools", "qc": "Qualcomm / EDL",
            "samsung": "Samsung", "xiaomi": "Xiaomi / Redmi / POCO",
            "huawei": "Huawei / Honor", "pixel": "Google Pixel",
            "oneplus": "OnePlus", "motorola": "Motorola", "sony": "Sony",
            "lg": "LG", "oppo": "Oppo / Realme", "vivo": "Vivo / iQOO",
            "about": "حول البرنامج"
        }
        self.header_label.configure(text=titles.get(key, ""))

    # ==================== السجل ====================
    def _log(self, text, level="info"):
        icons = {"info": "ℹ️", "success": "✓", "error": "❌", "warn": "⚠️", "cmd": "▶"}
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{ts}] {icons.get(level, '•')} {text}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _copy_log(self):
        self.clipboard_clear()
        self.clipboard_append(self.log_box.get("1.0", "end"))
        self._log("✓ نُسخ السجل", "success")

    # ==================== التنفيذ ====================
    def _run(self, cmd, description=""):
        def worker():
            self.progress.start()
            try:
                self._log(description or "تنفيذ...", "cmd")
                self._log(" ".join(cmd) if isinstance(cmd, list) else cmd, "info")
                result = subprocess.run(cmd, shell=isinstance(cmd, str),
                                        capture_output=True, text=True, timeout=90)
                if result.stdout.strip():
                    self._log(result.stdout.strip()[:1500], "success")
                if result.stderr.strip():
                    self._log(result.stderr.strip()[:1500], "warn")
                self._log("انتهى.", "success")
                self._refresh_device_status()
            except FileNotFoundError:
                self._log(f"الأداة غير موجودة: {cmd[0]}", "error")
            except subprocess.TimeoutExpired:
                self._log("انتهت المهلة", "error")
            except Exception as e:
                self._log(f"خطأ: {e}", "error")
            finally:
                self.progress.stop()
                self.progress.set(0)
        threading.Thread(target=worker, daemon=True).start()

    def _refresh_device_status(self):
        def worker():
            try:
                r = subprocess.run([ADB, "devices"], capture_output=True,
                                   text=True, timeout=10)
                lines = [l for l in r.stdout.splitlines()[1:] if l.strip()]
                if lines:
                    dev_id = lines[0].split()[0]
                    r2 = subprocess.run([ADB, "shell", "getprop", "ro.product.model"],
                                        capture_output=True, text=True, timeout=5)
                    model = r2.stdout.strip() or "Android"
                    self.device_status_dot.configure(text_color="#a6e3a1")
                    self.device_status_text.configure(text=f"{model}\n{dev_id[:14]}")
                else:
                    self.device_status_dot.configure(text_color="#f38ba8")
                    self.device_status_text.configure(text="لا يوجد جهاز")
            except:
                self.device_status_dot.configure(text_color="#f38ba8")
                self.device_status_text.configure(text="خطأ ADB")
        threading.Thread(target=worker, daemon=True).start()

    def _auto_refresh_loop(self):
        self._refresh_device_status()
        self.after(5000, self._auto_refresh_loop)

    # ==================== ADB ====================
    def _adb_devices(self): self._run([ADB, "devices", "-l"], "قائمة الأجهزة")
    def _adb_info(self):
        for p in ["ro.product.manufacturer", "ro.product.model",
                  "ro.build.version.release", "ro.build.version.sdk"]:
            self._run([ADB, "shell", "getprop", p], p)
    def _adb_battery(self): self._run([ADB, "shell", "dumpsys", "battery"], "البطارية")
    def _adb_packages(self): self._run([ADB, "shell", "pm", "list", "packages", "-3"], "الحزم")
    def _adb_storage(self): self._run([ADB, "shell", "df", "-h"], "التخزين")
    def _adb_hardware(self):
        for p in ["ro.hardware", "ro.product.cpu.abi", "ro.sf.lcd_density"]:
            self._run([ADB, "shell", "getprop", p], p)
    def _adb_reboot(self): self._run([ADB, "reboot"], "إعادة تشغيل")
    def _adb_bootloader(self): self._run([ADB, "reboot", "bootloader"], "Bootloader")
    def _adb_recovery(self): self._run([ADB, "reboot", "recovery"], "Recovery")

    def _adb_screenshot(self):
        def worker():
            fn = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            try:
                with open(fn, "wb") as f:
                    subprocess.run([ADB, "exec-out", "screencap", "-p"],
                                   stdout=f, timeout=15)
                self._log(f"✓ حُفظت: {fn}", "success")
            except Exception as e:
                self._log(f"خطأ: {e}", "error")
        threading.Thread(target=worker, daemon=True).start()

    def _adb_record(self):
        self._log("⏺ التسجيل 30 ثانية...", "warn")
        self._run([ADB, "shell", "screenrecord", "/sdcard/record.mp4",
                   "--time-limit", "30"], "تسجيل")
        def pull():
            import time
            time.sleep(32)
            self._run([ADB, "pull", "/sdcard/record.mp4", "record.mp4"], "سحب التسجيل")
        threading.Thread(target=pull, daemon=True).start()

    def _adb_pull(self):
        remote = ctk.CTkInputDialog(text="مسار في الهاتف:", title="سحب").get_input()
        if remote:
            local = filedialog.asksaveasfilename()
            if local:
                self._run([ADB, "pull", remote, local], "سحب")

    def _adb_push(self):
        local = filedialog.askopenfilename()
        if local:
            remote = ctk.CTkInputDialog(text="مسار في الهاتف:", title="إرسال").get_input()
            if remote:
                self._run([ADB, "push", local, remote], "إرسال")

    def _adb_backup(self):
        local = filedialog.asksaveasfilename(defaultextension=".ab")
        if local:
            self._log("📦 اقبل النسخ على الهاتف", "warn")
            self._run([ADB, "backup", "-apk", "-all", "-f", local], "نسخ احتياطي")

    def _adb_report(self):
        def worker():
            report = {}
            for p in ["ro.product.manufacturer", "ro.product.model", "ro.product.device",
                      "ro.build.version.release", "ro.serialno", "ro.hardware"]:
                r = subprocess.run([ADB, "shell", "getprop", p],
                                   capture_output=True, text=True, timeout=5)
                report[p.split(".")[-1]] = r.stdout.strip()
            fn = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(fn, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            self._log(f"✓ {fn}", "success")
        threading.Thread(target=worker, daemon=True).start()

    def _adb_install(self):
        f = filedialog.askopenfilename(filetypes=[("APK", "*.apk")])
        if f:
            self._run([ADB, "install", "-r", f], f"تثبيت {os.path.basename(f)}")

    def _adb_uninstall(self):
        pkg = ctk.CTkInputDialog(text="اسم الحزمة:", title="إزالة").get_input()
        if pkg:
            self._run([ADB, "uninstall", pkg], f"إزالة {pkg}")

    def _adb_disable_bloat(self):
        pkg = ctk.CTkInputDialog(text="اسم حزمة النظام:", title="تعطيل").get_input()
        if pkg:
            self._run([ADB, "shell", "pm", "disable-user", "--user", "0", pkg], "تعطيل")

    def _adb_enable_bloat(self):
        pkg = ctk.CTkInputDialog(text="اسم الحزمة:", title="تفعيل").get_input()
        if pkg:
            self._run([ADB, "shell", "pm", "enable", pkg], "تفعيل")

    def _adb_factory_reset(self):
        if messagebox.askyesno("🚨 تحذير", "هذا سيمسح كل شيء!\nمتأكد؟"):
            if messagebox.askyesno("تأكيد أخير", "آخر فرصة؟"):
                self._run([ADB, "shell", "am", "broadcast", "-a",
                           "android.intent.action.MASTER_CLEAR"], "ضبط المصنع")

    def _adb_edl(self):
        if messagebox.askyesno("⚠️ تحذير", "قد يعلق الهاتف!\nمتأكد؟"):
            self._run([ADB, "shell", "reboot", "edl"], "دخول EDL")

    # ==================== Fastboot ====================
    def _fb_devices(self): self._run([FASTBOOT, "devices"], "أجهزة Fastboot")
    def _fb_getvar(self): self._run([FASTBOOT, "getvar", "product"], "متغير المنتج")
    def _fb_all_vars(self): self._run([FASTBOOT, "getvar", "all"], "كل المتغيرات")
    def _fb_reboot(self): self._run([FASTBOOT, "reboot"], "إعادة تشغيل")
    def _fb_recovery(self): self._run([FASTBOOT, "reboot", "recovery"], "Recovery")
    def _fb_bootloader(self): self._run([FASTBOOT, "reboot", "bootloader"], "Bootloader")

    # ==================== MTK ====================
    def _mtk_info(self): self._run([sys.executable, "-m", "mtkclient", "printgpt"], "MTK GPT")
    def _mtk_dump_boot(self): self._run([sys.executable, "-m", "mtkclient", "r", "boot", "boot.bin"], "سحب boot")
    def _mtk_unlock(self):
        if messagebox.askyesno("تحذير", "فك Bootloader سيمسح البيانات!\nمتأكد؟"):
            self._run([sys.executable, "-m", "mtkclient", "unlock", "bootloader"], "فك القفل")
    def _mtk_custom(self):
        cmd = ctk.CTkInputDialog(text="أمر mtkclient:", title="مخصص").get_input()
        if cmd:
            self._run([sys.executable, "-m", "mtkclient"] + cmd.split(), "MTK مخصص")

    # ==================== EDL ====================
    def _edl_gpt(self): self._run([sys.executable, "-m", "edl", "printgpt"], "EDL GPT")
    def _edl_dump_boot(self): self._run([sys.executable, "-m", "edl", "r", "boot", "boot.bin"], "EDL boot")

    # ==================== Samsung ====================
    def _samsung_info(self):
        for p in ["ro.product.model", "ro.build.version.release", "ro.csc.country_code"]:
            self._run([ADB, "shell", "getprop", p], p)
    def _samsung_csc(self): self._run([ADB, "shell", "getprop", "ro.csc.sales_code"], "CSC")
    def _samsung_serial(self): self._run([ADB, "shell", "getprop", "ro.serialno"], "Serial")
    def _samsung_download(self):
        self._log("📲 Download Mode (تحذير على الهاتف)", "warn")
        self._run([ADB, "reboot", "download"], "Download Mode")
    def _samsung_bootloader(self): self._run([ADB, "reboot", "bootloader"], "Bootloader")
    def _samsung_recovery(self): self._run([ADB, "reboot", "recovery"], "Recovery")

    # ==================== Xiaomi ====================
    def _xiaomi_info(self):
        for p in ["ro.product.model", "ro.build.version.incremental", "ro.miui.ui.version.name"]:
            self._run([ADB, "shell", "getprop", p], p)
    def _xiaomi_bl_status(self): self._run([FASTBOOT, "oem", "device-info"], "Bootloader")
    def _xiaomi_fastboot(self): self._run([ADB, "reboot", "bootloader"], "Fastboot")
    def _xiaomi_edl(self):
        if messagebox.askyesno("⚠️ تحذير", "قد يعلق!\nمتأكد؟"):
            self._run([ADB, "reboot", "edl"], "EDL")

    # ==================== Huawei ====================
    def _huawei_info(self):
        for p in ["ro.product.model", "ro.build.version.release", "ro.build.display.id"]:
            self._run([ADB, "shell", "getprop", p], p)
    def _huawei_bl_info(self): self._run([FASTBOOT, "oem", "get-bootinfo"], "Bootloader Info")
    def _huawei_fastboot(self): self._run([ADB, "reboot", "bootloader"], "Fastboot")

    # ==================== Pixel ====================
    def _pixel_info(self):
        for p in ["ro.product.model", "ro.build.version.release", "ro.build.id"]:
            self._run([ADB, "shell", "getprop", p], p)
    def _pixel_bl_status(self): self._run([FASTBOOT, "getvar", "all"], "كل المتغيرات")
    def _pixel_fastboot(self): self._run([ADB, "reboot", "bootloader"], "Fastboot")

    # ==================== OnePlus ====================
    def _oneplus_info(self):
        for p in ["ro.product.model", "ro.build.version.ota", "ro.build.version.release"]:
            self._run([ADB, "shell", "getprop", p], p)
    def _oneplus_bl_status(self): self._run([FASTBOOT, "oem", "device-info"], "Bootloader")
    def _oneplus_fastboot(self): self._run([ADB, "reboot", "bootloader"], "Fastboot")

    # ==================== Motorola ====================
    def _motorola_info(self):
        for p in ["ro.product.model", "ro.build.version.release", "ro.carrier"]:
            self._run([ADB, "shell", "getprop", p], p)
    def _motorola_unlock_data(self): self._run([FASTBOOT, "oem", "get_unlock_data"], "Unlock Data")
    def _motorola_fastboot(self): self._run([ADB, "reboot", "bootloader"], "Fastboot")

    # ==================== Sony ====================
    def _sony_info(self):
        for p in ["ro.product.model", "ro.build.version.release", "ro.semc.version.cust"]:
            self._run([ADB, "shell", "getprop", p], p)
    def _sony_bl_status(self): self._run([FASTBOOT, "oem", "device-info"], "Bootloader")
    def _sony_fastboot(self): self._run([ADB, "reboot", "bootloader"], "Fastboot")

    # ==================== LG ====================
    def _lg_info(self):
        for p in ["ro.product.model", "ro.lge.swversion", "ro.build.version.release"]:
            self._run([ADB, "shell", "getprop", p], p)
    def _lg_download(self): self._run([ADB, "reboot", "download"], "Download Mode")

    # ==================== Oppo/Realme ====================
    def _oppo_info(self):
        for p in ["ro.product.model", "ro.build.version.ota", "ro.build.version.release"]:
            self._run([ADB, "shell", "getprop", p], p)
    def _oppo_fastboot(self): self._run([ADB, "reboot", "bootloader"], "Fastboot")
    def _oppo_edl(self):
        if messagebox.askyesno("⚠️ تحذير", "قد يعلق!\nمتأكد؟"):
            self._run([ADB, "reboot", "edl"], "EDL")

    # ==================== Vivo ====================
    def _vivo_info(self):
        for p in ["ro.product.model", "ro.vivo.os.version", "ro.build.version.release"]:
            self._run([ADB, "shell", "getprop", p], p)
    def _vivo_fastboot(self): self._run([ADB, "reboot", "bootloader"], "Fastboot")


if __name__ == "__main__":
    app = MyToolApp()
    app.mainloop()
