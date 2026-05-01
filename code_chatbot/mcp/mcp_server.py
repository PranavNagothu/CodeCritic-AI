"""
MCP (Model Context Protocol) Server for Code Refactoring.

Provides tools for code search, refactoring, and analysis via MCP protocol.
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import ast

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Result from code search"""
    file_path: str
    line_number: int
    line_content: str
    context_before: List[str]
    context_after: List[str]
    match_start: int
    match_end: int


@dataclass
class RefactorResult:
    """Result from code refactoring"""
    files_changed: int
    total_replacements: int
    changes: List[Dict[str, any]]
    dry_run: bool
    success: bool
    error: Optional[str] = None


@dataclass
class RefactorSuggestion:
    """Suggested refactoring"""
    type: str  # 'extract_function', 'rename', 'simplify', etc.
    file_path: str
    line_start: int
    line_end: int
    description: str
    rationale: str
    estimated_impact: str  # 'low', 'medium', 'high'


class RefactorMCPServer:
    """
    MCP server providing code refactoring tools.
    
    Tools:
    - code_search: Search for patterns in codebase
    - code_refactor: Perform regex-based refactoring
    - suggest_refactorings: Analyze code and suggest improvements
    """
    
    def __init__(self, workspace_root: str):
        """
        Initialize MCP server.
        
        Args:
            workspace_root: Root directory of the codebase
        """
        self.workspace_root = Path(workspace_root)
        
        # Default ignore patterns
        self.ignore_patterns = [
            '**/__pycache__/**',
            '**/*.pyc',
            '**/node_modules/**',
            '**/.git/**',
            '**/venv/**',
            '**/.venv/**',
            '**/dist/**',
            '**/build/**',
            '**/*.egg-info/**'
        ]
    
    def code_search(
        self,
        pattern: str,
        file_pattern: str = "**/*.py",
        context_lines: int = 2,
        is_regex: bool = True
    ) -> List[SearchResult]:
        """
        Search for patterns in codebase.
        
        Args:
            pattern: Search pattern (regex or literal)
            file_pattern: Glob pattern for files to search
            context_lines: Number of context lines before/after match
            is_regex: Whether pattern is regex
            
        Returns:
            List of search results
        """
        results = []
        
        # Compile regex pattern
        try:
            if is_regex:
                regex = re.compile(pattern)
            else:
                regex = re.compile(re.escape(pattern))
        except re.error as e:
            logger.error(f"Invalid regex pattern: {e}")
            return results
        
        # Find matching files
        files = self._find_files(file_pattern)
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                # Search each line
                for line_num, line in enumerate(lines, start=1):
                    match = regex.search(line)
                    if match:
                        # Get context
                        start_idx = max(0, line_num - context_lines - 1)
                        end_idx = min(len(lines), line_num + context_lines)
                        
                        context_before = [l.rstrip() for l in lines[start_idx:line_num-1]]
                        context_after = [l.rstrip() for l in lines[line_num:end_idx]]
                        
                        results.append(SearchResult(
                            file_path=str(file_path.relative_to(self.workspace_root)),
                            line_number=line_num,
                            line_content=line.rstrip(),
                            context_before=context_before,
                            context_after=context_after,
                            match_start=match.start(),
                            match_end=match.end()
                        ))
            
            except Exception as e:
                logger.error(f"Error searching {file_path}: {e}")
        
        logger.info(f"Found {len(results)} matches for pattern '{pattern}'")
        return results
    
    def code_refactor(
        self,
        search_pattern: str,
        replace_pattern: str,
        file_pattern: str = "**/*.py",
        dry_run: bool = True,
        is_regex: bool = True
    ) -> RefactorResult:
        """
        Perform regex-based code refactoring.
        
        Args:
            search_pattern: Pattern to search for
            replace_pattern: Replacement string (supports capture groups)
            file_pattern: Glob pattern for files to process
            dry_run: If True, only show what would change
            is_regex: Whether pattern is regex
            
        Returns:
            RefactorResult with changes made or to be made
        """
        changes = []
        files_changed = 0
        total_replacements = 0
        
        try:
            # Compile regex
            if is_regex:
                regex = re.compile(search_pattern)
            else:
                regex = re.compile(re.escape(search_pattern))
        except re.error as e:
            return RefactorResult(
                files_changed=0,
                total_replacements=0,
                changes=[],
                dry_run=dry_run,
                success=False,
                error=f"Invalid regex: {e}"
            )
        
        # Find matching files
        files = self._find_files(file_pattern)
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    original_content = f.read()
                
                # Perform replacement
                new_content, num_replacements = regex.subn(replace_pattern, original_content)
                
                if num_replacements > 0:
                    files_changed += 1
                    total_replacements += num_replacements
                    
                    # Record change
                    change = {
                        'file_path': str(file_path.relative_to(self.workspace_root)),
                        'replacements': num_replacements,
                        'preview': self._generate_diff_preview(original_content, new_content)
                    }
                    changes.append(change)
                    
                    # Apply change if not dry run
                    if not dry_run:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        logger.info(f"Applied {num_replacements} replacements to {file_path}")
            
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
        
        result = RefactorResult(
            files_changed=files_changed,
            total_replacements=total_replacements,
            changes=changes,
            dry_run=dry_run,
            success=True
        )
        
        logger.info(f"Refactoring {'preview' if dry_run else 'complete'}: "
                   f"{files_changed} files, {total_replacements} replacements")
        
        return result
    
    def suggest_refactorings(
        self,
        file_path: str,
        max_suggestions: int = 5
    ) -> List[RefactorSuggestion]:
        """
        Analyze code and suggest refactorings.
        
        Args:
            file_path: Path to file to analyze
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List of refactoring suggestions
        """
        suggestions = []
        
        full_path = self.workspace_root / file_path
        
        if not full_path.exists():
            logger.error(f"File not found: {file_path}")
            return suggestions
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Analyze for common issues
            for node in ast.walk(tree):
                # Long functions
                if isinstance(node, ast.FunctionDef):
                    func_lines = node.end_lineno - node.lineno + 1
                    if func_lines > 50:
                        suggestions.append(RefactorSuggestion(
                            type='extract_function',
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.end_lineno,
                            description=f"Function '{node.name}' is {func_lines} lines long",
                            rationale="Consider breaking it into smaller functions for better readability",
                            estimated_impact='medium'
                        ))
                
                # Complex conditionals
                if isinstance(node, ast.If):
                    if self._is_complex_conditional(node.test):
                        suggestions.append(RefactorSuggestion(
                            type='simplify_conditional',
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.lineno,
                            description="Complex conditional expression",
                            rationale="Consider extracting to a named variable for clarity",
                            estimated_impact='low'
                        ))
            
            # Limit suggestions
            suggestions = suggestions[:max_suggestions]
        
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
        
        return suggestions
    
    def _find_files(self, pattern: str) -> List[Path]:
        """Find files matching glob pattern, excluding ignored paths."""
        files = []
        
        for file_path in self.workspace_root.glob(pattern):
            if file_path.is_file() and not self._should_ignore(file_path):
                files.append(file_path)
        
        return files
    
    def _should_ignore(self, file_path: Path) -> bool:
        """Check if file should be ignored."""
        relative_path = file_path.relative_to(self.workspace_root)
        
        for pattern in self.ignore_patterns:
            if relative_path.match(pattern):
                return True
        
        return False
    
    def _generate_diff_preview(self, original: str, new: str, max_lines: int = 10) -> str:
        """Generate a preview of changes."""
        orig_lines = original.split('\n')
        new_lines = new.split('\n')
        
        # Simple diff - show first few changed lines
        diff_lines = []
        for i, (orig, new) in enumerate(zip(orig_lines, new_lines)):
            if orig != new:
                diff_lines.append(f"Line {i+1}:")
                diff_lines.append(f"- {orig}")
                diff_lines.append(f"+ {new}")
                
                if len(diff_lines) >= max_lines * 3:
                    break
        
        return '\n'.join(diff_lines)
    
    def _is_complex_conditional(self, node: ast.expr) -> bool:
        """Check if conditional is complex."""
        # Count boolean operators
        bool_ops = sum(1 for _ in ast.walk(node) if isinstance(_, (ast.And, ast.Or)))
        return bool_ops > 2


# Example usage
if __name__ == "__main__":
    # Create server
    server = RefactorMCPServer(os.environ.get("WORKSPACE_ROOT", "."))
    
    # Test code search
    results = server.code_search("def.*index", file_pattern="**/*.py")
    print(f"\nFound {len(results)} matches")
    for r in results[:3]:
        print(f"  {r.file_path}:{r.line_number} - {r.line_content[:60]}")
    
    # Test refactor (dry run)
    refactor_result = server.code_refactor(
        search_pattern=r"print\((.*)\)",
        replace_pattern=r"logger.info(\1)",
        file_pattern="**/*.py",
        dry_run=True
    )
    print(f"\nRefactor preview: {refactor_result.files_changed} files, {refactor_result.total_replacements} replacements")
