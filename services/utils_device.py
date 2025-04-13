# File: transcribe_audio_service/services/utils_device.py
import torch 
from cfg.conf_main import BATCH_SIZE_THRESHOLDS
import psutil
import platform

try:
    import pynvml
    pynvml.nvmlInit()
    GPU_AVAILABLE = True
    print("✔ GPU_AVAILABLE =", GPU_AVAILABLE)

    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    name = pynvml.nvmlDeviceGetName(handle).decode("utf-8")
    memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
    driver_version = pynvml.nvmlSystemGetDriverVersion().decode("utf-8")
    cuda_version = pynvml.nvmlSystemGetCudaDriverVersion()

    major = cuda_version // 1000
    minor = (cuda_version % 1000) // 10
    formatted_cuda_version = f"{major}.{minor}"

    GPU_INFO = {
        "name": name,
        "total_memory_MB": memory.total // 1024**2,
        "driver_version": driver_version,
        "cuda_version": formatted_cuda_version,
    }

    print(f"🧠 GPU Info: {GPU_INFO}")

except Exception as e:
    GPU_AVAILABLE = False
    GPU_INFO = {"error": str(e)}
    print("❌ GPU_AVAILABLE =", GPU_AVAILABLE)
    print("🔍 NVML Exception:", e)

def get_device_status():
    """Returns a tuple (device_str, cuda_available_bool)."""
    if torch.cuda.is_available():
        device = torch.cuda.get_device_name(0)
        return (device, True)
    return ("CPU", False)

def get_optimal_batch_size(vram_gb, using_gpu):
    if not using_gpu:
        return BATCH_SIZE_THRESHOLDS["low"]["batch_size"]

    if vram_gb >= BATCH_SIZE_THRESHOLDS["high"]["vram"]:
        return BATCH_SIZE_THRESHOLDS["high"]["batch_size"]
    elif vram_gb >= BATCH_SIZE_THRESHOLDS["medium"]["vram"]:
        return BATCH_SIZE_THRESHOLDS["medium"]["batch_size"]
    else:
        return BATCH_SIZE_THRESHOLDS["low"]["batch_size"]
    
def get_cpu_usage():
    name = platform.processor() or platform.uname().processor or "Unknown CPU"
    name_trimmed = name[:15] + "…" if len(name) > 15 else name
    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "cpu_cores": psutil.cpu_count(logical=True),
        "cpu_name": name_trimmed
    }


def get_ram_usage():
    mem = psutil.virtual_memory()
    return mem.percent, mem.used / (1024**3), mem.total / (1024**3)

def get_gpu_usage():
    if not GPU_AVAILABLE:
        return None
    try:
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        
        return {
            "gpu_percent": utilization.gpu,
            "mem_used": mem_info.used / (1024 ** 3),
            "mem_total": mem_info.total / (1024 ** 3),
            "gpu_temp": temp,  # 🌡️ Celsius
            "gpu_name": pynvml.nvmlDeviceGetName(handle).decode("utf-8"),
        }
        
    except:
        return None