# Codebase Memory MCP

## Available Tools

### Indexing
- `index_repository` - Index a repository into the knowledge graph
- `list_projects` - List all indexed projects
- `delete_project` - Remove a project
- `index_status` - Check indexing status

### Querying
- `search_graph` - Search by label, name pattern, file pattern
- `trace_call_path` - BFS traversal - who calls a function and what it calls
- `query_graph` - Execute Cypher-like queries
- `search_code` - Grep-like text search with graph enrichment

### Analysis
- `get_code_snippet` - Read source code for a function
- `get_graph_schema` - Get node/edge types
- `get_architecture` - Codebase overview: languages, packages, routes
- `detect_changes` - Map git diff to affected symbols
- `manage_adr` - Architecture Decision Records

## Quick Usage

```bash
# Index current project
codebase-memory-mcp cli index_repository '{"repo_path": "D:/work/datastore"}'

# Search for functions
codebase-memory-mcp cli search_graph '{"project": "datastore", "label": "Function", "name_pattern": ".*holdings.*"}'

# Get architecture
codebase-memory-mcp cli get_architecture '{"project": "datastore"}'
```

## MCP Configuration

Add to your OpenCode/Claude config:

```json
{
  "mcpServers": {
    "codebase-memory-mcp": {
      "command": "C:/Users/life8/.local/bin/codebase-memory-mcp.exe"
    }
  }
}
```

## Skills Available

Use these skills when working with codebase-memory-mcp:
- `codebase-memory-exploring` - For exploring code structure
- `codebase-memory-tracing` - For call chain analysis
- `codebase-memory-quality` - For code quality analysis
- `codebase-memory-reference` - For MCP tool reference