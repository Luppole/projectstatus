import os
import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
from rich.progress import Progress, TaskID

class ParallelScanner:
    """Parallel file scanner using threads, processes, and async I/O."""
    
    def __init__(self, 
                 max_workers: Optional[int] = None,
                 use_processes: bool = False,
                 chunk_size: int = 1000):
        """Initialize the parallel scanner.
        
        Args:
            max_workers: Maximum number of workers. Defaults to CPU count.
            use_processes: Whether to use processes instead of threads.
            chunk_size: Number of files to process in each chunk.
        """
        self.max_workers = max_workers or os.cpu_count() or 4
        self.use_processes = use_processes
        self.chunk_size = chunk_size
        self.executor = (ProcessPoolExecutor if use_processes 
                        else ThreadPoolExecutor)(max_workers=self.max_workers)
    
    async def scan_files(self,
                        files: List[Path],
                        process_func: Callable[[Path], Dict[str, Any]],
                        progress: Optional[Progress] = None) -> Dict[Path, Dict[str, Any]]:
        """Scan files in parallel using async I/O and thread/process pools.
        
        Args:
            files: List of files to scan
            process_func: Function to process each file
            progress: Optional progress bar
            
        Returns:
            Dictionary mapping file paths to their statistics
        """
        results = {}
        task_id = None
        
        if progress:
            task_id = progress.add_task("Scanning files...", total=len(files))
        
        # Process files in chunks to avoid memory issues
        for i in range(0, len(files), self.chunk_size):
            chunk = files[i:i + self.chunk_size]
            
            # Create tasks for each file in the chunk
            tasks = []
            for file_path in chunk:
                # Read file content asynchronously
                async def process_file(file_path: Path) -> Dict[str, Any]:
                    try:
                        async with aiofiles.open(file_path, 'rb') as f:
                            content = await f.read()
                        # Process file in thread/process pool
                        loop = asyncio.get_event_loop()
                        result = await loop.run_in_executor(
                            self.executor,
                            process_func,
                            file_path
                        )
                        return result
                    except Exception as e:
                        return {'error': str(e)}
                
                tasks.append(process_file(file_path))
            
            # Wait for all tasks in the chunk to complete
            chunk_results = await asyncio.gather(*tasks)
            
            # Update results and progress
            for file_path, result in zip(chunk, chunk_results):
                results[file_path] = result
                if progress and task_id is not None:
                    progress.update(task_id, advance=1)
        
        return results
    
    def __del__(self):
        """Clean up executor on deletion."""
        self.executor.shutdown(wait=False) 