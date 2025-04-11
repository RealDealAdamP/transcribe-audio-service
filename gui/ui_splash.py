# File: gui/ui_splash.py

from ttkbootstrap import Label, Progressbar, Toplevel
from services.utils_device import GPU_AVAILABLE, GPU_INFO
from gui.style_config import get_theme_style, get_bootstyles
from services.version import __version__


class SplashScreen:
    def __init__(self, root):
        self.root = root
        self.splash = None
        self.progress = None
        self.text_label = None
        self.title_label = None
        self.style, self.fonts = get_theme_style()
        self.bootstyles = get_bootstyles().get("splash", {})

    def show(self):
        # 🧮 Center splash relative to root
        self.root.update_idletasks()
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()

        splash_width = 800
        splash_height = 400
        splash_x = root_x + (root_width - splash_width) // 2
        splash_y = root_y + (root_height - splash_height) // 2

        # 🖼️ Create splash window
        self.splash = Toplevel(self.root)
        self.splash.overrideredirect(True)
        self.splash.geometry(f"{splash_width}x{splash_height}+{splash_x}+{splash_y}")
        self.splash.configure(bg="#191919")
        self.splash.lift()
        self.splash.attributes("-topmost", True)

        # ─── Title Label ─────────────────────────────
        self.title_label = Label(
            self.splash,
            text="Transcribe Audio Service",
            font=self.fonts["label"],
            bootstyle=self.bootstyles.get("label_title", "info"),
            anchor="center",
            justify="center"
        )
        self.title_label.pack(pady=(20, 10))

        # ─── GPU Info Display ────────────────────────
        gpu_text = (
            f"✔ GPU_AVAILABLE = True\n🧠 GPU Info: {GPU_INFO}"
            if GPU_AVAILABLE else
            f"❌ GPU_AVAILABLE = False\n🔍 {GPU_INFO.get('error', 'Unavailable')}"
        )
        self.text_label = Label(
            self.splash,
            text=gpu_text,
            font=self.fonts["label"],
            bootstyle=self.bootstyles.get("label_status", "secondary"),
            justify="center"
        )
        self.text_label.pack(pady=(0, 15))

        # ─── Progress Bar ────────────────────────────
        self.progress = Progressbar(
            self.splash,
            mode='determinate',
            bootstyle=self.bootstyles.get("progressbar", "primary-striped"),
            length=300,
            maximum=100
        )
        self.progress.pack(pady=(0, 20))
        self.progress.start(10)

    def set_progress(self, value):
        if self.progress:
            self.progress.stop()
            self.progress.config(mode="determinate")
            self.progress["value"] = value
            self.splash.update_idletasks()

    def close(self):
        if self.progress:
            self.progress.stop()
        if self.splash:
            self.splash.destroy()
        self.root.deiconify()  # Reveal main UI window

