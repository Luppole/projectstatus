import pytest
from utils.file_utils import count_lines, scan_directory
from rich.console import Console

@pytest.fixture
def console():
    return Console(force_terminal=True)

def test_count_lines(test_dir):
    """Test line counting functionality."""
    # Test Python file with comments and blank lines
    stats = count_lines(test_dir / 'test.py')
    assert stats['code'] == 1
    assert stats['blank'] == 1
    assert stats['comment'] == 1
    
    # Test JavaScript file
    stats = count_lines(test_dir / 'test.js')
    assert stats['code'] == 1
    assert stats['blank'] == 1
    assert stats['comment'] == 1
    
    # Test Java file with multiline structure
    stats = count_lines(test_dir / 'test.java')
    assert stats['code'] == 3
    assert stats['blank'] == 0
    assert stats['comment'] == 1

def test_scan_directory(test_dir, console):
    """Test directory scanning functionality."""
    # Test scanning with default settings
    file_stats, lang_stats = scan_directory(test_dir, console)
    
    # Check language statistics
    assert 'Python' in lang_stats
    assert 'JavaScript' in lang_stats
    assert 'Java' in lang_stats
    
    # Check file statistics
    assert len(file_stats) > 0
    assert any('test.py' in str(f) for f in file_stats.keys())
    assert any('test.js' in str(f) for f in file_stats.keys())

def test_scan_directory_with_exclusions(test_dir, console):
    """Test directory scanning with exclusions."""
    # Test scanning with excluded directories
    file_stats, lang_stats = scan_directory(
        test_dir,
        console,
        exclude_dirs=['__pycache__', 'node_modules']
    )
    
    # Verify excluded directories are not included
    assert not any('__pycache__' in str(f) for f in file_stats.keys())
    assert not any('node_modules' in str(f) for f in file_stats.keys())

def test_scan_directory_with_extensions(test_dir, console):
    """Test directory scanning with specific extensions."""
    # Test scanning only Python files
    file_stats, lang_stats = scan_directory(
        test_dir,
        console,
        include_extensions=['.py']
    )
    
    # Verify only Python files are included
    assert all(str(f).endswith('.py') for f in file_stats.keys())
    assert 'Python' in lang_stats
    assert 'JavaScript' not in lang_stats

def test_scan_directory_with_binary_files(test_dir, console):
    """Test directory scanning with binary files."""
    file_stats, lang_stats = scan_directory(test_dir, console)
    
    # Verify binary file is not included in statistics
    assert not any('test.bin' in str(f) for f in file_stats.keys())

def test_scan_directory_performance(large_test_dir, console):
    """Test directory scanning performance with many files."""
    import time
    
    start_time = time.time()
    file_stats, lang_stats = scan_directory(large_test_dir, console)
    end_time = time.time()
    
    # Verify all files were processed
    assert len(file_stats) == 1000
    assert 'Python' in lang_stats
    
    # Verify reasonable performance (should be under 5 seconds for 1000 files)
    assert end_time - start_time < 5.0 