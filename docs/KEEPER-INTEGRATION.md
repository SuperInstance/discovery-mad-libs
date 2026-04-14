# Lighthouse Keeper Integration

## What It Does

A lighthouse keeper on the network can authenticate the discovery engine and provide API keys dynamically, so keys don't need to be stored locally. The keeper acts as a proxy:

```
Discovery Engine → Keeper → LLM Provider
                  ↑
            Authenticates
            the engine,
            provides key,
            proxies the call
```

## Setup

### 1. Keeper Mode: Local (default)
All API calls go directly to providers using keys in `.env`:
```
KEEPER_MODE=local
```

### 2. Keeper Mode: Proxy
All LLM calls route through the keeper:
```
KEEPER_MODE=proxy
KEEPER_URL=https://your-keeper.example.com
KEEPER_TOKEN=your-engine-auth-token
```

The keeper:
- Authenticates the discovery engine via token
- Selects the appropriate API key for the requested model
- Proxies the LLM call
- Returns the response
- Logs usage for fleet accounting

### 3. Keeper Mode: Key Fetch
Fetch keys from keeper, then call providers directly:
```
KEEPER_MODE=key-fetch
KEEPER_URL=https://your-keeper.example.com
KEEPER_TOKEN=your-engine-auth-token
```

## For Fleet Operators

If you're running a lighthouse keeper (like Oracle1), you can:

1. Register discovery engines by issuing tokens
2. Control which models each engine can access
3. Rotate API keys without updating every engine's .env
4. Track token spend per engine
5. Rate-limit engines that are burning too many tokens

## Hot-Swapping Models

The model registry supports hot-swapping mid-session:

```python
from engine.models import call, list_models

# Start with a fast model for iteration
result = call("generate hypothesis", model_alias="fast")

# Switch to a quality model for evaluation
eval_result = call("evaluate this", model_alias="quality")

# Or call a specific provider/model directly
result = call("test", model_alias="deepinfra/Qwen/Qwen3-235B-A22B")
```

Templates can specify which model to use for each phase:
```json
{
  "models": {
    "generate": "fast",
    "evaluate": "quality",
    "fix": "code"
  }
}
```

## Adding New Providers

Add to `engine/models.py`:
```python
PROVIDERS["my-provider"] = {
    "url_env": "MY_PROVIDER_URL",
    "key_env": "MY_PROVIDER_API_KEY", 
    "default_url": "https://api.myprovider.com/v1/chat/completions",
}

MODELS["my-alias"] = ("my-provider", "my-model-id")
```

Then add to `.env`:
```
MY_PROVIDER_API_KEY=your_key
MY_PROVIDER_URL=https://api.myprovider.com/v1/chat/completions
```

No code changes needed in the discovery engine — it picks up new providers from the registry.
