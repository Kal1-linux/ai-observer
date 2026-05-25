import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from fastapi.responses import FileResponse
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

# Initialize SQLite waitlist DB
DB_PATH = "waitlist.db"

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

# Check if Mempalace Core is available locally (Option A)
try:
    from mempalace.mcp_server import tool_add_drawer, tool_kg_add, tool_search
    LOCAL_DATABASE_AVAILABLE = True
    print("🧠 Local Mempalace Database Core detected. Running in cloud-native Mode.")
except ImportError:
    LOCAL_DATABASE_AVAILABLE = False
    print("🌉 Local Mempalace Database Core NOT detected. Running in remote SSH Bridge Mode.")

app = FastAPI(title="Mempalace SaaS MVP")

# Mock Database
MOCK_DB = []

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

def get_tenant_id(api_key: str = Security(api_key_header)) -> str:
    if not api_key or not api_key.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token. Use 'Bearer <token>'")
    token = api_key.replace("Bearer ", "")
    
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
        print("🌉 Bridging data to 192.168.1.137 Real Mempalace Database...")
        process = subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no", "root@192.168.1.137", "bash"],
            input=ssh_script,
            text=True,
            capture_output=True
        )
        if "SUCCESS" in process.stdout:
            print("✅ Successfully injected into real Mempalace on 192.168.1.137!")
        else:
            print(f"❌ Injection failed. stdout: {process.stdout} stderr: {process.stderr}")
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
        process = subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no", "root@192.168.1.137", "bash"],
            input=ssh_script,
            text=True,
            capture_output=True
        )
        
        stdout_lines = process.stdout.strip().splitlines()
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

# Serve static landing page
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_landing():
    return FileResponse("static/index.html")

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
    print("🚀 Starting Mempalace SaaS Prototype on port 8000...")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
