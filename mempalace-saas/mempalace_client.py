import asyncio
import sys
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession
import mcp.types as types

# We will use the valid test token for user_pratham
API_KEY = "test-token-123"
SERVER_URL = "http://127.0.0.1:8000/sse"

async def main():
    if len(sys.argv) < 2:
        print("Usage: python mempalace_client.py <text_to_save>")
        sys.exit(1)
        
    text_to_save = sys.argv[1]
    
    # We pass the Authorization header via SSE connection parameters
    # The mcp sdk sse_client can take standard HTTP headers or we can use a custom httpx client.
    # Currently mcp uses starlette/httpx under the hood. For simplicity in the MVP, 
    # we can pass headers if supported, or we just rely on standard transport.
    import httpx
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    print("🔌 Connecting to Cloud Mempalace...")
    
    # We use a custom SSE client with the headers injected
    try:
        async with sse_client(url=SERVER_URL, headers=headers) as (read_stream, write_stream):
            print("✅ Connected securely.")
            
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                
                print("🧠 Calling mempalace_add tool...")
                # Call the MCP tool
                result = await session.call_tool("mempalace_add", arguments={"content": text_to_save})
                
                print("\n☁️  Cloud Response:")
                for content in result.content:
                    if isinstance(content, types.TextContent):
                        print(content.text)
                        
    except httpx.HTTPStatusError as e:
        print(f"❌ Authentication Failed: {e.response.status_code}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
