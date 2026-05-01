"""
Merkle Tree implementation for efficient codebase change detection.

This module builds
a cryptographic hash tree of the codebase to quickly identify which files
have changed since the last indexing operation.
"""

import hashlib
import json
import logging
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MerkleNode:
    """Represents a node in the Merkle tree (file or directory)."""
    
    path: str  # Relative path from root
    hash: str  # SHA-256 hash of content (or combined child hashes for directories)
    is_directory: bool
    size: int = 0  # File size in bytes (0 for directories)
    modified_time: Optional[str] = None  # ISO format timestamp
    children: Optional[List['MerkleNode']] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            'path': self.path,
            'hash': self.hash,
            'is_directory': self.is_directory,
            'size': self.size,
            'modified_time': self.modified_time,
        }
        if self.children:
            result['children'] = [child.to_dict() for child in self.children]
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MerkleNode':
        """Create MerkleNode from dictionary."""
        children = None
        if 'children' in data and data['children']:
            children = [cls.from_dict(child) for child in data['children']]
        
        return cls(
            path=data['path'],
            hash=data['hash'],
            is_directory=data['is_directory'],
            size=data.get('size', 0),
            modified_time=data.get('modified_time'),
            children=children
        )


@dataclass
class ChangeSet:
    """Represents changes detected between two Merkle trees."""
    
    added: List[str]  # New files
    modified: List[str]  # Changed files
    deleted: List[str]  # Removed files
    unchanged: List[str]  # Files that haven't changed
    
    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return bool(self.added or self.modified or self.deleted)
    
    def total_changes(self) -> int:
        """Total number of changed files."""
        return len(self.added) + len(self.modified) + len(self.deleted)
    
    def summary(self) -> str:
        """Human-readable summary of changes."""
        return (
            f"Added: {len(self.added)}, "
            f"Modified: {len(self.modified)}, "
            f"Deleted: {len(self.deleted)}, "
            f"Unchanged: {len(self.unchanged)}"
        )


