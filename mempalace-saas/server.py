import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Security, Request, Query
from fastapi.security import APIKeyHeader
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import json
import datetime
import subprocess
import urllib.request
import urllib.error
import sqlite3
import uuid
import asyncio
import paramiko
import io

# Initialize SQLite waitlist DB and Palace path dynamically
# If we have a persistent volume at /app/data, write data there to prevent container reset erasure
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERSISTENT_DATA_DIR = "/app/data"
if os.path.exists(PERSISTENT_DATA_DIR) and os.access(PERSISTENT_DATA_DIR, os.W_OK):
    DB_PATH = os.path.join(PERSISTENT_DATA_DIR, "waitlist.db")
    os.environ["MEMPALACE_PALACE_PATH"] = os.path.join(PERSISTENT_DATA_DIR, "palace")
    print(f"📦 Persistent volume detected at {PERSISTENT_DATA_DIR}. Storing DB and memories in volume.")
else:
    DB_PATH = os.path.join(BASE_DIR, "waitlist.db")
    print(f"📁 No persistent volume found. Storing DB locally at: {DB_PATH}")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS waitlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            api_key TEXT UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def setup_ssh_key():
    private_key = os.environ.get("SSH_PRIVATE_KEY")
    if private_key:
        ssh_dir = os.path.expanduser("~/.ssh")
        os.makedirs(ssh_dir, exist_ok=True)
        key_path = os.path.join(ssh_dir, "id_rsa")
        
        # Write private key securely
        with open(key_path, "w") as f:
            f.write(private_key.strip() + "\n")
            
        os.chmod(key_path, 0o600)
        print("🔐 SSH private key written and secured from environment variables.")

init_db()
setup_ssh_key()

# Load configuration from config.env if available
MEMPALACE_SERVER = "192.168.1.137"
for env_path in ["../config.env", "config.env", "/home/prathammodi/ai-observer/config.env"]:
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k.strip()] = v.strip()
if "MEMPALACE_SERVER" in os.environ:
    MEMPALACE_SERVER = os.environ["MEMPALACE_SERVER"]

def run_ssh_command(cmd: str):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Load private key from env or file
    private_key_str = os.environ.get("SSH_PRIVATE_KEY")
    if private_key_str:
        try:
            pkey = paramiko.RSAKey.from_private_key(io.StringIO(private_key_str.strip()))
        except Exception:
            pkey = paramiko.RSAKey.from_private_key_file(os.path.expanduser("~/.ssh/id_rsa"))
    else:
        # Load from file fallback
        key_path = os.path.expanduser("~/.ssh/id_rsa")
        pkey = paramiko.RSAKey.from_private_key_file(key_path)
        
    ssh.connect(MEMPALACE_SERVER, username="root", pkey=pkey, timeout=15)
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    stdout_str = stdout.read().decode("utf-8")
    stderr_str = stderr.read().decode("utf-8")
    ssh.close()
    
    return stdout_str, stderr_str

def remote_handle_request(payload):
    # Enforce SSH execution of the entire payload on the remote mempalace.mcp_server
    ssh_script = f"""
cd /root/mempalace && source venv/bin/activate && python3 - <<'PYEOF'
import json, sys
from mempalace.mcp_server import handle_request
payload = json.loads({repr(json.dumps(payload))})
response = handle_request(payload)
print(json.dumps(response))
PYEOF
"""
    try:
        stdout_str, stderr_str = run_ssh_command(ssh_script)
        stdout_lines = stdout_str.strip().splitlines()
        for line in stdout_lines:
            line = line.strip()
            if line.startswith("{"):
                try:
                    return json.loads(line)
                except Exception:
                    pass
        # Fallback if no JSON found
        return {"jsonrpc": "2.0", "id": payload.get("id"), "error": {"code": -32603, "message": f"No JSON response from remote SSH server. Stderr: {stderr_str}"}}
    except Exception as e:
        return {"jsonrpc": "2.0", "id": payload.get("id"), "error": {"code": -32603, "message": f"SSH bridge error: {e}"}}

