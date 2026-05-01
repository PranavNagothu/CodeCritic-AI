
from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from code_chatbot.core.rate_limiter import get_rate_limiter

# Define State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

def create_agent_graph(llm, retriever, repo_name: str = "Codebase", repo_dir: str = ".", provider: str = "gemini", code_analyzer=None):
    """
    Creates a LangGraph for CodeCritic AI.
    Enables: Search -> Read File -> Reason -> Search -> Answer.
    Uses adaptive rate limiting to maximize usage within free tier.
    """
    
    from pydantic import BaseModel, Field

    class SearchInput(BaseModel):
        query: str = Field(description="The query string to search for in the codebase.")

    # 1. Wrap Retriever as a Tool
    @tool("search_codebase", args_schema=SearchInput)
    def search_codebase(query: str):
        """
        Search the codebase for code snippets relevant to the query. 
        Returns top 5 most relevant code sections with file paths.
        Use this when you need to find specific functions, classes, or implementations.
        You can call this multiple times with different queries to gather comprehensive information.
        """
        docs = retriever.invoke(query)
        result = ""
        # Increased to 5 results * 2000 chars = ~10000 chars (~2500 tokens) - much better context
        for i, doc in enumerate(docs[:5]):
            fp = doc.metadata.get('file_path', 'unknown')
            # Get relative path for cleaner display
            import os
            display_path = os.path.basename(fp) if fp != 'unknown' else 'unknown'
            content = doc.page_content[:2000]  # Increased from 1000 to 2000
            result += f"--- Result {i+1}: {display_path} ---\n{content}\n\n"
        
        if not result:
            return "No relevant code found. Try a different search query or use list_files to explore the codebase structure."
        
        return result

    # 2. Import File System Tools
    from code_chatbot.agents.tools import get_filesystem_tools, get_call_graph_tools
    
    # 3. Combine Tools
    fs_tools = get_filesystem_tools(repo_dir)
    call_graph_tools = get_call_graph_tools(code_analyzer) if code_analyzer else []
    tools = fs_tools + [search_codebase] + call_graph_tools
    
    # 4. Bind to LLM
    # Note: Not all LLMs support bind_tools cleanly, but Gemini/Groq(Llama3) do via LangChain
    model_with_tools = llm.bind_tools(tools)
    
    # 5. Define Nodes
    # Get rate limiter for this provider
    rate_limiter = get_rate_limiter(provider)
    
    def agent(state):
        messages = state["messages"]
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Smart adaptive delay - only waits when approaching rate limit
        rate_limiter.wait_if_needed()

        # Retry loop for 429 errors
        # FAIL FAST: Only retry twice (5s, 10s) = 15s max delay.
        # If it still fails, we want to bubble up to rag.py to trigger Linear RAG fallback.
        for i in range(2):
            try:
                response = model_with_tools.invoke(messages)
                # Track usage for statistics (if available in response metadata)
                try:
                    usage = getattr(response, 'usage_metadata', None)
                    if usage:
                        rate_limiter.record_usage(
                            input_tokens=getattr(usage, 'input_tokens', 0),
                            output_tokens=getattr(usage, 'output_tokens', 0)
                        )
                except:
                    pass
                
                return {"messages": [response]}
            except Exception as e:
                # Catch both Gemini 429 and Groq Overloaded errors
                if any(err in str(e) for err in ["429", "RESOURCE_EXHAUSTED", "rate_limit_exceeded"]):
                    import time
                    wait = 5 * (2 ** i) # 5, 10
                    logger.warning(f"⚠️ Rate limit hit. Cooling down for {wait}s...")
                    time.sleep(wait)
                    if i == 1: raise e
                else:
                    raise e
        return {"messages": []} # Should not reach here

    tool_node = ToolNode(tools)
    
    # 6. Define Limits (Graph recursion limit is set in .compile(), but we can add logic here)
    
    # 7. Build Graph
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent)
    workflow.add_node("tools", tool_node)
    
    workflow.set_entry_point("agent")
    
    # Conditional Edge
    def should_continue(state):
        last_message = state["messages"][-1]
        
        # If there is no tool call, then we finish
        if not last_message.tool_calls:
            return END
        
        # Otherwise context switch to tools
        return "tools"

    workflow.add_conditional_edges(
        "agent",
        should_continue,
    )
    
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()
