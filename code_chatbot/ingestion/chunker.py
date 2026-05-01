"""Enhanced chunker with proper token counting and AST-based structural merging strategies."""

import logging
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from functools import cached_property

import pygments
import tiktoken
from langchain_core.documents import Document
from tree_sitter import Language, Parser, Node
import tree_sitter_python
import tree_sitter_javascript

logger = logging.getLogger(__name__)
tokenizer = tiktoken.get_encoding("cl100k_base")


@dataclass
class FileChunk:
    """Represents a chunk of code with byte positions and rich metadata."""
    file_content: str
    file_metadata: Dict
    start_byte: int
    end_byte: int
    
    # Enhanced metadata fields
    symbols_defined: Optional[List[str]] = None  # Functions/classes defined in this chunk
    imports_used: Optional[List[str]] = None     # Import statements relevant to chunk
    complexity_score: Optional[int] = None       # Cyclomatic complexity
    parent_context: Optional[str] = None         # Parent class/module name
    
    @cached_property
    def filename(self):
        if "file_path" not in self.file_metadata:
            raise ValueError("file_metadata must contain a 'file_path' key.")
        return self.file_metadata["file_path"]
    
    @cached_property
    def content(self) -> str:
        """The text content to be embedded. Includes filename for context."""
        return self.filename + "\n\n" + self.file_content[self.start_byte : self.end_byte]
    
    @cached_property
    def num_tokens(self):
        """Number of tokens in this chunk."""
        return len(tokenizer.encode(self.content, disallowed_special=()))
    
    def to_document(self) -> Document:
        """Convert to LangChain Document with enhanced metadata."""
        chunk_type = self.file_metadata.get("chunk_type", "code")
        name = self.file_metadata.get("name", None)
        
        # Calculate line range from byte positions
        lines_before = self.file_content[:self.start_byte].count('\n')
        lines_in_chunk = self.file_content[self.start_byte:self.end_byte].count('\n')
        line_range = f"L{lines_before + 1}-L{lines_before + lines_in_chunk + 1}"
        
        # Get language from file extension
        ext = self.filename.split('.')[-1].lower() if '.' in self.filename else 'unknown'
        language_map = {
            'py': 'python', 'js': 'javascript', 'ts': 'typescript',
            'jsx': 'javascript', 'tsx': 'typescript', 'java': 'java',
            'cpp': 'cpp', 'c': 'c', 'go': 'go', 'rs': 'rust'
        }
        language = language_map.get(ext, ext)
        
        metadata = {
            **self.file_metadata,
            "id": f"{self.filename}_{self.start_byte}_{self.end_byte}",
            "start_byte": self.start_byte,
            "end_byte": self.end_byte,
            "length": self.end_byte - self.start_byte,
            "line_range": line_range,
            "language": language,
            "chunk_type": chunk_type,
            "name": name,
        }
        
        # Add enhanced metadata if available
        if self.symbols_defined:
            metadata["symbols"] = self.symbols_defined
        if self.imports_used:
            metadata["imports"] = self.imports_used
        if self.complexity_score is not None:
            metadata["complexity"] = self.complexity_score
        if self.parent_context:
            metadata["parent_context"] = self.parent_context
        
        return Document(page_content=self.content, metadata=metadata)


