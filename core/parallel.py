import os
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Callable, Any

def set_gpu_for_worker(gpu_id: int) -> None:
    """Set CUDA_VISIBLE_DEVICES for current process."""
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)

def convert_pdf_worker(args: tuple) -> Any:
    """Worker function for parallel conversion."""
    pdf_path_str, gpu_id, config_dict, output_dir_str = args

    # Set GPU before imports
    set_gpu_for_worker(gpu_id)

    try:
        # Import inside worker to avoid side effects
        from core.pipeline import IntegratedPipeline
        from config.settings import ConversionConfig

        # Reconstruct config
        config = ConversionConfig(**config_dict)
        config.gpu.cuda_visible_devices = str(gpu_id)
        config.gpu.num_gpus = 1
        import os
        import multiprocessing as mp
        from concurrent.futures import ProcessPoolExecutor, as_completed
        from pathlib import Path
        from typing import List, Optional, Callable, Any


        def set_gpu_for_worker(gpu_id: int) -> None:
            """Set CUDA_VISIBLE_DEVICES for current process."""

            os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)


        def convert_pdf_worker(args: tuple) -> Any:
            """Worker function for parallel conversion using IntegratedPipeline."""

            pdf_path_str, gpu_id, config_dict, output_dir_str = args
            set_gpu_for_worker(gpu_id)

            from config.settings import ConversionConfig
            from core.pipeline import IntegratedPipeline

            config = ConversionConfig(**config_dict)
            pdf_path = Path(pdf_path_str)
            output_dir = Path(output_dir_str)

            with IntegratedPipeline(config) as pipeline:
                return pipeline.convert(pdf_path, output_dir=output_dir)


        def batch_convert_parallel(
            pdf_paths: List[Path],
            config: Any,  # ConversionConfig
            output_dir: Optional[Path] = None,
            num_gpus: int = 2,
            progress_callback: Optional[Callable[[str, Any], None]] = None,
        ) -> List[Any]:
            """Convert multiple PDFs in parallel across GPUs."""

            if not pdf_paths:
                return []

            target_output = Path(output_dir) if output_dir else Path(config.output_dir)
            config_dict = config.model_dump()

            work_items = [
                (str(pdf), i % num_gpus, config_dict, str(target_output))
                for i, pdf in enumerate(pdf_paths)
            ]

            results = []
            ctx = mp.get_context("spawn")

            with ProcessPoolExecutor(max_workers=num_gpus, mp_context=ctx) as executor:
                futures = {
                    executor.submit(convert_pdf_worker, item): item[0]
                    for item in work_items
                }

                for future in as_completed(futures):
                    pdf_path = futures[future]
                    try:
                        result = future.result()
                        results.append(result)
                        if progress_callback:
                            progress_callback(pdf_path, result)
                    except Exception as e:
                        print(f"Parallel conversion error for {pdf_path}: {e}")

            return results