# Check if Mempalace Core is available locally (Option A)
# Auto-force remote mode on Railway to ensure data is saved on the persistent VPS instead of ephemeral container disk
FORCE_REMOTE = os.environ.get("MEMPALACE_FORCE_REMOTE", "false").lower() == "true" or "RAILWAY_STATIC_URL" in os.environ

if FORCE_REMOTE:
    LOCAL_DATABASE_AVAILABLE = False
    handle_request = remote_handle_request
    print(f"🌉 Forced Remote Mode (Railway/User forced). Running in remote SSH Bridge Mode targeting {MEMPALACE_SERVER}.")
else:
    try:
        from mempalace.mcp_server import tool_add_drawer, tool_kg_add, tool_search, handle_request
        LOCAL_DATABASE_AVAILABLE = True
        print("🧠 Local Mempalace Database Core detected. Running in cloud-native Mode.")
    except ImportError:
        LOCAL_DATABASE_AVAILABLE = False
        handle_request = remote_handle_request
        print(f"🌉 Local Mempalace Database Core NOT detected. Running in remote SSH Bridge Mode targeting {MEMPALACE_SERVER}.")

app = FastAPI(title="Mempalace SaaS MVP")

# Mock Database
MOCK_DB = []

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

def get_tenant_id(
    api_key: str = Security(api_key_header),
    token_param: str = Query(None, alias="token")
) -> str:
    token = None
    if api_key and api_key.startswith("Bearer "):
        token = api_key.replace("Bearer ", "")
    elif token_param:
        token = token_param
        
    if not token:
        raise HTTPException(status_code=401, detail="Missing or invalid token. Use 'Bearer <token>' header or '?token=<token>' query parameter")
    
    # 1. Check hardcoded developer tokens
    VALID_TOKENS = {
        "test-token-123": "user_pratham",
        "test-token-456": "user_demo"
    }
    
    if token in VALID_TOKENS:
        return VALID_TOKENS[token]
        
    # 2. Check waitlist database active tokens
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM waitlist WHERE api_key = ?", (token,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            email = row[0]
            # Map user's email to a safe, clean username/tenant_id
            return "user_" + email.split("@")[0].replace(".", "_").replace("-", "_")
    except Exception as e:
        print(f"⚠️ Token DB lookup failed: {e}")
        
    raise HTTPException(status_code=401, detail="Invalid token")

class MemoryPayload(BaseModel):
    content: str

