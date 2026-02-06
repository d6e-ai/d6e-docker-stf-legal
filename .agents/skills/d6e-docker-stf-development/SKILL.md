---
name: d6e-docker-stf-development
description: Creates custom Docker-based State Transition Functions (STFs) for D6E platform workflows. Use when building containerized business logic for D6E, implementing data processing steps, or creating workflow functions that need database access. Handles JSON input/output, SQL API integration, and multi-language implementations (Python, Node.js, Go).
---

# D6E Docker STF Development

## Overview

Docker STFs are containerized applications that execute as workflow steps in D6E. They read JSON from stdin, process data with custom logic, access workspace databases via internal API, and output JSON to stdout.

## When to Use

Apply this skill when users request:

- "Create a D6E Docker STF that..."
- "Build a custom STF for D6E that..."
- "I need a Docker-based workflow step..."
- "Help me create a data processing function for D6E"

## Core Concepts

### Input Format

Docker STFs receive this JSON via stdin:

```json
{
  "workspace_id": "UUID",
  "stf_id": "UUID",
  "caller": "UUID | null",
  "api_url": "http://api:8080",
  "api_token": "internal_token",
  "input": {
    "operation": "...",
    ...user-defined parameters
  },
  "sources": {
    "step_name": {
      "output": {...previous step data}
    }
  }
}
```

### Output Format

**Success:**

```json
{
  "output": {
    "status": "success",
    ...custom result data
  }
}
```

**Error:**

```json
{
  "error": "Error message",
  "type": "ErrorType"
}
```

### SQL API Access

Execute SQL via internal API:

**Endpoint:** `POST /api/v1/workspaces/{workspace_id}/sql`

**Headers:**

```
Authorization: Bearer {api_token}
X-Internal-Bypass: true
X-Workspace-ID: {workspace_id}
X-STF-ID: {stf_id}
```

**Request:**

```json
{ "sql": "SELECT * FROM my_table LIMIT 10" }
```

**Restrictions:**

- No DDL (CREATE, DROP, ALTER)
- Policy-controlled access
- Workspace scope only

## Quick Start

### Python Implementation

**main.py:**

```python
#!/usr/bin/env python3
import sys
import json
import requests
import logging

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

def execute_sql(api_url, api_token, workspace_id, stf_id, sql):
    """Execute SQL via D6E internal API"""
    url = f"{api_url}/api/v1/workspaces/{workspace_id}/sql"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "X-Internal-Bypass": "true",
        "X-Workspace-ID": workspace_id,
        "X-STF-ID": stf_id,
        "Content-Type": "application/json"
    }
    response = requests.post(url, json={"sql": sql}, headers=headers)
    response.raise_for_status()
    return response.json()

def main():
    try:
        input_data = json.load(sys.stdin)
        user_input = input_data["input"]

        # Your business logic here
        result = {"status": "success", "message": "Processed"}

        print(json.dumps({"output": result}))
    except Exception as e:
        logging.error(f"Error: {str(e)}", exc_info=True)
        print(json.dumps({"error": str(e), "type": type(e).__name__}))
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**Dockerfile:**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
RUN chmod +x main.py
ENTRYPOINT ["python3", "main.py"]
```

**requirements.txt:**

```
requests>=2.31.0
```

### Node.js Implementation

**index.js:**

```javascript
const axios = require("axios");

async function executeSql(apiUrl, apiToken, workspaceId, stfId, sql) {
  const response = await axios.post(
    `${apiUrl}/api/v1/workspaces/${workspaceId}/sql`,
    { sql },
    {
      headers: {
        Authorization: `Bearer ${apiToken}`,
        "X-Internal-Bypass": "true",
        "X-Workspace-ID": workspaceId,
        "X-STF-ID": stfId,
        "Content-Type": "application/json",
      },
    }
  );
  return response.data;
}

async function main() {
  try {
    const input = await readStdin();
    const data = JSON.parse(input);

    // Your business logic here
    const result = { status: "success", message: "Processed" };

    console.log(JSON.stringify({ output: result }));
  } catch (error) {
    console.error("Error:", error.message);
    console.log(
      JSON.stringify({
        error: error.message,
        type: error.name,
      })
    );
    process.exit(1);
  }
}

function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.on("data", (chunk) => (data += chunk));
    process.stdin.on("end", () => resolve(data));
  });
}

main();
```

