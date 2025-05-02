import pytest
import subprocess
import os
from pathlib import Path

def test_cli_help():
    """Test CLI help command."""
    result = subprocess.run(['python', 'main.py', '--help'], 
                          capture_output=True, text=True)
    assert result.returncode == 0
    assert 'usage:' in result.stdout.lower()
    assert '--help' in result.stdout

def test_cli_version():
    """Test CLI version command."""
    result = subprocess.run(['python', 'main.py', '--version'], 
                          capture_output=True, text=True)
    assert result.returncode == 0
    assert 'version' in result.stdout.lower()

def test_cli_scan_directory(test_dir):
    """Test CLI scan command with directory."""
    result = subprocess.run(['python', 'main.py', 'scan', str(test_dir)], 
                          capture_output=True, text=True)
    assert result.returncode == 0
    assert 'Python' in result.stdout
    assert 'JavaScript' in result.stdout

def test_cli_scan_nonexistent_directory():
    """Test CLI scan command with nonexistent directory."""
    result = subprocess.run(['python', 'main.py', 'scan', 'nonexistent'], 
                          capture_output=True, text=True)
    assert result.returncode != 0
    assert 'error' in result.stderr.lower()

def test_cli_scan_with_exclusions(test_dir):
    """Test CLI scan command with exclusions."""
    result = subprocess.run([
        'python', 'main.py', 'scan', 
        '--exclude', '__pycache__', 
        '--exclude', 'node_modules',
        str(test_dir)
    ], capture_output=True, text=True)
    assert result.returncode == 0
    assert '__pycache__' not in result.stdout

def test_cli_scan_with_extensions(test_dir):
    """Test CLI scan command with specific extensions."""
    result = subprocess.run([
        'python', 'main.py', 'scan',
        '--extensions', '.py',
        str(test_dir)
    ], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'Python' in result.stdout
    assert 'JavaScript' not in result.stdout

def test_cli_scan_with_output_file(test_dir, tmp_path):
    """Test CLI scan command with output file."""
    output_file = tmp_path / 'output.json'
    result = subprocess.run([
        'python', 'main.py', 'scan',
        '--output', str(output_file),
        str(test_dir)
    ], capture_output=True, text=True)
    assert result.returncode == 0
    assert output_file.exists()
    assert output_file.stat().st_size > 0

def test_cli_scan_with_invalid_options(test_dir):
    """Test CLI scan command with invalid options."""
    result = subprocess.run([
        'python', 'main.py', 'scan',
        '--invalid-option',
        str(test_dir)
    ], capture_output=True, text=True)
    assert result.returncode != 0
    assert 'error' in result.stderr.lower()

def test_cli_scan_with_empty_directory(tmp_path):
    """Test CLI scan command with empty directory."""
    result = subprocess.run(['python', 'main.py', 'scan', str(tmp_path)], 
                          capture_output=True, text=True)
    assert result.returncode == 0
    assert 'No files found' in result.stdout

def test_cli_scan_with_symlinks(test_dir, tmp_path):
    """Test CLI scan command with symlinks."""
    # Create a symlink to the test directory
    symlink_path = tmp_path / 'symlink'
    os.symlink(test_dir, symlink_path)
    
    result = subprocess.run(['python', 'main.py', 'scan', str(symlink_path)], 
                          capture_output=True, text=True)
    assert result.returncode == 0
    assert 'Python' in result.stdout
``` 