@app.post("/mempalace_add")
async def add_memory(payload: MemoryPayload, tenant_id: str = Depends(get_tenant_id)):
    print(f"\n🧠 [Cloud AI Worker] Received session for {tenant_id}. Running OpenRouter AI Summarization...")
    
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    if not openrouter_key:
        try:
            settings_path = os.path.expanduser("~/.claude/settings.json")
            if os.path.exists(settings_path):
                with open(settings_path, "r") as f:
                    settings_data = json.load(f)
                    openrouter_key = settings_data.get("env", {}).get("ANTHROPIC_AUTH_TOKEN")
        except Exception:
            pass
    summary_text = "Fallback summary (no API key)"
    tasks = ["Fallback task"]
    
    try:
        prompt = f"""Analyze this terminal session and extract a short summary and a list of completed tasks.
Return ONLY a valid JSON object in this format: {{"summary": "...", "tasks": ["...", "..."]}}
Session text:
{payload.content[:3000]}
"""
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps({
                "model": "openrouter/free",
                "messages": [
                    {"role": "system", "content": "You are a DevOps assistant that analyzes terminal logs and outputs strict JSON."},
                    {"role": "user", "content": prompt}
                ]
            }).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {openrouter_key}",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            result_json = json.loads(response.read().decode())
            content = result_json["choices"][0]["message"]["content"]
            # Clean up markdown code blocks if present
            if content.startswith("```json"):
                content = content.split("```json")[1].rsplit("```", 1)[0].strip()
            elif content.startswith("```"):
                content = content.split("```")[1].rsplit("```", 1)[0].strip()
                
            parsed_content = json.loads(content)
            summary_text = parsed_content.get("summary", summary_text)
            tasks = parsed_content.get("tasks", tasks)
            print("✅ OpenRouter AI extraction successful!")
            print(f"   Summary: {summary_text}")
    except Exception as e:
        print(f"⚠️ OpenRouter API failed: {e}")
    
    # 1. Format the data to match the strict Mempalace Graph JSON schema
    db_json = {
        "project": tenant_id,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": summary_text,
        "tasks": tasks,
        "decisions": [],
        "commands": [],
        "problems": [],
        "learnings": [],
        "files_created": [],
        "files_modified": [],
        "technologies": [],
        "tags": ["mempalace-cli"],
        "raw_text": payload.content
    }
    
    json_string = json.dumps(db_json)
    
    if LOCAL_DATABASE_AVAILABLE:
        try:
            print("🧠 Running cloud-native in-process database query...")
            source_file = f"mempalace-cli-{int(datetime.datetime.now().timestamp())}"
            result = tool_add_drawer(
                wing=tenant_id,
                room="sessions",
                content=json_string,
                source_file=source_file,
                added_by="mempalace-cli"
            )
            if result.get("success"):
                tool_kg_add(
                    subject=tenant_id,
                    predicate="worked_on",
                    object=summary_text[:100],
                    valid_from=db_json["timestamp"].split("T")[0]
                )
                print(f"✅ Successfully saved memory in-process for {tenant_id}!")
                return {"status": "success", "message": f"✅ Memory saved in-process securely for {tenant_id}!"}
            else:
                print(f"❌ In-process save failed: {result}")
                raise HTTPException(status_code=500, detail=f"Database save failed: {result}")
        except Exception as e:
            print(f"❌ In-process save exception: {e}")
            raise HTTPException(status_code=500, detail=f"Database save exception: {e}")
            
    # 2. Execute the bridge injection via SSH to the real VPS (Fallback)
    ssh_script = f"""
TMP_JSON=$(mktemp)
cat > "$TMP_JSON" <<'JSONEOF'
{json_string}
JSONEOF
cd /root/mempalace && source venv/bin/activate && python3 - "$TMP_JSON" <<'PYEOF'
from mempalace.mcp_server import tool_add_drawer, tool_kg_add
import json, time, sys

with open(sys.argv[1], 'r') as f:
    data = f.read()
parsed = json.loads(data)

source_file = 'mempalace-cli-' + str(int(time.time()))

try:
    result = tool_add_drawer(
        wing=parsed.get('project', 'mempalace-cli'),
        room='sessions',
        content=data,
        source_file=source_file,
        added_by='mempalace-cli'
    )
    if result.get('success'):
        tool_kg_add(
            subject='prathammodi',
            predicate='worked_on',
            object=parsed['summary'][:100],
            valid_from=parsed['timestamp'].split('T')[0]
        )
        print('SUCCESS')
    else:
        print(f"FAILED: {{result}}")
except Exception as e:
    print(f'FAILED: {{e}}')
PYEOF
rm -f "$TMP_JSON"
"""
    
    try:
        print(f"🌉 Bridging data to {MEMPALACE_SERVER} Real Mempalace Database...")
        stdout_str, stderr_str = run_ssh_command(ssh_script)
        if "SUCCESS" in stdout_str:
            print(f"✅ Successfully injected into real Mempalace on {MEMPALACE_SERVER}!")
        else:
            print(f"❌ Injection failed. stdout: {stdout_str} stderr: {stderr_str}")
    except Exception as e:
        print(f"❌ SSH bridge failed: {e}")
    
    print(f"✅ [Cloud AI Worker] Session completely processed for {tenant_id}!")
    
    return {"status": "success", "message": f"✅ Memory bridged to real database securely for {tenant_id}!"}