**Dockerfile:**

```dockerfile
FROM node:18-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY index.js .
ENTRYPOINT ["node", "index.js"]
```

## Implementation Checklist

When creating a Docker STF, ensure:

- [ ] Reads JSON from stdin
- [ ] Outputs JSON to stdout (`{"output": {...}}`)
- [ ] Logs to stderr (stdout is for results only)
- [ ] Handles errors gracefully
- [ ] Uses small base images (e.g., `python:3.11-slim`)
- [ ] Includes error type in error responses
- [ ] Validates input parameters
- [ ] Uses environment variables for configuration

## Best Practices

### Security

- Never log sensitive data (tokens, passwords)
- Validate all user inputs
- Use parameterized SQL queries
- Keep dependencies up-to-date

### Performance

- Use multi-stage builds to reduce image size
- Minimize dependencies
- Add `.dockerignore` to exclude unnecessary files
- Cache pip/npm installations

### Error Handling

```python
try:
    # Your logic
    result = process_data(input_data)
    print(json.dumps({"output": result}))
except ValueError as e:
    # Validation errors
    logging.error(f"Validation error: {str(e)}")
    print(json.dumps({"error": str(e), "type": "ValidationError"}))
    sys.exit(1)
except Exception as e:
    # Unexpected errors
    logging.error(f"Unexpected error: {str(e)}", exc_info=True)
    print(json.dumps({"error": str(e), "type": type(e).__name__}))
    sys.exit(1)
```

### Logging

```python
import logging

# Log to stderr
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("Processing started")
logging.debug(f"Input: {input_data}")  # Detailed logs
logging.warning("Deprecated operation used")
logging.error("Failed to process", exc_info=True)
```

## Common Patterns

### Data Validation Pattern

```python
def validate_input(user_input):
    required_fields = ["operation", "table_name"]
    for field in required_fields:
        if field not in user_input:
            raise ValueError(f"Missing required field: {field}")

    if user_input["operation"] not in ["query", "insert", "update"]:
        raise ValueError(f"Invalid operation: {user_input['operation']}")

    return True

# Usage
try:
    validate_input(input_data["input"])
except ValueError as e:
    print(json.dumps({"error": str(e), "type": "ValidationError"}))
    sys.exit(1)
```

### Database Query Pattern

```python
def safe_query(api_context, table_name, filters):
    """Execute a safe parameterized query"""
    # Build WHERE clause safely
    where_conditions = []
    for key, value in filters.items():
        # Simple validation
        if not key.isidentifier():
            raise ValueError(f"Invalid column name: {key}")
        where_conditions.append(f"{key} = '{value}'")

    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
    sql = f"SELECT * FROM {table_name} WHERE {where_clause} LIMIT 100"

    return execute_sql(
        api_context["api_url"],
        api_context["api_token"],
        api_context["workspace_id"],
        api_context["stf_id"],
        sql
    )
```

### External API Pattern

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    """Create session with retry logic"""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def call_external_api(url, params):
    """Call external API with error handling"""
    session = create_session()
    try:
        response = session.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        raise Exception("External API timeout")
    except requests.RequestException as e:
        raise Exception(f"External API error: {str(e)}")
```

## Testing Locally

### Build and Test

```bash
# Build image
docker build -t my-stf:latest .

# Test with sample input
echo '{
  "workspace_id": "test-id",
  "stf_id": "test-stf-id",
  "caller": null,
  "api_url": "http://localhost:8080",
  "api_token": "test-token",
  "input": {
    "operation": "test"
  },
  "sources": {}
}' | docker run --rm -i my-stf:latest
```

### Debug Mode

```bash
# Run with interactive shell
docker run --rm -it --entrypoint /bin/bash my-stf:latest

# Check image size
docker images my-stf:latest

