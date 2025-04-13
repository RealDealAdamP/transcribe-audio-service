# File: transcribe_audio_service/main.py
from ttkbootstrap import Window
from gui.ui_splash import SplashScreen
from services.version import __version__

if __name__ == "__main__":
    from services.dependency_check import check_dependencies
    if not check_dependencies():
        exit()

    root = Window(themename="darkly")

    # 🖼️ Pre-set main window geometry (but keep hidden for now)
    root.geometry("1400x950")
    root.title(f"Transcribe Audio Service v{__version__}")
    root.resizable(False, False)
    root.update_idletasks()  # Ensure winfo_* methods return correct values
    root.withdraw()          # Hide until splash completes

    # 🪄 Center splash relative to main window
    splash = SplashScreen(root)
    splash.show()

    def finish_loading():
       
        splash.set_progress(25)
        from gui.ui_main import TranscribeApp
        splash.set_progress(50)
        from gui.app import launch_app
        
        splash.set_progress(75)
        app = launch_app(root)
        app.initialize_ui()

        splash.set_progress(100)
        splash.close()  # ✅ This shows the main window

    root.after(100, finish_loading)
    root.mainloop()
