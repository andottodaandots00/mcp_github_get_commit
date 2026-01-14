"""
GPU Manager Module for Multi-GPU Handling.

This module provides comprehensive GPU management for document processing pipelines:
- GPU detection and information gathering
- Optimal device selection (CUDA, MPS, CPU)
- Multi-GPU allocation and work distribution
- CUDA stream management for async operations
- Memory monitoring and batch size optimization

Usage:
    from gpu_manager import GPUManager, WorkDistributor

    # Initialize GPU manager
    gpu_manager = GPUManager(device_preference="auto")

    # Get best available device
    device = gpu_manager.get_best_device()  # Returns "cuda:0", "mps", or "cpu"

    # Allocate multiple GPUs for parallel processing
    gpu_ids = gpu_manager.allocate_gpus(num_needed=2)

    # Distribute work across GPUs
    distributor = WorkDistributor(gpu_manager)
    chunks = distributor.split_workload(pdf_files, num_gpus=len(gpu_ids))
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

# Configure logging
_log = logging.getLogger(__name__)


# =============================================================================
# GPU Information Dataclass
# =============================================================================


@dataclass
class GPUInfo:
    """Information about a GPU device.

    Attributes:
        id: GPU device index (0, 1, 2, ...)
        name: GPU model name (e.g., "NVIDIA Tesla T4")
        total_memory: Total GPU memory in bytes
        free_memory: Available GPU memory in bytes
        utilization: Current GPU utilization as a fraction (0.0 to 1.0)
    """

    id: int
    name: str
    total_memory: int
    free_memory: int
    utilization: float

    @property
    def total_memory_gb(self) -> float:
        """Total memory in gigabytes."""
        return self.total_memory / (1024 ** 3)

    @property
    def free_memory_gb(self) -> float:
        """Free memory in gigabytes."""
        return self.free_memory / (1024 ** 3)

    @property
    def used_memory(self) -> int:
        """Used memory in bytes."""
        return self.total_memory - self.free_memory

    @property
    def used_memory_gb(self) -> float:
        """Used memory in gigabytes."""
        return self.used_memory / (1024 ** 3)

    @property
    def memory_utilization(self) -> float:
        """Memory utilization as a fraction (0.0 to 1.0)."""
        if self.total_memory == 0:
            return 0.0
        return self.used_memory / self.total_memory

    def __repr__(self) -> str:
        return (
            f"GPUInfo(id={self.id}, name='{self.name}', "
            f"memory={self.free_memory_gb:.1f}/{self.total_memory_gb:.1f}GB free, "
            f"utilization={self.utilization:.1%})"
        )


# =============================================================================
# GPU Manager Class
# =============================================================================


class GPUManager:
    """Manages GPU detection, selection, and allocation for processing pipelines.

    This class provides a unified interface for GPU management across different
    backends (CUDA, MPS, CPU) with proper error handling and fallback support.

    Attributes:
        device_preference: Preferred device type ("auto", "cuda", "cuda:N", "mps", "cpu")
        _cuda_available: Whether CUDA is available
        _mps_available: Whether MPS (Apple Metal) is available
        _xpu_available: Whether Intel XPU is available
        _gpu_count: Number of available CUDA GPUs
    """

    def __init__(self, device_preference: str = "auto") -> None:
        """Initialize the GPU manager.

        Args:
            device_preference: Preferred device type. Options:
                - "auto": Automatically detect best available device
                - "cpu": Force CPU execution
                - "cuda": Use default CUDA device (cuda:0)
                - "cuda:N": Use specific CUDA device N
                - "mps": Use Apple Metal (macOS only)
                - "xpu": Use Intel XPU
        """
        self.device_preference = device_preference.lower()
        self._cuda_available: bool = False
        self._mps_available: bool = False
        self._xpu_available: bool = False
        self._gpu_count: int = 0
        self._cuda_streams: Dict[int, List[Any]] = {}

        # Initialize device detection
        self._detect_available_backends()

        _log.info(
            f"GPUManager initialized: CUDA={self._cuda_available} ({self._gpu_count} GPUs), "
            f"MPS={self._mps_available}, XPU={self._xpu_available}"
        )

    def _detect_available_backends(self) -> None:
        """Detect available compute backends."""
        try:
            import torch

            # Check CUDA availability
            self._cuda_available = (
                torch.backends.cuda.is_built() and torch.cuda.is_available()
            )
            if self._cuda_available:
                self._gpu_count = torch.cuda.device_count()

            # Check MPS availability (Apple Metal)
            self._mps_available = (
                hasattr(torch.backends, 'mps') and
                torch.backends.mps.is_built() and
                torch.backends.mps.is_available()
            )

            # Check XPU availability (Intel)
            self._xpu_available = (
                hasattr(torch, 'xpu') and torch.xpu.is_available()
            )

        except ImportError:
            _log.warning("PyTorch not available. GPU features disabled.")
            self._cuda_available = False
            self._mps_available = False
            self._xpu_available = False
            self._gpu_count = 0

    @property
    def cuda_available(self) -> bool:
        """Check if CUDA is available."""
        return self._cuda_available

    @property
    def mps_available(self) -> bool:
        """Check if MPS (Apple Metal) is available."""
        return self._mps_available

    @property
    def xpu_available(self) -> bool:
        """Check if Intel XPU is available."""
        return self._xpu_available

    @property
    def gpu_count(self) -> int:
        """Get the number of available CUDA GPUs."""
        return self._gpu_count

    def detect_gpus(self) -> List[GPUInfo]:
        """Detect all available GPUs and return their information.

        Returns:
            List of GPUInfo objects for each available GPU.
            Returns empty list if no GPUs are available.
        """
        gpus: List[GPUInfo] = []

        if not self._cuda_available:
            _log.debug("No CUDA GPUs available.")
            return gpus

        try:
            import torch

            for device_id in range(self._gpu_count):
                try:
                    props = torch.cuda.get_device_properties(device_id)

                    # Get memory info (requires setting device context)
                    with torch.cuda.device(device_id):
                        free_memory, total_memory = torch.cuda.mem_get_info(device_id)

                    # Get utilization (try nvidia-smi approach, fallback to estimation)
                    utilization = self._get_gpu_utilization(device_id)

                    gpu_info = GPUInfo(
                        id=device_id,
                        name=props.name,
                        total_memory=total_memory,
                        free_memory=free_memory,
                        utilization=utilization,
                    )
                    gpus.append(gpu_info)
                    _log.debug(f"Detected GPU: {gpu_info}")

                except Exception as e:
                    _log.warning(f"Failed to get info for GPU {device_id}: {e}")

        except ImportError:
            _log.warning("PyTorch not available for GPU detection.")

        return gpus

    def _get_gpu_utilization(self, device_id: int) -> float:
        """Get GPU utilization for a specific device.

        Args:
            device_id: CUDA device index.

        Returns:
            GPU utilization as a fraction (0.0 to 1.0).
            Returns 0.0 if utilization cannot be determined.
        """
        try:
            # Try using pynvml if available (more accurate)
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(device_id)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            pynvml.nvmlShutdown()
            return util.gpu / 100.0
        except (ImportError, Exception):
            # Fallback: estimate from memory usage
            try:
                import torch
                with torch.cuda.device(device_id):
                    free, total = torch.cuda.mem_get_info(device_id)
                    return (total - free) / total if total > 0 else 0.0
            except Exception:
                return 0.0

    def get_best_device(self) -> str:
        """Get the optimal device based on preference and availability.

        Returns:
            Device string in PyTorch format:
            - "cuda:N" for CUDA GPUs
            - "mps" for Apple Metal
            - "xpu" for Intel XPU
            - "cpu" as fallback
        """
        # Handle explicit preferences first
        if self.device_preference == "cpu":
            return "cpu"

        # Handle specific CUDA device request
        if self.device_preference.startswith("cuda:"):
            if self._cuda_available:
                parts = self.device_preference.split(":")
                if len(parts) == 2 and parts[1].isdigit():
                    device_id = int(parts[1])
                    if device_id < self._gpu_count:
                        return f"cuda:{device_id}"
                    else:
                        _log.warning(
                            f"Requested CUDA device {device_id} not available "
                            f"(have {self._gpu_count} GPUs). Falling back to cuda:0."
                        )
                        return "cuda:0"
            _log.warning("CUDA requested but not available. Falling back to CPU.")
            return "cpu"

        # Handle generic CUDA request
        if self.device_preference == "cuda":
            if self._cuda_available:
                # Select GPU with most free memory
                return self._select_best_cuda_device()
            _log.warning("CUDA requested but not available. Falling back to CPU.")
            return "cpu"

        # Handle MPS request
        if self.device_preference == "mps":
            if self._mps_available:
                return "mps"
            _log.warning("MPS requested but not available. Falling back to CPU.")
            return "cpu"

        # Handle XPU request
        if self.device_preference == "xpu":
            if self._xpu_available:
                return "xpu"
            _log.warning("XPU requested but not available. Falling back to CPU.")
            return "cpu"

        # AUTO mode: priority CUDA > MPS > XPU > CPU
        if self._cuda_available:
            return self._select_best_cuda_device()
        if self._mps_available:
            return "mps"
        if self._xpu_available:
            return "xpu"

        return "cpu"

    def _select_best_cuda_device(self) -> str:
        """Select the best CUDA device based on free memory.

        Returns:
            Device string for the GPU with most free memory.
        """
        if self._gpu_count == 1:
            return "cuda:0"

        gpus = self.detect_gpus()
        if not gpus:
            return "cuda:0"

        # Sort by free memory (descending) and select the best
        best_gpu = max(gpus, key=lambda g: g.free_memory)
        _log.debug(f"Selected GPU {best_gpu.id} with {best_gpu.free_memory_gb:.1f}GB free")
        return f"cuda:{best_gpu.id}"

    def allocate_gpus(self, num_needed: int) -> List[int]:
        """Allocate GPUs for parallel work.

        Args:
            num_needed: Number of GPUs requested.

        Returns:
            List of GPU device IDs that can be used.
            Returns empty list if no GPUs available.
            Returns fewer GPUs if requested amount exceeds availability.
        """
        if not self._cuda_available or num_needed <= 0:
            return []

        available_gpus = self._gpu_count
        num_allocated = min(num_needed, available_gpus)

        if num_allocated < num_needed:
            _log.warning(
                f"Requested {num_needed} GPUs but only {available_gpus} available. "
                f"Allocating {num_allocated}."
            )

        # Get GPU info and sort by free memory
        gpus = self.detect_gpus()

        if gpus:
            # Allocate GPUs with most free memory first
            sorted_gpus = sorted(gpus, key=lambda g: g.free_memory, reverse=True)
            allocated_ids = [g.id for g in sorted_gpus[:num_allocated]]
        else:
            # Fallback: allocate sequentially
            allocated_ids = list(range(num_allocated))

        _log.info(f"Allocated GPUs: {allocated_ids}")
        return allocated_ids

    def get_memory_info(self, device_id: int = 0) -> Dict[str, Any]:
        """Get memory statistics for a specific GPU.

        Args:
            device_id: CUDA device index.

        Returns:
            Dictionary with memory statistics:
            - total: Total memory in bytes
            - free: Free memory in bytes
            - used: Used memory in bytes
            - total_gb: Total memory in GB
            - free_gb: Free memory in GB
            - used_gb: Used memory in GB
            - utilization: Memory utilization (0.0 to 1.0)

        Raises:
            RuntimeError: If CUDA is not available or device ID is invalid.
        """
        if not self._cuda_available:
            raise RuntimeError("CUDA is not available")

        if device_id < 0 or device_id >= self._gpu_count:
            raise RuntimeError(
                f"Invalid device ID {device_id}. Available: 0-{self._gpu_count - 1}"
            )

        try:
            import torch

            with torch.cuda.device(device_id):
                free_memory, total_memory = torch.cuda.mem_get_info(device_id)
                used_memory = total_memory - free_memory

                # Get allocated memory by PyTorch
                allocated = torch.cuda.memory_allocated(device_id)
                reserved = torch.cuda.memory_reserved(device_id)

                return {
                    "total": total_memory,
                    "free": free_memory,
                    "used": used_memory,
                    "total_gb": total_memory / (1024 ** 3),
                    "free_gb": free_memory / (1024 ** 3),
                    "used_gb": used_memory / (1024 ** 3),
                    "utilization": used_memory / total_memory if total_memory > 0 else 0.0,
                    "pytorch_allocated": allocated,
                    "pytorch_reserved": reserved,
                    "pytorch_allocated_gb": allocated / (1024 ** 3),
                    "pytorch_reserved_gb": reserved / (1024 ** 3),
                }
        except Exception as e:
            raise RuntimeError(f"Failed to get memory info for device {device_id}: {e}")

    def set_device(self, device_id: int) -> None:
        """Set the current CUDA device.

        Args:
            device_id: CUDA device index to set as current.

        Raises:
            RuntimeError: If CUDA is not available or device ID is invalid.
        """
        if not self._cuda_available:
            raise RuntimeError("CUDA is not available")

        if device_id < 0 or device_id >= self._gpu_count:
            raise RuntimeError(
                f"Invalid device ID {device_id}. Available: 0-{self._gpu_count - 1}"
            )

        try:
            import torch
            torch.cuda.set_device(device_id)

            # Also set environment variable for child processes
            os.environ["CUDA_VISIBLE_DEVICES"] = str(device_id)

            _log.debug(f"Set current CUDA device to {device_id}")
        except Exception as e:
            raise RuntimeError(f"Failed to set device {device_id}: {e}")

    def create_cuda_streams(self, num_streams: int, device_id: int = 0) -> List[Any]:
        """Create CUDA streams for asynchronous operations.

        CUDA streams allow overlapping compute and data transfer operations
        for improved GPU utilization.

        Args:
            num_streams: Number of streams to create.
            device_id: CUDA device to create streams on.

        Returns:
            List of torch.cuda.Stream objects.
            Returns empty list if CUDA is not available.
        """
        if not self._cuda_available:
            _log.warning("CUDA not available. Cannot create CUDA streams.")
            return []

        if num_streams <= 0:
            return []

        try:
            import torch

            streams = []
            with torch.cuda.device(device_id):
                for _ in range(num_streams):
                    streams.append(torch.cuda.Stream(device=device_id))

            # Cache streams for later synchronization
            self._cuda_streams[device_id] = streams

            _log.debug(f"Created {num_streams} CUDA streams on device {device_id}")
            return streams

        except Exception as e:
            _log.warning(f"Failed to create CUDA streams: {e}")
            return []

    def synchronize_all(self) -> None:
        """Wait for all GPU work to complete on all devices.

        This synchronizes all CUDA devices, ensuring all queued operations
        have completed before returning.
        """
        if not self._cuda_available:
            return

        try:
            import torch

            # Synchronize all devices
            for device_id in range(self._gpu_count):
                with torch.cuda.device(device_id):
                    torch.cuda.synchronize(device_id)

            _log.debug(f"Synchronized {self._gpu_count} CUDA device(s)")

        except Exception as e:
            _log.warning(f"Failed to synchronize devices: {e}")

    def synchronize_device(self, device_id: int = 0) -> None:
        """Wait for GPU work to complete on a specific device.

        Args:
            device_id: CUDA device index to synchronize.
        """
        if not self._cuda_available:
            return

        try:
            import torch

            with torch.cuda.device(device_id):
                torch.cuda.synchronize(device_id)

        except Exception as e:
            _log.warning(f"Failed to synchronize device {device_id}: {e}")

    def clear_cache(self, device_id: Optional[int] = None) -> None:
        """Clear GPU memory cache.

        Args:
            device_id: Specific device to clear, or None for all devices.
        """
        if not self._cuda_available:
            return

        try:
            import torch

            if device_id is not None:
                with torch.cuda.device(device_id):
                    torch.cuda.empty_cache()
                _log.debug(f"Cleared cache on device {device_id}")
            else:
                # Clear all devices
                for dev_id in range(self._gpu_count):
                    with torch.cuda.device(dev_id):
                        torch.cuda.empty_cache()
                _log.debug(f"Cleared cache on all {self._gpu_count} devices")

        except Exception as e:
            _log.warning(f"Failed to clear cache: {e}")

    def get_device_name(self, device_id: int = 0) -> str:
        """Get the name of a CUDA device.

        Args:
            device_id: CUDA device index.

        Returns:
            GPU name string, or "Unknown" if not available.
        """
        if not self._cuda_available:
            return "CPU"

        try:
            import torch
            return torch.cuda.get_device_name(device_id)
        except Exception:
            return "Unknown"

    def __repr__(self) -> str:
        return (
            f"GPUManager(preference='{self.device_preference}', "
            f"cuda={self._cuda_available}, gpus={self._gpu_count}, "
            f"mps={self._mps_available}, xpu={self._xpu_available})"
        )


# =============================================================================
# Work Distributor Class
# =============================================================================


class WorkDistributor:
    """Distributes workload across multiple GPUs for parallel processing.

    This class provides utilities for splitting work items across available
    GPUs, with support for both equal splitting and size-balanced distribution.

    Attributes:
        gpu_manager: GPUManager instance for GPU operations.
    """

    def __init__(self, gpu_manager: GPUManager) -> None:
        """Initialize the work distributor.

        Args:
            gpu_manager: GPUManager instance to use for GPU operations.
        """
        self.gpu_manager = gpu_manager

    def split_workload(
        self,
        items: List[Any],
        num_gpus: int,
    ) -> List[List[Any]]:
        """Split items evenly across GPUs.

        Distributes items as evenly as possible, with earlier chunks
        receiving any extra items when the count is not evenly divisible.

        Args:
            items: List of work items to distribute.
            num_gpus: Number of GPUs to distribute across.

        Returns:
            List of lists, where each inner list contains items for one GPU.

        Example:
            >>> distributor.split_workload([1, 2, 3, 4, 5], 2)
            [[1, 2, 3], [4, 5]]
        """
        if not items:
            return [[] for _ in range(max(1, num_gpus))]

        if num_gpus <= 0:
            return [items]

        if num_gpus == 1:
            return [items]

        # Calculate chunk sizes
        total_items = len(items)
        base_size = total_items // num_gpus
        remainder = total_items % num_gpus

        chunks: List[List[Any]] = []
        start_idx = 0

        for gpu_idx in range(num_gpus):
            # Earlier GPUs get one extra item if there's a remainder
            chunk_size = base_size + (1 if gpu_idx < remainder else 0)
            end_idx = start_idx + chunk_size
            chunks.append(items[start_idx:end_idx])
            start_idx = end_idx

        _log.debug(
            f"Split {total_items} items across {num_gpus} GPUs: "
            f"{[len(c) for c in chunks]}"
        )

        return chunks

    def balance_by_size(
        self,
        items: List[Any],
        sizes: List[int],
        num_gpus: int,
    ) -> List[List[Any]]:
        """Balance workload across GPUs by item size.

        Uses a greedy algorithm to distribute items so that each GPU
        receives approximately equal total work based on item sizes.
        Items are assigned to the GPU with the smallest current total.

        Args:
            items: List of work items to distribute.
            sizes: List of sizes corresponding to each item (e.g., file sizes, page counts).
            num_gpus: Number of GPUs to distribute across.

        Returns:
            List of lists, where each inner list contains items for one GPU.

        Raises:
            ValueError: If items and sizes have different lengths.

        Example:
            >>> items = ['small.pdf', 'large.pdf', 'medium.pdf']
            >>> sizes = [10, 100, 50]
            >>> distributor.balance_by_size(items, sizes, 2)
            [['large.pdf'], ['medium.pdf', 'small.pdf']]
        """
        if len(items) != len(sizes):
            raise ValueError(
                f"Items ({len(items)}) and sizes ({len(sizes)}) must have same length"
            )

        if not items:
            return [[] for _ in range(max(1, num_gpus))]

        if num_gpus <= 0:
            return [items]

        if num_gpus == 1:
            return [items]

        # Create item-size pairs and sort by size (descending)
        indexed_items = list(enumerate(zip(items, sizes)))
        indexed_items.sort(key=lambda x: x[1][1], reverse=True)

        # Initialize GPU buckets
        gpu_chunks: List[List[Any]] = [[] for _ in range(num_gpus)]
        gpu_totals: List[int] = [0] * num_gpus

        # Greedy assignment: assign largest items first to GPU with smallest total
        for _, (item, size) in indexed_items:
            # Find GPU with smallest current total
            min_gpu_idx = gpu_totals.index(min(gpu_totals))
            gpu_chunks[min_gpu_idx].append(item)
            gpu_totals[min_gpu_idx] += size

        _log.debug(
            f"Balanced {len(items)} items across {num_gpus} GPUs by size: "
            f"totals={gpu_totals}, counts={[len(c) for c in gpu_chunks]}"
        )

        return gpu_chunks

    def get_optimal_batch_size(
        self,
        gpu_memory: int,
        item_memory_estimate: int,
        safety_factor: float = 0.8,
        min_batch_size: int = 1,
        max_batch_size: int = 128,
    ) -> int:
        """Calculate optimal batch size based on available GPU memory.

        Estimates how many items can be processed in a single batch
        without exceeding available GPU memory.

        Args:
            gpu_memory: Available GPU memory in bytes.
            item_memory_estimate: Estimated memory required per item in bytes.
            safety_factor: Fraction of memory to actually use (default: 0.8).
            min_batch_size: Minimum batch size to return.
            max_batch_size: Maximum batch size to return.

        Returns:
            Optimal batch size within the specified range.

        Example:
            >>> # 8GB GPU, 100MB per item
            >>> distributor.get_optimal_batch_size(8 * 1024**3, 100 * 1024**2)
            64
        """
        if item_memory_estimate <= 0:
            _log.warning("Item memory estimate must be positive. Using min batch size.")
            return min_batch_size

        if gpu_memory <= 0:
            _log.warning("GPU memory must be positive. Using min batch size.")
            return min_batch_size

        # Calculate optimal batch size with safety margin
        usable_memory = int(gpu_memory * safety_factor)
        optimal_batch = usable_memory // item_memory_estimate

        # Clamp to valid range
        batch_size = max(min_batch_size, min(optimal_batch, max_batch_size))

        _log.debug(
            f"Calculated batch size: {batch_size} "
            f"(memory={gpu_memory / (1024**3):.1f}GB, "
            f"per_item={item_memory_estimate / (1024**2):.1f}MB)"
        )

        return batch_size

    def estimate_batch_sizes_per_gpu(
        self,
        item_memory_estimate: int,
        safety_factor: float = 0.8,
        min_batch_size: int = 1,
        max_batch_size: int = 128,
    ) -> Dict[int, int]:
        """Calculate optimal batch sizes for each available GPU.

        Args:
            item_memory_estimate: Estimated memory required per item in bytes.
            safety_factor: Fraction of memory to actually use.
            min_batch_size: Minimum batch size to return.
            max_batch_size: Maximum batch size to return.

        Returns:
            Dictionary mapping GPU ID to optimal batch size.
        """
        batch_sizes: Dict[int, int] = {}

        gpus = self.gpu_manager.detect_gpus()

        for gpu in gpus:
            batch_size = self.get_optimal_batch_size(
                gpu_memory=gpu.free_memory,
                item_memory_estimate=item_memory_estimate,
                safety_factor=safety_factor,
                min_batch_size=min_batch_size,
                max_batch_size=max_batch_size,
            )
            batch_sizes[gpu.id] = batch_size

        return batch_sizes

    def __repr__(self) -> str:
        return f"WorkDistributor(gpu_manager={self.gpu_manager})"


# =============================================================================
# Utility Functions
# =============================================================================


def get_default_gpu_manager(device_preference: str = "auto") -> GPUManager:
    """Create a default GPU manager instance.

    Args:
        device_preference: Preferred device type.

    Returns:
        Configured GPUManager instance.
    """
    return GPUManager(device_preference=device_preference)


def detect_best_device() -> str:
    """Quick utility to detect the best available device.

    Returns:
        Device string ("cuda:N", "mps", or "cpu").
    """
    manager = GPUManager(device_preference="auto")
    return manager.get_best_device()


def is_gpu_available() -> bool:
    """Check if any GPU is available.

    Returns:
        True if CUDA or MPS is available.
    """
    manager = GPUManager(device_preference="auto")
    return manager.cuda_available or manager.mps_available


def get_gpu_memory_gb(device_id: int = 0) -> float:
    """Get total GPU memory in gigabytes.

    Args:
        device_id: CUDA device index.

    Returns:
        Total GPU memory in GB, or 0.0 if not available.
    """
    manager = GPUManager(device_preference="auto")
    try:
        info = manager.get_memory_info(device_id)
        return info["total_gb"]
    except Exception:
        return 0.0


# =============================================================================
# Example Usage and Testing
# =============================================================================


if __name__ == "__main__":
    # Configure logging for demonstration
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    print("=" * 60)
    print("GPU Manager Module - Demo")
    print("=" * 60)

    # Create GPU manager
    manager = GPUManager(device_preference="auto")
    print(f"\nGPU Manager: {manager}")

    # Detect GPUs
    print("\n--- Detected GPUs ---")
    gpus = manager.detect_gpus()
    if gpus:
        for gpu in gpus:
            print(f"  {gpu}")
    else:
        print("  No GPUs detected")

    # Get best device
    print(f"\n--- Best Device ---")
    best_device = manager.get_best_device()
    print(f"  Best device: {best_device}")

    # Allocate GPUs
    print(f"\n--- GPU Allocation ---")
    allocated = manager.allocate_gpus(num_needed=2)
    print(f"  Allocated GPUs: {allocated}")

    # Work distribution
    print(f"\n--- Work Distribution ---")
    distributor = WorkDistributor(manager)

    # Test even split
    test_items = list(range(10))
    chunks = distributor.split_workload(test_items, num_gpus=3)
    print(f"  Split 10 items across 3 GPUs: {chunks}")

    # Test balanced split
    items = ["small", "large", "medium", "tiny", "huge"]
    sizes = [10, 100, 50, 5, 200]
    balanced = distributor.balance_by_size(items, sizes, num_gpus=2)
    print(f"  Balanced by size across 2 GPUs: {balanced}")

    # Test batch size calculation
    batch = distributor.get_optimal_batch_size(
        gpu_memory=16 * 1024**3,  # 16GB
        item_memory_estimate=256 * 1024**2,  # 256MB per item
    )
    print(f"  Optimal batch size (16GB GPU, 256MB/item): {batch}")

    print("\n" + "=" * 60)
    print("Demo Complete")
    print("=" * 60)
