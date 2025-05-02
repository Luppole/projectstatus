import pytest
import time
from pathlib import Path
from utils.cache_utils import FileCache

def test_cache_initialization(tmp_path):
    """Test cache initialization."""
    cache = FileCache(cache_dir=tmp_path)
    assert cache.cache_dir == tmp_path
    assert tmp_path.exists()

def test_cache_save_and_load(test_dir, tmp_path):
    """Test saving and loading cache."""
    cache = FileCache(cache_dir=tmp_path)
    
    # Create some test stats
    stats = {
        'files': {
            str(test_dir / 'test.py'): {'lines': 10},
            str(test_dir / 'test.js'): {'lines': 20}
        }
    }
    
    # Save stats
    cache.save_stats(test_dir, stats)
    
    # Load stats
    loaded_stats = cache.get_cached_stats(test_dir)
    assert loaded_stats == stats

def test_cache_invalidation(test_dir, tmp_path):
    """Test cache invalidation when files change."""
    cache = FileCache(cache_dir=tmp_path)
    
    # Create initial stats
    stats = {
        'files': {
            str(test_dir / 'test.py'): {'lines': 10}
        }
    }
    
    # Save stats
    cache.save_stats(test_dir, stats)
    
    # Modify a file
    test_file = test_dir / 'test.py'
    test_file.write_text('print("Modified")\n')
    
    # Cache should be invalid
    assert cache.get_cached_stats(test_dir) is None

def test_cache_clear(tmp_path):
    """Test clearing cache."""
    cache = FileCache(cache_dir=tmp_path)
    
    # Create some cache files
    (tmp_path / 'test1.json').write_text('{}')
    (tmp_path / 'test2.json').write_text('{}')
    
    # Clear cache
    cache.clear_cache()
    
    # Check files are gone
    assert not list(tmp_path.glob('*.json'))

def test_cache_nonexistent_directory():
    """Test cache with nonexistent directory."""
    cache = FileCache()
    assert cache.get_cached_stats(Path('nonexistent')) is None

def test_cache_file_deletion(test_dir, tmp_path):
    """Test cache invalidation when files are deleted."""
    cache = FileCache(cache_dir=tmp_path)
    
    # Create initial stats
    stats = {
        'files': {
            str(test_dir / 'test.py'): {'lines': 10}
        }
    }
    
    # Save stats
    cache.save_stats(test_dir, stats)
    
    # Delete a file
    (test_dir / 'test.py').unlink()
    
    # Cache should be invalid
    assert cache.get_cached_stats(test_dir) is None

def test_cache_multiple_directories(test_dir, tmp_path):
    """Test caching multiple directories."""
    cache = FileCache(cache_dir=tmp_path)
    
    # Create stats for two directories
    dir1 = test_dir / 'dir1'
    dir2 = test_dir / 'dir2'
    dir1.mkdir()
    dir2.mkdir()
    
    stats1 = {'files': {str(dir1 / 'test.py'): {'lines': 10}}}
    stats2 = {'files': {str(dir2 / 'test.js'): {'lines': 20}}}
    
    # Save stats for both directories
    cache.save_stats(dir1, stats1)
    cache.save_stats(dir2, stats2)
    
    # Load stats for both directories
    assert cache.get_cached_stats(dir1) == stats1
    assert cache.get_cached_stats(dir2) == stats2 