# VerifiMind MCP Server - Common Issues & Solutions

## Understanding HTTP Status Codes

When accessing the VerifiMind MCP Server, you may encounter different HTTP status codes. Here's what they mean and how to fix them:

---

## 🔄 **302 & 307 - Redirects** (Normal Behavior)

**What it means:**
Your request is being automatically redirected to the correct URL.

**Common causes:**
- Accessing `http://` instead of `https://`
- Missing trailing slash on `/mcp` endpoint

**✅ Solution:**
Always use the HTTPS URL with trailing slash:
```
https://verifimind.ysenseai.org/mcp/
```

---

## ❌ **404 - Not Found** (Configuration Error)

**What it means:**
The endpoint you're trying to access doesn't exist on the server.

**Common causes:**
- Typo in the URL
- Accessing non-existent resource paths like `/mcp/resource/`
- Using old/deprecated endpoints

**✅ Solution:**
Use the correct MCP endpoint:
```
https://verifimind.ysenseai.org/mcp/
```

**For MCP Client configuration:**
```json
{
  "mcpServers": {
    "verifimind": {
      "url": "https://verifimind.ysenseai.org/mcp/"
    }
  }
}
```

---

## 🚫 **405 - Method Not Allowed** (Wrong HTTP Method)

**What it means:**
You're using the wrong HTTP method (e.g., POST when only GET is allowed).

**Common causes:**
- Misconfigured MCP client
- Accessing `.well-known/` discovery endpoint with wrong method

**✅ Solution:**
Ensure your MCP client uses:
- **GET** for discovery endpoints
- **POST** for actual MCP method calls

---

## ⚠️ **400 - Bad Request** (Malformed Request)

**What it means:**
The server couldn't understand your request format.

**Common causes:**
- Invalid JSON in request body
- Missing required headers
- Incorrect MCP protocol version

**✅ Solution:**
1. Verify your MCP client is up-to-date
2. Check request headers include `Content-Type: application/json`
3. Validate JSON syntax

---

## Quick Start Guide

### Step 1: Test Basic Connectivity
```bash
curl https://verifimind.ysenseai.org/mcp/
```

### Step 2: Configure Your MCP Client
Add the server to your MCP client configuration:

**Claude Desktop:**
Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "verifimind": {
      "url": "https://verifimind.ysenseai.org/mcp/"
    }
  }
}
```

### Step 3: Verify Connection
Restart your MCP client and verify the VerifiMind server appears in the available tools list.

---

## Still Having Issues?

If you continue to experience errors:
1. Check the server status at: https://verifimind.ysenseai.org/
2. Verify you're using the latest MCP protocol version
3. Review the full error message for specific details