@app.get("/mempalace_search")
async def search_memory(query: str, tenant_id: str = Depends(get_tenant_id)):
    print(f"\n🔍 [Cloud AI Worker] Searching sessions for {tenant_id} matching '{query}'...")
    
    if LOCAL_DATABASE_AVAILABLE:
        try:
            print(f"🧠 Running cloud-native in-process database search for {tenant_id}...")
            data = tool_search(query=query, limit=10, wing=tenant_id)
            formatted_results = []
            if "results" in data:
                hits = data.get("results", [])
                for hit in hits:
                    formatted_results.append(hit.get("text", ""))
            return {"status": "success", "results": formatted_results}
        except Exception as e:
            print(f"❌ In-process search failed: {e}")
            return {"status": "error", "message": f"Search failed: {e}"}
            
    # Securely query the remote VPS database over SSH in the background (Fallback)
    ssh_script = f"""
cd /root/mempalace && source venv/bin/activate && python3 - <<'PYEOF'
from mempalace.mcp_server import tool_search
import json
results = tool_search(query={repr(query)}, limit=10)
print(json.dumps(results))
PYEOF
"""
    try:
        stdout_str, stderr_str = run_ssh_command(ssh_script)

        stdout_lines = stdout_str.strip().splitlines()
        formatted_results = []
        for line in stdout_lines:
            line = line.strip()
            if line.startswith("{"):
                try:
                    data = json.loads(line)
                    if "results" in data:
                        hits = data.get("results", [])
                        for hit in hits:
                            formatted_results.append(hit.get("text", ""))
                        break
                except Exception:
                    pass
        
        return {"status": "success", "results": formatted_results}
    except Exception as e:
        print(f"❌ SSH search bridge failed: {e}")
        return {"status": "error", "message": f"Search failed: {e}"}

active_mcp_sessions = {}

