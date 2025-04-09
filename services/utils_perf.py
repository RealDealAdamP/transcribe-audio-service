# File: transcribe_audio_service/services/utils_perf.py

import time
from contextlib import contextmanager

@contextmanager
def stage_timer(stage_name):
    start_time = time.time()
    print(f"⏳ Starting: {stage_name}...")
    yield
    duration = time.time() - start_time
    print(f"✅ Completed: {stage_name} in {duration:.2f} seconds")