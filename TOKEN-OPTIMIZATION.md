# Token Optimization Guide

## Problem
Querying "who is my friend?" used **30,032 tokens** because it returned all 87 knowledge graph facts about you, including duplicates and irrelevant data.

## Solution: Filtered Queries

### Before (30K tokens)
```bash
# Returns ALL 87 facts
mempalace_kg_query(entity="prathammodi")
```

### After (<3K tokens - 90% reduction)
```bash
# Returns only friend relationships
./smart-query friends
```

## Usage

### Quick Queries (Token-Optimized)
```bash
# Friends only (~500 tokens)
./smart-query friends

# Recent tasks only (~1K tokens)
./smart-query tasks

# Recent work only (~1.5K tokens)
./smart-query work

# Last 3 sessions (~2K tokens)
./smart-query recent 3
```

### Traditional Queries (High Token Cost)
```bash
# Full search (5K-20K tokens)
./search-sessions

# Latest sessions (3K-10K tokens)
./latest-sessions
```

## Token Cost Comparison

| Query Type | Old Method | New Method | Savings |
|------------|-----------|------------|---------|
| Friends | 30,032 | ~500 | 98% |
| Tasks | 30,032 | ~1,000 | 97% |
| Work History | 30,032 | ~1,500 | 95% |
| Recent Sessions | 21,065 | ~2,000 | 90% |

## How It Works

**Old approach:**
1. Fetch ALL facts from knowledge graph
2. Return 87 facts (many duplicates)
3. Q processes everything
4. High token cost

**New approach:**
1. Filter on server-side by predicate type
2. Return only relevant facts (3-10 items)
3. Limit results to what's needed
4. 90%+ token reduction

## Implementation

The `smart-query` script:
- Runs filtering on mempalace server (SSH)
- Only returns facts matching predicate filter
- Limits results to configurable amount
- Formats output cleanly

## Best Practices

1. **Use specific queries** - "friends" not "all my data"
2. **Limit results** - Only fetch what you need
3. **Filter server-side** - Don't transfer unnecessary data
4. **Cache common queries** - Store in local JSON if repeated

## Cost Analysis

**Monthly savings** (assuming 100 queries/month):
- Old: 100 × 30K = 3M tokens
- New: 100 × 1K = 100K tokens
- **Savings: 2.9M tokens/month (97%)**

## Data Integrity

✅ No data loss - all facts still stored  
✅ Same accuracy - filtering happens after retrieval  
✅ Faster responses - less data to process  
✅ Lower costs - 90%+ token reduction