# Inspect logs
docker run --rm -i my-stf:latest < input.json 2>&1 | tee output.log
```

## Troubleshooting

### Issue: "Policy violation" error

**Cause:** STF doesn't have permission to access the table.

**Solution:** Create policies:

```javascript
// Create policy group
d6e_create_policy_group({ name: "my-stf-group" });

// Add STF to group
d6e_add_member_to_policy_group({
  policy_group_id: "{group_id}",
  member_type: "stf",
  member_id: "{stf_id}",
});

// Grant access
d6e_create_policy({
  policy_group_id: "{group_id}",
  table_name: "my_table",
  operation: "select",
  mode: "allow",
});
```

### Issue: Output not appearing in D6E

**Cause:** Output not in correct JSON format.

**Solution:** Always use `{"output": {...}}` format:

```python
# ✅ Correct
print(json.dumps({"output": {"status": "success"}}))

# ❌ Wrong
print(json.dumps({"status": "success"}))
```

### Issue: "Image not found" in D6E

**Cause:** Image not accessible from D6E API server.

**Solution:**

1. Publish to container registry (GitHub, Docker Hub)
2. Or ensure same Docker daemon as D6E API server

### Issue: Large image size

**Solution:** Use multi-stage builds:

```dockerfile
# Build stage
FROM python:3.11 AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY main.py .
ENV PATH=/root/.local/bin:$PATH
ENTRYPOINT ["python3", "main.py"]
```

## File Requirements

Every Docker STF should include:

```
my-stf/
├── main.py (or index.js, main.go)  # Entry point
├── Dockerfile                       # Container definition
├── requirements.txt (or package.json, go.mod)  # Dependencies
├── .dockerignore                    # Exclude files
└── README.md                        # Documentation
```

**.dockerignore:**

```
.git
.gitignore
*.md
tests/
__pycache__/
*.pyc
node_modules/
.env
```

## README Template for D6E AI Agent Users

When publishing a Docker STF, include a comprehensive README that enables D6E AI agents to automatically create and execute workflows. The README should follow this structure:

### Required README Sections

1. **Title and Description** - Clear name and purpose of the STF
2. **Docker Image URL** - Full path (e.g., `ghcr.io/d6e-ai/stf-xxx:latest`)
3. **LLM/AI Agent Usage Instructions** - Step-by-step STF creation guide
4. **Supported Operations** - Table of available operations with parameters
5. **Input/Output Examples** - Concrete JSON examples for each operation
6. **AI Agent Prompts** - Ready-to-use prompts for common tasks
7. **Troubleshooting** - Common issues and solutions
8. **Local Build and Test** - Commands for local development

### README Template

Use the following template for your Docker STF README:

````markdown
# {STF Name}

{Brief description of what this STF does}

**Docker Image**: `ghcr.io/{org}/{stf-name}:latest`

## Usage for LLM/AI Agents

To use this Docker image from a D6E AI agent, follow these steps to create and execute the STF.

### Step 1: Create the STF

```javascript
d6e_create_stf({
  name: "{stf-name}",
  description: "{Description of the STF functionality}",
});
```

### Step 2: Create the STF Version

```javascript
d6e_create_stf_version({
  stf_id: "{stf_id from Step 1}",
  version: "1.0.0",
  runtime: "docker",
  code: '{"image":"ghcr.io/{org}/{stf-name}:latest"}',
});
```

**Important**: Always set `runtime` to `"docker"` and format the `code` field as a JSON string: `{"image":"ghcr.io/{org}/{stf-name}:latest"}`.

### Step 3: Create the Workflow

```javascript
d6e_create_workflow({
  name: "{stf-name}-workflow",
  input_steps: [],
  stf_steps: [
    {
      stf_id: "{stf_id}",
      version: "1.0.0",
    },
  ],
  effect_steps: [],
});
```

### Step 4: Execute the Workflow

```javascript
d6e_execute_workflow({
  workflow_id: "{workflow_id}",
  input: {
    operation: "{operation_name}",
    // ...operation-specific parameters
  },
});
```

## Supported Operations

| Operation | Required Parameters | Optional | DB Required | Description |
|-----------|---------------------|----------|-------------|-------------|
| `{operation_1}` | `param1`, `param2` | `optional1` | ❌/✅ | {Description} |
| `{operation_2}` | `param1` | - | ❌/✅ | {Description} |

## Input/Output Examples

### {Operation Name}

**Input**:

```json
{
  "operation": "{operation_name}",
  "param1": "value1",
  "param2": "value2"
}
```

**Output**:

```json
{
  "output": {
    "status": "success",
    "operation": "{operation_name}",
    "data": {
      // ... result data
    }
  }
}
```

## 🤖 Prompts for AI Agents

### Basic Prompt

```
Use the Docker skill for {task description} in D6E.

