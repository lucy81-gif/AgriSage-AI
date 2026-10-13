# First-party MCP server

AgriSage AI exposes the same audited tool boundary used by the agent through the
Python MCP SDK. Tools are read-only for evidence retrieval, except for
`draft_advisory` and `create_follow_up`, which write to the configured SQLAlchemy
database (SQLite locally or PostgreSQL when `DATABASE_URL` is set) and are logged.

From the repository root, after installing `requirements.txt`:

```powershell
python mcp-server/server.py
```

The server uses stdio transport so an MCP-compatible host can launch it as a
child process. Set `DATABASE_URL` in `.env` when the host should use a database
other than the default SQLite file.

The LangGraph agent launches this server with the MCP Python SDK over stdio,
lists its tools, and invokes each selected tool through the protocol. Tool
inputs, results, timing, and failures are recorded by the API process in
`tool_call_logs`, so server handlers do not create duplicate records.
