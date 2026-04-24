#!/usr/bin/env bash
# AI Observer - Session analytics
source config.env 2>/dev/null || { MEMPALACE_SERVER=192.168.1.137; USERNAME=prathammodi; }

ssh root@$MEMPALACE_SERVER "cd /root/mempalace && source venv/bin/activate && python - <<'PY'
from mempalace.mcp_server import _get_collection, tool_kg_query
import json
from datetime import datetime
from collections import Counter

col = _get_collection()
results = col.get(where={'wing': 'ai-observer'}, limit=1000)

sessions = []
for doc in results['documents']:
    try:
        sessions.append(json.loads(doc))
    except:
        pass
if not sessions:
    print('No sessions found')
    exit()
sessions.sort(key=lambda x: x['timestamp'], reverse=True)

# Stats
total = len(sessions)
dates = Counter(s['timestamp'][:10] for s in sessions)
techs = Counter()
for s in sessions:
    techs.update(s.get('technologies', []))

print('📊 AI Observer Analytics')
print('=' * 50)
print(f'Total sessions: {total}')
print(f'Date range: {sessions[-1][\"timestamp\"][:10]} → {sessions[0][\"timestamp\"][:10]}')
print()

print('📅 Sessions per day (last 7 days):')
for date, count in sorted(dates.items(), reverse=True)[:7]:
    print(f'  {date}: {count} sessions')
print()

print('🔧 Top technologies:')
for tech, count in techs.most_common(10):
    print(f'  {tech}: {count}')
print()

print('📈 Recent sessions:')
for s in sessions[:5]:
    print(f'  {s[\"timestamp\"]}: {s[\"summary\"][:60]}...')
PY
"