class MerkleTree:
    """
    Builds and compares Merkle trees for efficient change detection.
    
    The tree structure mirrors the directory structure, with each node
    containing a hash of its content (for files) or combined child hashes
    (for directories). This allows quick identification of changes.
    """
    
    # File extensions to ignore
    IGNORE_EXTENSIONS = {
        '.pyc', '.pyo', '.pyd', '.so', '.dll', '.dylib',
        '.class', '.o', '.obj', '.exe', '.bin',
        '.git', '.svn', '.hg', '.DS_Store',
        '__pycache__', 'node_modules', '.venv', 'venv',
        '.egg-info', 'dist', 'build', '.pytest_cache',
        '.mypy_cache', '.tox', 'coverage', '.coverage'
    }
    
    def __init__(self, ignore_patterns: Optional[List[str]] = None):
        """
        Initialize Merkle tree builder.
        
        Args:
            ignore_patterns: Additional patterns to ignore (e.g., ['*.log', 'temp/*'])
        """
        self.ignore_patterns = ignore_patterns or []
    
    def _should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored."""
        # Check if any part of the path matches ignore extensions
        for part in path.parts:
            if part in self.IGNORE_EXTENSIONS:
                return True
        
        # Check file extension
        if path.suffix in self.IGNORE_EXTENSIONS:
            return True
        
        # Check custom patterns
        for pattern in self.ignore_patterns:
            if path.match(pattern):
                return True
        
        return False
    
    def _hash_file(self, file_path: Path) -> str:
        """
        Compute SHA-256 hash of a file's content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Hexadecimal hash string
        """
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            logger.warning(f"Failed to hash file {file_path}: {e}")
            # Return a hash of the error message to ensure consistency
            return hashlib.sha256(str(e).encode()).hexdigest()
    
    def _hash_directory(self, children: List[MerkleNode]) -> str:
        """
        Compute hash for a directory based on its children.
        
        Args:
            children: List of child MerkleNodes
            
        Returns:
            Combined hash of all children
        """
        # Sort children by path for consistency
        sorted_children = sorted(children, key=lambda x: x.path)
        
        # Combine all child hashes
        combined = ''.join(child.hash for child in sorted_children)
        
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def build_tree(self, root_path: str) -> MerkleNode:
        """
        Build a Merkle tree for the given directory.
        
        Args:
            root_path: Root directory to build tree from
            
        Returns:
            Root MerkleNode of the tree
        """
        root = Path(root_path).resolve()
        
        if not root.exists():
            raise ValueError(f"Path does not exist: {root_path}")
        
        logger.info(f"Building Merkle tree for: {root}")
        return self._build_node(root, root)
    
    def _build_node(self, path: Path, root: Path) -> MerkleNode:
        """
        Recursively build a MerkleNode for a path.
        
        Args:
            path: Current path to process
            root: Root directory (for computing relative paths)
            
        Returns:
            MerkleNode for this path
        """
        relative_path = str(path.relative_to(root))
        
        if path.is_file():
            # File node
            stat = path.stat()
            return MerkleNode(
                path=relative_path,
                hash=self._hash_file(path),
                is_directory=False,
                size=stat.st_size,
                modified_time=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                children=None
            )
        else:
            # Directory node
            children = []
            try:
                for child_path in sorted(path.iterdir()):
                    if self._should_ignore(child_path):
                        continue
                    
                    child_node = self._build_node(child_path, root)
                    children.append(child_node)
            except PermissionError:
                logger.warning(f"Permission denied: {path}")
            
            return MerkleNode(
                path=relative_path,
                hash=self._hash_directory(children),
                is_directory=True,
                size=0,
                modified_time=None,
                children=children
            )
    
    def compare_trees(self, old_tree: Optional[MerkleNode], new_tree: MerkleNode) -> ChangeSet:
        """
        Compare two Merkle trees to find changes.
        
        Args:
            old_tree: Previous tree snapshot (None if first time)
            new_tree: Current tree snapshot
            
        Returns:
            ChangeSet describing all changes
        """
        if old_tree is None:
            # First time indexing - all files are new
            all_files = self._collect_all_files(new_tree)
            return ChangeSet(
                added=all_files,
                modified=[],
                deleted=[],
                unchanged=[]
            )
        
        added: List[str] = []
        modified: List[str] = []
        deleted: List[str] = []
        unchanged: List[str] = []
        
        # Build path->node maps for efficient lookup
        old_files = self._build_file_map(old_tree)
        new_files = self._build_file_map(new_tree)
        
        # Find added and modified files
        for path, new_node in new_files.items():
            if path not in old_files:
                added.append(path)
            elif old_files[path].hash != new_node.hash:
                modified.append(path)
            else:
                unchanged.append(path)
        
        # Find deleted files
        for path in old_files:
            if path not in new_files:
                deleted.append(path)
        
        change_set = ChangeSet(
            added=sorted(added),
            modified=sorted(modified),
            deleted=sorted(deleted),
            unchanged=sorted(unchanged)
        )
        
        logger.info(f"Change detection complete: {change_set.summary()}")
        return change_set
    
    def _collect_all_files(self, node: MerkleNode) -> List[str]:
        """Collect all file paths from a tree."""
        files = []
        
        if not node.is_directory:
            files.append(node.path)
        elif node.children:
            for child in node.children:
                files.extend(self._collect_all_files(child))
        
        return files
    
    def _build_file_map(self, node: MerkleNode) -> Dict[str, MerkleNode]:
        """Build a map of file paths to nodes."""
        file_map = {}
        
        if not node.is_directory:
            file_map[node.path] = node
        elif node.children:
            for child in node.children:
                file_map.update(self._build_file_map(child))
        
        return file_map
    
    def save_snapshot(self, tree: MerkleNode, snapshot_path: str):
        """
        Save a Merkle tree snapshot to disk.
        
        Args:
            tree: MerkleNode to save
            snapshot_path: Path to save the snapshot JSON file
        """
        snapshot_file = Path(snapshot_path)
        snapshot_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(snapshot_file, 'w') as f:
            json.dump(tree.to_dict(), f, indent=2)
        
        logger.info(f"Saved Merkle tree snapshot to: {snapshot_path}")
    
    def load_snapshot(self, snapshot_path: str) -> Optional[MerkleNode]:
        """
        Load a Merkle tree snapshot from disk.
        
        Args:
            snapshot_path: Path to the snapshot JSON file
            
        Returns:
            MerkleNode or None if snapshot doesn't exist
        """
        snapshot_file = Path(snapshot_path)
        
        if not snapshot_file.exists():
            logger.info(f"No snapshot found at: {snapshot_path}")
            return None
        
        try:
            with open(snapshot_file, 'r') as f:
                data = json.load(f)
            
            tree = MerkleNode.from_dict(data)
            logger.info(f"Loaded Merkle tree snapshot from: {snapshot_path}")
            return tree
        except Exception as e:
            logger.error(f"Failed to load snapshot: {e}")
            return None


def get_changed_files(root_path: str, snapshot_path: str) -> ChangeSet:
    """
    Convenience function to detect changes since last snapshot.
    
    Args:
        root_path: Root directory of codebase
        snapshot_path: Path to previous snapshot file
        
    Returns:
        ChangeSet describing all changes
    """
    merkle = MerkleTree()
    
    # Load previous snapshot
    old_tree = merkle.load_snapshot(snapshot_path)
    
    # Build current tree
    new_tree = merkle.build_tree(root_path)
    
    # Compare
    changes = merkle.compare_trees(old_tree, new_tree)
    
    # Save new snapshot
    merkle.save_snapshot(new_tree, snapshot_path)
    
    return changes
