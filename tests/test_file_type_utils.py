import pytest
from utils.file_type_utils import is_binary_file, get_file_info, get_mime_type

def test_binary_file_detection(test_dir):
    """Test binary file detection."""
    # Test binary file
    assert is_binary_file(test_dir / 'test.bin')
    
    # Test text files
    assert not is_binary_file(test_dir / 'test.py')
    assert not is_binary_file(test_dir / 'test.js')
    assert not is_binary_file(test_dir / 'test.txt')

def test_mime_type_detection(test_dir):
    """Test MIME type detection."""
    # Test various file types
    assert 'text/x-python' in get_mime_type(test_dir / 'test.py')
    assert 'text/javascript' in get_mime_type(test_dir / 'test.js')
    assert 'text/plain' in get_mime_type(test_dir / 'test.txt')
    assert 'application/octet-stream' in get_mime_type(test_dir / 'test.bin')

def test_language_detection(test_dir):
    """Test language detection from file info."""
    # Test Python file
    mime, ext, lang = get_file_info(test_dir / 'test.py')
    assert lang == 'Python'
    assert ext == '.py'
    
    # Test JavaScript file
    mime, ext, lang = get_file_info(test_dir / 'test.js')
    assert lang == 'JavaScript'
    assert ext == '.js'
    
    # Test Java file
    mime, ext, lang = get_file_info(test_dir / 'test.java')
    assert lang == 'Java'
    assert ext == '.java'
    
    # Test C++ file
    mime, ext, lang = get_file_info(test_dir / 'test.cpp')
    assert lang == 'C++'
    assert ext == '.cpp'
    
    # Test shell script
    mime, ext, lang = get_file_info(test_dir / 'test.sh')
    assert lang == 'Shell'
    assert ext == '.sh'
    
    # Test binary file
    mime, ext, lang = get_file_info(test_dir / 'test.bin')
    assert lang is None
    assert ext == '.bin'

def test_nonexistent_file():
    """Test handling of nonexistent files."""
    with pytest.raises(FileNotFoundError):
        get_file_info('nonexistent.txt')

def test_file_without_extension(test_dir):
    """Test files without extensions."""
    file_path = test_dir / 'testfile'
    file_path.write_text('print("Hello")')
    
    mime, ext, lang = get_file_info(file_path)
    assert ext == ''
    assert lang is None  # Should not detect language without extension 