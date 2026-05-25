import os
import json
import urllib.request
import urllib.parse
from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP server
mcp = FastMCP("Mempalace Search")

API_BASE_URL = os.environ.get("MEMPALACE_API_URL", "http://127.0.0.1:8000").rstrip("/")
API_URL = f"{API_BASE_URL}/mempalace_search"
# The API Key the MCP uses to fetch data from the SaaS
API_TOKEN = os.environ.get("MEMPALACE_API_KEY", "test-token-123")

@mcp.tool()
def search_mempalace_history(query: str) -> str:
    """
    Search the user's historical terminal sessions in the Mempalace Cloud.
    Use this tool to find past commands, tasks, IP addresses, or bug fixes the user has done previously.
    """
    # Construct the query URL
    params = urllib.parse.urlencode({"query": query})
    url = f"{API_URL}?{params}"
    
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {API_TOKEN}"
    })
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                results = data.get("results", [])
                if not results:
                    return f"No historical terminal sessions found matching: '{query}'"
                
                output = f"Found {len(results)} past sessions matching '{query}':\n\n"
                for i, res in enumerate(results, 1):
                    output += f"--- Result {i} ---\n{res}\n\n"
                return output
            else:
                return f"Error connecting to Mempalace Cloud SaaS. Status: {response.status}"
    except Exception as e:
        return f"Failed to reach Mempalace Cloud SaaS: {e}"

if __name__ == "__main__":
    print("🚀 Starting Mempalace MCP Server...")
    print("To install in Claude Desktop, add the following to your claude_desktop_config.json:")
    print('{"mcpServers": {"mempalace": {"command": "python3", "args": ["/absolute/path/to/mempalace_mcp.py"]}}}')
    mcp.run()
