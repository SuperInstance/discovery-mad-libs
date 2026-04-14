#!/usr/bin/env python3
"""
Model Registry — connects to any LLM via .env config or lighthouse keeper.
Hot-swaps models mid-session. Keeper can authenticate and proxy calls.
"""

import json
import os
import subprocess
from pathlib import Path

try:
    from dotenv import dotenv_values
except ImportError:
    def dotenv_values(path):
        """Minimal .env parser."""
        vals = {}
        try:
            for line in Path(path).read_text().splitlines():
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    vals[k.strip()] = v.strip()
        except:
            pass
        return vals

BASE = Path(__file__).parent.parent
ENV_FILE = BASE / ".env"

# ─── Load Environment ───

def load_env():
    """Load .env file into environment."""
    env = dotenv_values(ENV_FILE)
    for k, v in env.items():
        if v and not os.environ.get(k):
            os.environ[k] = v
    return env

# ─── Model Registry ───

MODELS = {
    # alias: (provider, model_id)
    "fast": ("groq", "compound-beta-mini"),
    "quick": ("deepinfra", "meta-llama/Llama-3.3-70B-Instruct-Turbo"),
    "quality": ("deepinfra", "deepseek-ai/DeepSeek-V3-0324"),
    "smart": ("deepinfra", "Qwen/Qwen3-235B-A22B"),
    "code": ("deepinfra", "deepseek-ai/DeepSeek-V3-0324"),
    "creative": ("deepinfra", "Qwen/Qwen3-235B-A22B"),
    "evaluator": ("deepinfra", "meta-llama/Llama-3.3-70B-Instruct-Turbo"),
}

PROVIDERS = {
    "groq": {
        "url_env": "GROQ_URL",
        "key_env": "GROQ_API_KEY",
        "default_url": "https://api.groq.com/openai/v1/chat/completions",
    },
    "deepinfra": {
        "url_env": "DEEPINFRA_URL",
        "key_env": "DEEPINFRA_API_KEY",
        "default_url": "https://api.deepinfra.com/v1/openai/chat/completions",
    },
    "openai": {
        "url_env": "OPENAI_URL",
        "key_env": "OPENAI_API_KEY",
        "default_url": "https://api.openai.com/v1/chat/completions",
    },
}

# ─── Keeper Integration ───

def call_via_keeper(prompt, model_id, keeper_url, keeper_token, max_tokens=2000):
    """Route LLM call through a lighthouse keeper for key management."""
    body = json.dumps({
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.8,
    })
    try:
        r = subprocess.run(
            ["curl", "-s", "-X", "POST",
             f"{keeper_url}/v1/chat/completions",
             "-H", f"Authorization: Bearer {keeper_token}",
             "-H", "Content-Type: application/json",
             "-d", body],
            capture_output=True, text=True, timeout=120
        )
        resp = json.loads(r.stdout)
        return resp["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ERROR: Keeper call failed: {e}"

# ─── Main Call Function ───

def call(prompt, model_alias="quick", max_tokens=2000, temperature=0.8):
    """Call an LLM by alias. Routes through keeper if configured."""
    load_env()
    
    # Check keeper mode
    keeper_mode = os.environ.get("KEEPER_MODE", "local")
    if keeper_mode == "proxy" and os.environ.get("KEEPER_URL"):
        keeper_url = os.environ["KEEPER_URL"]
        keeper_token = os.environ.get("KEEPER_TOKEN", "")
        # Resolve model ID from alias
        provider, model_id = MODELS.get(model_alias, ("deepinfra", model_alias))
        return call_via_keeper(prompt, model_id, keeper_url, keeper_token, max_tokens)
    
    # Direct call
    if model_alias in MODELS:
        provider, model_id = MODELS[model_alias]
    else:
        # Try parsing "provider/model" format
        if "/" in model_alias:
            provider, model_id = model_alias.split("/", 1)
        else:
            provider, model_id = "deepinfra", model_alias
    
    prov = PROVIDERS.get(provider, {})
    url = os.environ.get(prov.get("url_env", ""), prov.get("default_url", ""))
    key = os.environ.get(prov.get("key_env", ""), "")
    
    if not url or not key:
        return f"ERROR: No URL or key for provider {provider}"
    
    body = json.dumps({
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    })
    
    try:
        r = subprocess.run(
            ["curl", "-s", "-X", "POST", url,
             "-H", f"Authorization: Bearer {key}",
             "-H", "Content-Type: application/json",
             "-d", body],
            capture_output=True, text=True, timeout=120
        )
        resp = json.loads(r.stdout)
        return resp["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ERROR: {e}"

# ─── Registry Management ───

def list_models():
    """List all available model aliases."""
    load_env()
    print("Available models:")
    for alias, (provider, model_id) in MODELS.items():
        key_env = PROVIDERS.get(provider, {}).get("key_env", "")
        has_key = "✓" if os.environ.get(key_env) else "✗"
        print(f"  {alias:12s} {provider}/{model_id:45s} key:{has_key}")
    
    keeper = os.environ.get("KEEPER_URL", "")
    if keeper:
        print(f"\n  Keeper: {keeper} (mode: {os.environ.get('KEEPER_MODE', 'local')})")

def add_model(alias, provider, model_id):
    """Add or update a model in the registry."""
    MODELS[alias] = (provider, model_id)
    # TODO: persist to .env or config file

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_models()
    elif len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        print(call(prompt))
    else:
        list_models()
