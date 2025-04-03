In this case we enabled all tools. AI used tools to search news, search/generate images, generate html, and package them into a website.

Visit the case in [yourware](https://qs6umhk5lp.app-staging.yourware.so/)

### .env file content

```bash
DEFAULT_MODEL="bedrock:us.anthropic.claude-3-7-sonnet-20250219-v1:0"
TAVILY_API_KEY=
BFL_API_KEY=
PIXABAY_API_KEY=
```

### mcp.json content

- You need to login to [yourware](https://www.yourware.so/) for automated deployment
- Access [quick-create](https://www.yourware.so/api/v1/api-keys/quick-create) for api key.

```json
{
    "mcpServers": {
        "yourware": {
            "command": "/opt/homebrew/bin/uvx",
            "args": [
                "yourware-mcp@latest",
                "stdio"
            ],
            "env": {
                "YOURWARE_API_KEY": ""
            }
        }
    }
}
```
