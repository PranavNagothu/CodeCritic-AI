import logging
import os
from typing import Any, Dict, List, Optional, Set
from anytree import Node, RenderTree
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import PrivateAttr
import Levenshtein

logger = logging.getLogger(__name__)

class LLMRetriever(BaseRetriever):
    """
    Retriever that uses an LLM to select relevant files from the project structure.
    Uses LangChain models to identify relevant files from the repo structure.
    """
    
    llm: BaseChatModel
    repo_files: List[str]
    top_k: int = 5
    repo_structure: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Use object.__setattr__ to avoid pydantic validation errors if frozen
        # But since we made it a field, we can just set it OR pass it in kwargs if calculated before.
        # Better: calculate it here and set it.
        structure = self._build_repo_structure(self.repo_files)
        self.repo_structure = structure
        
    def _build_repo_structure(self, files: List[str]) -> str:
        """Builds a visual tree structure of the repository."""
        # Build tree
        root = Node("root")
        nodes = {"": root}
        
        for file_path in files:
            parts = file_path.strip("/").split("/")
            current_path = ""
            parent = root
            
            for part in parts:
                current_path = f"{current_path}/{part}" if current_path else part
                if current_path not in nodes:
                    nodes[current_path] = Node(part, parent=parent)
                parent = nodes[current_path]
        
        # Render tree
        render = ""
        for pre, _, node in RenderTree(root):
            if node.name == "root": continue
            # Simplify characters for token efficiency
            line = f"{pre}{node.name}"
            line = line.replace("└", " ").replace("├", " ").replace("│", " ").replace("─", " ")
            render += line + "\n"
            
        return render

    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun) -> List[Document]:
        """Retrieve relevant documents for a given query."""
        try:
            logger.info("LLMRetriever: Asking LLM to select files...")
            filenames = self._ask_llm_to_retrieve(query)
            logger.info(f"LLMRetriever: Selected {len(filenames)} files: {filenames}")
            
            documents = []
            for filename in filenames:
                # We expect the caller to handle reading the actual content if needed, 
                # or we return a Document with just metadata if we don't have access to the file system here.
                # Ideally, we should have access to read the file. 
                # Let's assume we can read if it is a local path (which it should be in this app).
                
                # Check if we can find the absolute path? 
                # The repo_files passed in might be relative paths or absolute.
                # We will assume they are paths we can open.
                
                try:
                    # If repo_files are absolute, great. If relative, we might need a base_dir.
                    # For now, let's assume the passed repo_files are valid paths to read.
                    if os.path.exists(filename):
                         with open(filename, "r", errors='ignore') as f:
                            content = f.read()
                            documents.append(Document(
                                page_content=content,
                                metadata={"file_path": filename, "source": "llm_retriever"}
                            ))
                    else:
                        documents.append(Document(
                            page_content="",
                            metadata={"file_path": filename, "source": "llm_retriever", "error": "File not found"}
                        ))
                except Exception as e:
                    logger.warning(f"Failed to read file {filename}: {e}")
                    
            return documents
        except Exception as e:
            logger.error(f"LLMRetriever failed: {e}")
            return []

    def _ask_llm_to_retrieve(self, user_query: str) -> List[str]:
        """Feeds the file hierarchy and user query to the LLM."""
        
        system_prompt = f"""
You are a senior software engineer helping to navigate a codebase.
Your task is to identify the top {self.top_k} files in the repository that are most likely to contain the answer to the user's query.

Here is the file structure of the repository:
{self.repo_structure}

Rules:
1. Respond ONLY with a list of file paths, one per line.
2. Do not include any explanation or conversational text.
3. Select files that are relevant to: "{user_query}"
4. If the file paths in the structure are relative, return them as they appear in the structure.
"""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User Query: {user_query}")
        ]
        
        response = self.llm.invoke(messages)
        text = response.content.strip()
        logger.info(f"DEBUG: Raw LLM Response: {text}")
        
        # Parse response
        lines = text.split('\n')
        selected_files = []
        for line in lines:
            cleaned = line.strip().strip("- ").strip("* ")
            if cleaned:
                # Validate if it exists in our known files (fuzzy match if needed)
                match = self._find_best_match(cleaned)
                if match:
                    selected_files.append(match)
        
        return list(set(selected_files))[:self.top_k]

    def _find_best_match(self, filename: str) -> Optional[str]:
        """Finds the closest matching filename from the repo."""
        if filename in self.repo_files:
            return filename
            
        # 1. Try exact match on basename
        for f in self.repo_files:
            if os.path.basename(f) == filename:
                return f
        
        # 2. Fuzzy match
        best_match = None
        min_dist = float('inf')
        
        for f in self.repo_files:
            # We compare with the full path or just the end?
            # Let's compare with the full path since LLM sees the structure.
            dist = Levenshtein.distance(filename, f)
            if dist < min_dist:
                min_dist = dist
                best_match = f
                
        if min_dist < 20: # Arbitrary threshold
            return best_match
            
        return None
