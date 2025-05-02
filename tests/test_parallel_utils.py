import pytest
import asyncio
from pathlib import Path
from utils.parallel_utils import ParallelScanner

def dummy_process_func(file_path: Path) -> dict:
    """Dummy function to process files."""
    return {'path': str(file_path), 'size': file_path.stat().st_size}

@pytest.mark.asyncio
async def test_parallel_scanner(test_dir):
    """Test parallel scanner with thread pool."""
    scanner = ParallelScanner(use_processes=False)
    files = list(test_dir.glob('*'))
    
    results = await scanner.scan_files(files, dummy_process_func)
    
    assert len(results) == len(files)
    for file_path, result in results.items():
        assert 'path' in result
        assert 'size' in result
        assert result['path'] == str(file_path)

@pytest.mark.asyncio
async def test_parallel_scanner_with_processes(test_dir):
    """Test parallel scanner with process pool."""
    scanner = ParallelScanner(use_processes=True)
    files = list(test_dir.glob('*'))
    
    results = await scanner.scan_files(files, dummy_process_func)
    
    assert len(results) == len(files)
    for file_path, result in results.items():
        assert 'path' in result
        assert 'size' in result
        assert result['path'] == str(file_path)

@pytest.mark.asyncio
async def test_parallel_scanner_with_progress(test_dir):
    """Test parallel scanner with progress bar."""
    from rich.progress import Progress
    
    scanner = ParallelScanner()
    files = list(test_dir.glob('*'))
    
    with Progress() as progress:
        results = await scanner.scan_files(files, dummy_process_func, progress)
    
    assert len(results) == len(files)

@pytest.mark.asyncio
async def test_parallel_scanner_with_errors(test_dir):
    """Test parallel scanner with file errors."""
    def error_func(file_path: Path) -> dict:
        raise Exception("Test error")
    
    scanner = ParallelScanner()
    files = list(test_dir.glob('*'))
    
    results = await scanner.scan_files(files, error_func)
    
    assert len(results) == len(files)
    for result in results.values():
        assert 'error' in result
        assert result['error'] == "Test error"

@pytest.mark.asyncio
async def test_parallel_scanner_performance(large_test_dir):
    """Test parallel scanner performance with many files."""
    import time
    
    scanner = ParallelScanner()
    files = list(large_test_dir.glob('*.py'))
    
    start_time = time.time()
    results = await scanner.scan_files(files, dummy_process_func)
    end_time = time.time()
    
    assert len(results) == len(files)
    # Should process 1000 files in under 5 seconds
    assert end_time - start_time < 5.0 