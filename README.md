# kovamind

[![Tests](https://github.com/KovaMind/python-sdk/actions/workflows/tests.yml/badge.svg)](https://github.com/KovaMind/python-sdk/actions/workflows/tests.yml)

Python SDK for the **Kova Mind** memory API — give your AI agents persistent, learning memory.

```bash
pip install kovamind
```

## Quickstart

```python
from kovamind import KovaMind

kova = KovaMind(api_key="km_live_xxx")

# Extract memories from a conversation
result = kova.extract(
    conversation=[
        {"role": "user",      "content": "I love dark mode and hate Comic Sans."},
        {"role": "assistant", "content": "Noted! I'll keep that in mind."},
    ],
    user_id="alex",
)

print(f"Extracted {len(result.patterns)} patterns")
for p in result.patterns:
    print(f"  [{p.category}] {p.pattern}  (confidence: {p.confidence:.0%})")

# Recall memories
recall = kova.recall(
    context="The user is asking about text editor settings.",
    user_id="alex",
    max_patterns=5,
)

for p in recall.patterns:
    print(p.pattern)

# Score surprise
surprise = kova.surprise(
    content="Alex now prefers light mode",
    user_id="alex",
)
print(f"Score: {surprise.score:.2f}, Route: {surprise.route}")
```

## API reference

### `KovaMind(api_key, base_url, timeout, session)`

| Parameter | Default | Description |
|-----------|---------|-------------|
| `api_key` | required | Your `km_live_...` or `km_test_...` key |
| `base_url` | `https://api.kovamind.io` | API base URL |
| `timeout` | `30` | Request timeout in seconds |
| `session` | `None` | Optional custom `requests.Session` |

### `extract(conversation, user_id, *, session_id=None)`

Extract memory patterns from a conversation.

### `recall(context, user_id, *, max_patterns=10, min_confidence=0.3)`

Retrieve relevant memory patterns.

### `surprise(content, user_id)`

Score how surprising new content is (0.0 = familiar, 1.0 = contradicts memory).

| Score | Route | Meaning |
|-------|-------|---------|
| < 0.3 | `reinforce` | Already known |
| 0.3-0.7 | `update` | New information |
| > 0.7 | `contradict` | Conflicts with memory |

### `reinforce(pattern_id, reinforcement_type, *, context=None)`

Confirm, deny, strengthen, or weaken a stored pattern.

### `health()`

Check API health (no auth required).

## Error handling

```python
from kovamind import KovaMind, AuthError, RateLimitError, NotFoundError, KovaMindError

try:
    result = kova.recall(context="editor preferences", user_id="alex")
except AuthError:
    print("Check your API key")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except NotFoundError:
    print("Resource not found")
except KovaMindError as e:
    print(f"API error {e.status_code}: {e}")
```

## License

MIT
