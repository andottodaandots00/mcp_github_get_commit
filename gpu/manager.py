"""GPU manager wrapper module.

This module provides wrapper functions around the existing GPUManager
from the parent folder, adapting it for use with Docling's accelerator
device configuration and providing optimized batch size recommendations
based on available GPU memory.

Example usage:
    >>> device = get_accelerator_device(preference="cuda")
    >>> batch_sizes = get_optimal_batch_sizes(memory_gb=16.0)
    >>> manager = get_gpu_manager(preference="auto")
"""

from pathlib import Path
from typing import Dict, Optional
import sys
import os
import logging

# Add parent directory to path to import GPUManager
sys.path.insert(0, str(Path(__file__).parent.parent))
from gpu_manager import GPUManager, GPUInfo
from docling.datamodel.accelerator_options import AcceleratorDevice

logger = logging.getLogger(__name__)


def setup_gpu_environment(config) -> None:
    """Configure CUDA environment variables.

    Args:
        config: GPU configuration with device settings (GPUConfig)
    """
    if hasattr(config, 'cuda_visible_devices') and config.cuda_visible_devices:
        os.environ["CUDA_VISIBLE_DEVICES"] = str(config.cuda_visible_devices)
        logger.info(f"Set CUDA_VISIBLE_DEVICES={config.cuda_visible_devices}")

    if hasattr(config, 'num_threads'):
        os.environ["OMP_NUM_THREADS"] = str(config.num_threads)
        os.environ["NUMEXPR_MAX_THREADS"] = str(config.num_threads)

    # Suppress TensorFlow warnings
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

    num_gpus = getattr(config, 'num_gpus', 'unknown')
    num_threads = getattr(config, 'num_threads', 'unknown')
    logger.info(f"GPU environment configured: {num_gpus} GPUs, {num_threads} threads")


def get_accelerator_device(preference: str = "auto") -> AcceleratorDevice:
    """Get the appropriate AcceleratorDevice based on available hardware.

    This function detects available GPU hardware and returns the corresponding
    Docling AcceleratorDevice enum value. It leverages the GPUManager to
    determine the best available device based on the preference.

    Args:
        preference: Device preference string. Options:
            - "auto": Automatically select best available device
            - "cuda": Prefer NVIDIA CUDA devices
            - "mps": Prefer Apple Metal Performance Shaders
            - "cpu": Force CPU usage

    Returns:
        AcceleratorDevice enum value corresponding to the best available device.

    Examples:
        >>> device = get_accelerator_device(preference="auto")
        >>> print(device)
        AcceleratorDevice.CUDA

        >>> device = get_accelerator_device(preference="cpu")
        >>> print(device)
        AcceleratorDevice.CPU
    """
    # Create GPUManager instance with specified preference
    manager = GPUManager(device_preference=preference)

    # Get the best available device string
    device_str = manager.get_best_device()

    # Map device string to AcceleratorDevice enum
    if device_str == "cpu":
        return AcceleratorDevice.CPU
    elif device_str == "cuda" or device_str.startswith("cuda:"):
        return AcceleratorDevice.CUDA
    elif device_str == "mps":
        return AcceleratorDevice.MPS
    elif device_str == "xpu":
        return AcceleratorDevice.XPU
    else:
        return AcceleratorDevice.AUTO


def get_optimal_batch_sizes(memory_gb: float) -> Dict[str, int]:
    """Get optimal batch sizes for different processing tasks based on available memory.

    Returns recommended batch sizes for OCR, layout analysis, and table recognition
    tasks based on the amount of GPU memory available. These values are tuned
    for typical PDF processing workloads with Docling.

    Args:
        memory_gb: Available GPU memory in gigabytes.

    Returns:
        Dictionary with batch sizes for 'ocr', 'layout', and 'table' tasks.

    Examples:
        >>> batch_sizes = get_optimal_batch_sizes(memory_gb=16.0)
        >>> print(batch_sizes)
        {'ocr': 32, 'layout': 64, 'table': 4}

        >>> batch_sizes = get_optimal_batch_sizes(memory_gb=4.0)
        >>> print(batch_sizes)
        {'ocr': 8, 'layout': 16, 'table': 2}
    """
    if memory_gb >= 14:
        return {"ocr": 32, "layout": 64, "table": 4}
    elif memory_gb >= 8:
        return {"ocr": 16, "layout": 32, "table": 2}
    else:
        return {"ocr": 8, "layout": 16, "table": 2}


def get_gpu_manager(preference: str = "auto") -> GPUManager:
    """Get a configured GPUManager instance.

    Simple wrapper function that creates and returns a GPUManager instance
    with the specified device preference.

    Args:
        preference: Device preference string ("auto", "cuda", "mps", "cpu").

    Returns:
        Configured GPUManager instance.

    Examples:
        >>> manager = get_gpu_manager(preference="cuda")
        >>> device = manager.get_best_device()
        >>> info = manager.get_gpu_info()
    """
    return GPUManager(device_preference=preference)
