"""
Path obfuscation module for privacy-preserving codebase indexing.

Implements HMAC-based path component hashing to mask sensitive file paths
while preserving directory structure for retrieval.
privacy features.
"""

import hashlib
import hmac
import json
import logging
import secrets
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class PathObfuscator:
    """
    Obfuscates file paths using HMAC-based hashing.
    
    Each path component (directory/file name) is hashed separately,
    preserving the directory structure while masking actual names.
    
    Example:
        src/payments/invoice_processor.py -> a9f3/x72k/qp1m8d.f4
    """
    
    def __init__(self, secret_key: Optional[str] = None, mapping_file: Optional[str] = None):
        """
        Initialize path obfuscator.
        
        Args:
            secret_key: Secret key for HMAC (auto-generated if not provided)
            mapping_file: File to store path mappings for decryption
        """
        self.secret_key = secret_key or self._generate_key()
        self.mapping_file = mapping_file or "chroma_db/.path_mapping.json"
        
        # Load existing mappings
        self.obfuscated_to_original: Dict[str, str] = {}
        self.original_to_obfuscated: Dict[str, str] = {}
        self._load_mappings()
    
    def _generate_key(self) -> str:
        """Generate a random secret key."""
        return secrets.token_hex(32)
    
    def _hash_component(self, component: str) -> str:
        """
        Hash a single path component using HMAC.
        
        Args:
            component: Path component (directory or file name)
            
        Returns:
            Hashed component (shortened for readability)
        """
        # Use HMAC-SHA256 for secure hashing
        h = hmac.new(
            self.secret_key.encode(),
            component.encode(),
            hashlib.sha256
        )
        
        # Take first 8 characters of hex digest for readability
        return h.hexdigest()[:8]
    
    def obfuscate_path(self, original_path: str) -> str:
        """
        Obfuscate a file path.
        
        Args:
            original_path: Original file path (e.g., "src/payments/invoice.py")
            
        Returns:
            Obfuscated path (e.g., "a9f3/x72k/qp1m8d.f4")
        """
        # Check if already obfuscated
        if original_path in self.original_to_obfuscated:
            return self.original_to_obfuscated[original_path]
        
        # Split path into components
        path_obj = Path(original_path)
        components = list(path_obj.parts)
        
        # Hash each component
        obfuscated_components = []
        for component in components:
            # Preserve file extension for type identification
            if '.' in component and component == components[-1]:
                # This is a file with extension
                name, ext = component.rsplit('.', 1)
                hashed_name = self._hash_component(name)
                # Shorten extension hash
                hashed_ext = self._hash_component(ext)[:2]
                obfuscated_components.append(f"{hashed_name}.{hashed_ext}")
            else:
                # Directory or file without extension
                obfuscated_components.append(self._hash_component(component))
        
        # Reconstruct path
        obfuscated_path = '/'.join(obfuscated_components)
        
        # Store mapping
        self.original_to_obfuscated[original_path] = obfuscated_path
        self.obfuscated_to_original[obfuscated_path] = original_path
        self._save_mappings()
        
        logger.debug(f"Obfuscated: {original_path} -> {obfuscated_path}")
        return obfuscated_path
    
    def deobfuscate_path(self, obfuscated_path: str) -> Optional[str]:
        """
        Deobfuscate a file path.
        
        Args:
            obfuscated_path: Obfuscated path
            
        Returns:
            Original path or None if not found
        """
        return self.obfuscated_to_original.get(obfuscated_path)
    
    def _load_mappings(self):
        """Load path mappings from disk."""
        mapping_path = Path(self.mapping_file)
        
        if not mapping_path.exists():
            logger.info(f"No existing path mappings found at {self.mapping_file}")
            return
        
        try:
            with open(mapping_path, 'r') as f:
                data = json.load(f)
            
            self.obfuscated_to_original = data.get('obfuscated_to_original', {})
            self.original_to_obfuscated = data.get('original_to_obfuscated', {})
            
            logger.info(f"Loaded {len(self.original_to_obfuscated)} path mappings")
        except Exception as e:
            logger.error(f"Failed to load path mappings: {e}")
    
    def _save_mappings(self):
        """Save path mappings to disk."""
        mapping_path = Path(self.mapping_file)
        mapping_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            data = {
                'obfuscated_to_original': self.obfuscated_to_original,
                'original_to_obfuscated': self.original_to_obfuscated,
                'secret_key': self.secret_key  # Store for consistency
            }
            
            with open(mapping_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(self.original_to_obfuscated)} path mappings")
        except Exception as e:
            logger.error(f"Failed to save path mappings: {e}")
    
    def clear_mappings(self):
        """Clear all path mappings."""
        self.obfuscated_to_original.clear()
        self.original_to_obfuscated.clear()
        
        mapping_path = Path(self.mapping_file)
        if mapping_path.exists():
            mapping_path.unlink()
        
        logger.info("Cleared all path mappings")
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about path mappings."""
        return {
            'total_paths': len(self.original_to_obfuscated),
            'unique_directories': len(set(
                str(Path(p).parent) for p in self.original_to_obfuscated.keys()
            ))
        }


# Global obfuscator instance
_obfuscator: Optional[PathObfuscator] = None


def get_obfuscator(
    secret_key: Optional[str] = None,
    mapping_file: Optional[str] = None
) -> PathObfuscator:
    """
    Get the global path obfuscator instance.
    
    Args:
        secret_key: Secret key for HMAC (auto-generated if not provided)
        mapping_file: File to store path mappings
        
    Returns:
        PathObfuscator instance
    """
    global _obfuscator
    
    if _obfuscator is None:
        _obfuscator = PathObfuscator(secret_key, mapping_file)
    
    return _obfuscator


def reset_obfuscator():
    """Reset the global obfuscator (useful for testing)."""
    global _obfuscator
    _obfuscator = None
