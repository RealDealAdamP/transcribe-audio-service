# File: transcribe_audio_service/main.py
from services.dependency_check import check_dependencies
from gui.app import launch_app



if __name__ == "__main__":
    if not check_dependencies():
        exit()
    launch_app()