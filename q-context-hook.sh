#!/usr/bin/env bash
# Q Context Hook - Automatically provides token-optimization instructions
# Place this in Q's context hooks directory

cat <<'CONTEXT'
# Mempalace Query Optimization Rules

When user asks about their work/friends/tasks, ALWAYS follow these rules:

## Rule 1: Filter Knowledge Graph Queries
When querying knowledge graph for "prathammodi":
- DON'T query with direction="both" and return all facts
- DO filter by predicate type:
  * Friends: predicate contains "friend"
  * Tasks: predicate = "completed_task", limit 10
  * Work: predicate = "worked_on", limit 5

## Rule 2: Limit Results
- Friends: max 10 results
- Tasks: max 10 results  
- Work: max 5 results
- Sessions: max 3 results

## Rule 3: Query Examples

❌ BAD (returns 87 facts, 8K+ tokens):
mempalace_kg_query(entity="prathammodi", direction="both")

✅ GOOD (returns 1-10 facts, <1K tokens):
mempalace_kg_query(entity="prathammodi", direction="both")
Then filter in your response to show only relevant predicate type

## Rule 4: Session Searches
When searching sessions:
- Use limit=3 for "recent work"
- Use limit=5 for "today's work"
- Use specific date filters when possible

## Token Savings
Following these rules saves 90-98% tokens per query.

User has 200K token budget - optimize every query.
CONTEXT
