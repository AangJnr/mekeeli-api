
from mcp import Mcp
from mcp.tools.gmail import GmailTool
from mcp.tools.search import SearchTool
from mcp.tools.tika import TikaTool
from mcp.llms.ollama import OllamaLlm

def get_mcp():
    mcp = Mcp()
    mcp.add_tool(GmailTool())
    mcp.add_tool(SearchTool())
    mcp.add_tool(TikaTool())
    mcp.set_llm(OllamaLlm(model="gemma2"))
    return mcp
