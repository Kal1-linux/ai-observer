# Claude Instructions

## Memory Protocol

**CRITICAL:** Before answering questions about people, projects, or past work:

1. **ALWAYS check mempalace FIRST** using these tools:
   - `mempalace_kg_query` - for people/relationships
   - `mempalace_search` - for work history/sessions

2. **Never guess** - if asked about a person/project, query mempalace before responding

3. **Examples:**
   - "Who is Nikhil?" → `mempalace_kg_query(entity="Nikhil")`
   - "What did I work on?" → `mempalace_search(query="work sessions")`
   - "Tell me about my friends" → `mempalace_kg_query(entity="prathammodi")` then query each friend

## Available Tools

- `mempalace_kg_query` - Query knowledge graph for facts
- `mempalace_search` - Semantic search across all stored data
- `mempalace_kg_timeline` - See chronological history
- `mempalace_list_wings` - See what's stored

**Remember:** Storage is not memory, but storage + this protocol = memory.