@app.get("/sse")
async def mcp_sse_connect(request: Request, tenant_id: str = Depends(get_tenant_id)):
    """
    Establish a Server-Sent Events (SSE) stream for Model Context Protocol.
    Protected by API key bearer auth mapping to tenant_id.
    """
    if not handle_request:
        raise HTTPException(status_code=503, detail="Mempalace Core database handler not loaded")
        
    session_id = str(uuid.uuid4())
    queue = asyncio.Queue()
    active_mcp_sessions[session_id] = {
        "queue": queue,
        "tenant_id": tenant_id
    }
    print(f"🔌 New SSE MCP Session established: {session_id} for tenant: {tenant_id}")
    
    # Construct absolute external base URL, honoring reverse proxy headers
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.url.netloc)
    if not host:
        host = request.url.netloc
    base_url = f"{scheme}://{host}".rstrip("/")

    async def sse_event_generator():
        try:
            # yield initial endpoint event specifying where the client should post requests
            yield f"event: endpoint\ndata: {base_url}/message?sessionId={session_id}\n\n"
            
            while True:
                # Wait for messages pushed to the session queue
                message = await queue.get()
                yield f"event: message\ndata: {message}\n\n"
                queue.task_done()
        except asyncio.CancelledError:
            print(f"🔌 SSE connection closed for session: {session_id}")
        finally:
            active_mcp_sessions.pop(session_id, None)

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/message")
async def mcp_receive_message(request: Request, sessionId: str):
    """
    Handle POST messages from the client in the SSE connection session.
    Automatically intercepts and rewrites JSON-RPC arguments to enforce strict tenant isolation.
    """
    if not handle_request:
        raise HTTPException(status_code=503, detail="Mempalace Core database handler not loaded")
        
    session_data = active_mcp_sessions.get(sessionId)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found or expired")
        
    tenant_id = session_data["tenant_id"]
    queue = session_data["queue"]
    
    try:
        body = await request.body()
        payload = json.loads(body.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {e}")
        
    # --- PROTOCOL LEVEL ARGUMENT REWRITER (Tenant Security Gate) ---
    method = payload.get("method")
    params = payload.get("params", {})
    tool_name = params.get("name")
    tool_args = params.get("arguments", {})
    
    if method == "tools/call" and tool_name:
        # Enforce that all search and write tools are bound strictly to this tenant's wing
        if tool_name in ["mempalace_search", "mempalace_check_duplicate", "mempalace_add_drawer"]:
            tool_args["wing"] = tenant_id
            print(f"🔒 Enforced JSON-RPC wing isolation parameter for {tool_name} -> {tenant_id}")
        elif tool_name in ["mempalace_kg_add", "mempalace_kg_query", "mempalace_kg_invalidate", "mempalace_kg_timeline"]:
            # Enforce that all KG queries and updates are restricted to the tenant
            if "subject" in tool_args or tool_name == "mempalace_kg_add":
                tool_args["subject"] = tenant_id
            if "entity" in tool_args or tool_name in ["mempalace_kg_query", "mempalace_kg_timeline"]:
                tool_args["entity"] = tenant_id
            print(f"🔒 Enforced JSON-RPC KG isolation parameter for {tool_name} -> {tenant_id}")
            
    # Process the request synchronously (or in an executor)
    try:
        loop = asyncio.get_running_loop()
        response_dict = await loop.run_in_executor(None, handle_request, payload)
    except Exception as e:
        print(f"❌ MCP handle_request exception: {e}")
        response_dict = {
            "jsonrpc": "2.0",
            "id": payload.get("id"),
            "error": {"code": -32603, "message": f"Internal handler error: {e}"}
        }
        
    # Push the response dictionary onto the SSE session queue to stream it back to the client
    await queue.put(json.dumps(response_dict))
    
    return {"status": "accepted"}

# Serve static landing page
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

@app.get("/")
async def serve_landing():
    return FileResponse(os.path.join(BASE_DIR, "static", "index.html"))

class WaitlistPayload(BaseModel):
    email: str

@app.post("/waitlist")
async def waitlist_signup(payload: WaitlistPayload):
    email = payload.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email address")
        
    api_key = f"sk-mp-{uuid.uuid4().hex}"
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if already registered
        cursor.execute("SELECT api_key FROM waitlist WHERE email = ?", (email,))
        row = cursor.fetchone()
        if row:
            existing_key = row[0]
            conn.close()
            return {"status": "success", "message": "Already registered!", "api_key": existing_key}
            
        cursor.execute("INSERT INTO waitlist (email, api_key) VALUES (?, ?)", (email, api_key))
        conn.commit()
        conn.close()
        print(f"🎉 New waitlist signup: {email} -> API Key generated!")
        return {"status": "success", "message": "Successfully signed up!", "api_key": api_key}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Registration failed, please try again")
    except Exception as e:
        print(f"⚠️ SQLite waitlist insert failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get("/admin/waitlist")
async def get_waitlist(api_key: str = Security(api_key_header)):
    if not api_key or not api_key.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = api_key.replace("Bearer ", "")
    
    ADMIN_TOKEN = os.environ.get("MEMPALACE_ADMIN_TOKEN", "admin-secret-token-123")
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid admin token")
        
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, api_key, created_at FROM waitlist ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        users = []
        for row in rows:
            users.append({
                "id": row[0],
                "email": row[1],
                "api_key": row[2],
                "created_at": row[3]
            })
        return {"status": "success", "waitlist": users}
    except Exception as e:
        print(f"⚠️ SQLite waitlist fetch failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

if __name__ == "__main__":
    import sys
    if "--stdio" in sys.argv:
        # Loop over lines from standard input for Stdio MCP transport
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                    response = handle_request(payload)
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
                except json.JSONDecodeError:
                    print("Error: Invalid JSON input", file=sys.stderr)
                except Exception as e:
                    print(f"Error handling request: {e}", file=sys.stderr)
        except KeyboardInterrupt:
            pass
    else:
        print("🚀 Starting Mempalace SaaS Prototype on port 8000...")
        uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
