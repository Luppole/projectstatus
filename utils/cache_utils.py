import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

class FileCache:
    """Cache for file statistics to enable incremental scanning."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize the cache.
        
        Args:
            cache_dir: Directory to store cache files. Defaults to .projectstatus/cache
        """
        if cache_dir is None:
            cache_dir = Path('.projectstatus/cache')
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_cache_path(self, directory: Path) -> Path:
        """Get the cache file path for a directory."""
        # Create a unique hash for the directory path
        dir_hash = hashlib.md5(str(directory.absolute()).encode()).hexdigest()
        return self.cache_dir / f"{dir_hash}.json"
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate a hash for a file based on its content and modification time."""
        stat = file_path.stat()
        # Combine file size and modification time for quick change detection
        return f"{stat.st_size}:{stat.st_mtime}"
    
    def get_cached_stats(self, directory: Path) -> Optional[Dict[str, Any]]:
        """Get cached statistics for a directory if they exist and are valid."""
        cache_path = self._get_cache_path(directory)
        if not cache_path.exists():
            return None
            
        try:
            with open(cache_path) as f:
                cache_data = json.load(f)
                
            # Check if any files have changed
            for file_path, file_hash in cache_data['file_hashes'].items():
                path = Path(file_path)
                if not path.exists() or self._get_file_hash(path) != file_hash:
                    return None
                    
            return cache_data['stats']
        except (json.JSONDecodeError, KeyError):
            return None
    
    def save_stats(self, directory: Path, stats: Dict[str, Any]) -> None:
        """Save statistics to cache."""
        cache_path = self._get_cache_path(directory)
        
        # Calculate hashes for all files
        file_hashes = {}
        for file_path in stats.get('files', {}).keys():
            path = Path(file_path)
            if path.exists():
                file_hashes[str(path)] = self._get_file_hash(path)
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'directory': str(directory.absolute()),
            'file_hashes': file_hashes,
            'stats': stats
        }
        
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        for cache_file in self.cache_dir.glob('*.json'):
            cache_file.unlink() 