class StructuralChunker:
    """
    Chunks code files based on their AST structure (Functions, Classes) using Tree-sitter.
    Uses proper token counting with tiktoken and implements merging strategies to avoid 
    pathologically small chunks.
    """
    def __init__(self, max_tokens: int = 800):
        self.max_tokens = max_tokens
        self.parsers = {}
        self._init_parsers()
        
    def _init_parsers(self):
        try:
            self.parsers['py'] = Parser(Language(tree_sitter_python.language()))
            self.parsers['python'] = self.parsers['py']
            js_parser = Parser(Language(tree_sitter_javascript.language()))
            self.parsers['js'] = js_parser
            self.parsers['javascript'] = js_parser
            self.parsers['jsx'] = js_parser
            self.parsers['ts'] = js_parser
            self.parsers['tsx'] = js_parser
        except Exception as e:
            logger.error(f"Error initializing parsers in Chunker: {e}")

    @staticmethod
    def _get_language_from_filename(filename: str) -> Optional[str]:
        """Returns a canonical name for the language based on file extension."""
        extension = os.path.splitext(filename)[1]
        if extension == ".tsx":
            return "tsx"
        
        try:
            lexer = pygments.lexers.get_lexer_for_filename(filename)
            return lexer.name.lower()
        except pygments.util.ClassNotFound:
            return None
    
    @staticmethod
    def is_code_file(filename: str) -> bool:
        """Checks whether the file can be parsed as code."""
        language = StructuralChunker._get_language_from_filename(filename)
        return language and language not in ["text only", "none"]

    def chunk(self, content: str, file_path: str) -> List[Document]:
        """Main chunking entry point."""
        ext = file_path.split('.')[-1].lower()
        parser = self.parsers.get(ext)
        
        if "\0" in content:
             logger.warning(f"Binary content detected in {file_path}, skipping chunking")
             return []

        if not parser:
            logger.warning(f"No parser found for extension: {ext}, treating as text file")
            # Fallback to simple text chunking for non-code files
            return self._chunk_text_file(content, file_path)

        try:
            tree = parser.parse(bytes(content, "utf8"))
            
            if not tree.root_node.children or tree.root_node.children[0].type == "ERROR":
                logger.warning(f"Failed to parse code in {file_path}, falling back to text chunking")
                return self._chunk_text_file(content, file_path)
            
            file_metadata = {"file_path": file_path, "chunk_type": "code", "_full_content": content}
            file_chunks = self._chunk_node(tree.root_node, content, file_metadata)
            
            # Convert FileChunk objects to Documents
            return [chunk.to_document() for chunk in file_chunks]
            
        except Exception as e:
            logger.error(f"Failed to chunk {file_path}: {e}, falling back to text chunking")
            return self._chunk_text_file(content, file_path)

    def _chunk_text_file(self, content: str, file_path: str) -> List[Document]:
        """Fallback chunking for text files."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.max_tokens * 4,  # Approximate char count
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        texts = splitter.split_text(content)
        return [
            Document(
                page_content=f"{file_path}\n\n{text}",
                metadata={"file_path": file_path, "chunk_type": "text"}
            )
            for text in texts
        ]

    def _chunk_node(self, node: Node, file_content: str, file_metadata: Dict) -> List[FileChunk]:
        """
        Recursively splits a node into chunks. 
        If a node is small enough, returns it as a single chunk.
        If too large, recursively chunks its children and merges neighboring chunks when possible.
        """
        node_chunk = FileChunk(file_content, file_metadata, node.start_byte, node.end_byte)
        
        # If chunk is small enough and not a module/program node, return it
        if node_chunk.num_tokens <= self.max_tokens and node.type not in ["module", "program"]:
            # Add metadata about the node type and name
            chunk_metadata = {**file_metadata}
            chunk_metadata["chunk_type"] = node.type
            name = self._get_node_name(node, file_content)
            if name:
                chunk_metadata["name"] = name
            
            # Extract enhanced metadata
            node_chunk.file_metadata = chunk_metadata
            node_chunk.symbols_defined = self._extract_symbols(node, file_content)
            node_chunk.imports_used = self._extract_imports(node, file_content)
            node_chunk.complexity_score = self._calculate_complexity(node, file_content)
            node_chunk.parent_context = self._get_parent_context(node, file_content)
            
            return [node_chunk]
        
        # If leaf node is too large, split it as text
        if not node.children:
            return self._chunk_large_text(
                file_content[node.start_byte : node.end_byte], 
                node.start_byte, 
                file_metadata
            )
        
        # Recursively chunk children
        chunks = []
        for child in node.children:
            chunks.extend(self._chunk_node(child, file_content, file_metadata))
        
        # Merge neighboring chunks if their combined size doesn't exceed max_tokens
        merged_chunks = []
        for chunk in chunks:
            if not merged_chunks:
                merged_chunks.append(chunk)
            elif merged_chunks[-1].num_tokens + chunk.num_tokens < self.max_tokens - 50:
                # Try merging
                merged = FileChunk(
                    file_content,
                    file_metadata,
                    merged_chunks[-1].start_byte,
                    chunk.end_byte,
                )
                if merged.num_tokens <= self.max_tokens:
                    merged_chunks[-1] = merged
                else:
                    merged_chunks.append(chunk)
            else:
                merged_chunks.append(chunk)
        
        # Verify all chunks are within token limit
        for chunk in merged_chunks:
            if chunk.num_tokens > self.max_tokens:
                logger.warning(
                    f"Chunk size {chunk.num_tokens} exceeds max_tokens {self.max_tokens} "
                    f"for {chunk.filename} at bytes {chunk.start_byte}-{chunk.end_byte}"
                )
        
        return merged_chunks
    
    def _chunk_large_text(self, text: str, start_offset: int, file_metadata: Dict) -> List[FileChunk]:
        """Splits large text (e.g., long comments or strings) into smaller chunks."""
        # Need full file content for FileChunk to work properly
        file_content = file_metadata.get("_full_content", "")
        if not file_content:
            logger.warning("Cannot chunk large text without full file content")
            return []
            
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.max_tokens * 4,
            chunk_overlap=200
        )
        texts = splitter.split_text(text)
        
        chunks = []
        current_offset = start_offset
        for text_chunk in texts:
            end_offset = current_offset + len(text_chunk)
            chunk = FileChunk(
                file_content,
                {**file_metadata, "chunk_type": "large_text"},
                current_offset,
                end_offset
            )
            chunks.append(chunk)
            current_offset = end_offset
        
        return chunks

    def _get_node_name(self, node: Node, content: str) -> Optional[str]:
        """Extracts the name of a function or class node."""
        name_node = node.child_by_field_name("name")
        if name_node:
            return content[name_node.start_byte:name_node.end_byte]
        return None
    
    def _extract_symbols(self, node: Node, content: str) -> List[str]:
        """
        Extract function and class names defined in this node.
        
        Returns:
            List of symbol names (e.g., ['MyClass', 'MyClass.my_method'])
        """
        symbols = []
        
        def traverse(n: Node, parent_class: Optional[str] = None):
            # Check if this is a function or class definition
            if n.type in ['function_definition', 'class_definition', 'method_definition']:
                name = self._get_node_name(n, content)
                if name:
                    if parent_class:
                        symbols.append(f"{parent_class}.{name}")
                    else:
                        symbols.append(name)
                    
                    # If it's a class, traverse its children with this class as parent
                    if n.type == 'class_definition':
                        for child in n.children:
                            traverse(child, name)
                        return  # Don't traverse children again
            
            # Traverse children
            for child in n.children:
                traverse(child, parent_class)
        
        traverse(node)
        return symbols
    
    def _extract_imports(self, node: Node, content: str) -> List[str]:
        """
        Extract import statements from this node.
        
        Returns:
            List of import statements (e.g., ['import os', 'from typing import List'])
        """
        imports = []
        
        def traverse(n: Node):
            # Python imports
            if n.type in ['import_statement', 'import_from_statement']:
                import_text = content[n.start_byte:n.end_byte].strip()
                imports.append(import_text)
            
            # JavaScript/TypeScript imports
            elif n.type == 'import_statement':
                import_text = content[n.start_byte:n.end_byte].strip()
                imports.append(import_text)
            
            # Traverse children
            for child in n.children:
                traverse(child)
        
        traverse(node)
        return imports
    
    def _calculate_complexity(self, node: Node, content: str) -> int:
        """
        Calculate cyclomatic complexity for a code chunk.
        
        Cyclomatic complexity = number of decision points + 1
        Decision points: if, elif, for, while, except, and, or, case, etc.
        
        Returns:
            Complexity score (integer)
        """
        complexity = 1  # Base complexity
        
        # Decision point node types
        decision_nodes = {
            'if_statement', 'elif_clause', 'else_clause',
            'for_statement', 'while_statement',
            'except_clause', 'case_clause',
            'conditional_expression',  # ternary operator
            'boolean_operator',  # and, or
        }
        
        def traverse(n: Node):
            nonlocal complexity
            
            if n.type in decision_nodes:
                complexity += 1
            
            for child in n.children:
                traverse(child)
        
        traverse(node)
        return complexity
    
    def _get_parent_context(self, node: Node, content: str) -> Optional[str]:
        """
        Get the parent class or module context for this node.
        
        Returns:
            Parent class name or None
        """
        current = node.parent
        
        while current:
            if current.type == 'class_definition':
                name = self._get_node_name(current, content)
                if name:
                    return name
            current = current.parent
        
        return None