Docker Image: ghcr.io/{org}/{stf-name}:latest

Steps:
1. Create STF with d6e_create_stf (name: "{stf-name}")
2. Create STF version with d6e_create_stf_version:
   - runtime: "docker"
   - code: "{\"image\":\"ghcr.io/{org}/{stf-name}:latest\"}"
3. Create workflow with d6e_create_workflow
4. Execute with d6e_execute_workflow

Supported operations:
- "{operation_1}": {description} (required: {required_params})
- "{operation_2}": {description} (required: {required_params})

Start with {recommended_first_operation} to verify the setup.
```

### Task-Specific Prompt

```
{Specific task description}

Skill to use:
- Docker Image: ghcr.io/{org}/{stf-name}:latest
- Operation: {operation_name}

Parameters:
- param1: "value1"
- param2: "value2"

Include the following in the results:
- {Expected output item 1}
- {Expected output item 2}
```

### Complete Execution Prompt

```
{Complete workflow description}

Docker Image: ghcr.io/{org}/{stf-name}:latest

Execution steps:
1. Create STF (name: "{stf-name}", runtime: "docker")

2. {First operation description}:
   - operation: "{operation_1}"
   - param1: value1
   - param2: value2

3. {Second operation description}:
   - operation: "{operation_2}"
   - param1: value1

4. Display results:
   - {Output item 1}
   - {Output item 2}

{Additional instructions or requests}
```

## Troubleshooting

### {Common Issue 1}

{Description and solution}

### {Common Issue 2}

{Description and solution}

## Local Build and Test

```bash
# Build
docker build -t {stf-name}:latest .

# Test
echo '{
  "workspace_id": "test-ws",
  "stf_id": "test-stf",
  "caller": null,
  "api_url": "http://localhost:8080",
  "api_token": "test-token",
  "input": {
    "operation": "{operation_name}",
    "param1": "value1"
  },
  "sources": {}
}' | docker run --rm -i {stf-name}:latest
```

## Related Documentation

- [Project README](../README.md)
- {Additional documentation links}
````

### Key Points for README Creation

1. **Explicit Docker Registration Instructions**
   - Always specify `runtime: "docker"`
   - Format `code` as JSON string: `'{"image":"..."}'`
   - Include the full image path with tag

2. **AI-Friendly Operation Tables**
   - Use consistent table format
   - Clearly mark database requirements (❌/✅)
   - List all required and optional parameters

3. **Ready-to-Use Prompts**
   - Provide multiple prompt examples (basic, specific, complete)
   - Include all necessary parameters in prompts
   - Suggest a recommended first operation for testing

4. **Clear Input/Output Examples**
   - Show complete JSON structures
   - Include both success and error response examples
   - Document all possible output fields

5. **Self-Contained Instructions**
   - Users should be able to copy the README and prompt to an AI agent
   - The AI agent should be able to execute without additional context
   - All steps should be clearly numbered and ordered

## Additional Resources

For detailed information:

- Complete API reference: [reference.md](reference.md)
- More implementation examples: [examples.md](examples.md)
- Quick start guide: [../docs/QUICKSTART.md](../../docs/QUICKSTART.md)
- Testing guide: [../docs/TESTING.md](../../docs/TESTING.md)
- Publishing guide: [../docs/PUBLISHING.md](../../docs/PUBLISHING.md)
