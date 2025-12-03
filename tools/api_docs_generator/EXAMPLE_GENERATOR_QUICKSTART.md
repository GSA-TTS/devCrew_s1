# ExampleGenerator - Quick Start Guide

## Installation

```bash
pip install structlog
```

## 5-Minute Quick Start

### 1. Basic Usage

```python
from tools.api_docs_generator.example_generator import ExampleGenerator

# Initialize
gen = ExampleGenerator(base_url="https://api.example.com")

# Define OpenAPI operation spec
spec = {
    "requestBody": {
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email"}
                    }
                }
            }
        }
    }
}

# Generate examples
curl = gen.generate_curl("/users", "POST", spec)
python = gen.generate_python("/users", "POST", spec)
javascript = gen.generate_javascript("/users", "POST", spec)

print(curl)
print(python)
print(javascript)
```

### 2. With Authentication

```python
# Bearer token
auth = {"type": "bearer", "token": "your_token_here"}

curl = gen.generate_curl("/users", "POST", spec, auth=auth)
# Output includes: -H "Authorization: Bearer your_token_here"
```

### 3. Generate All Examples

```python
# Full OpenAPI spec
openapi_spec = {
    "paths": {
        "/users": {
            "get": {"parameters": []},
            "post": {"requestBody": {...}}
        }
    }
}

# Generate for all endpoints
all_examples = gen.generate_all_examples(openapi_spec, auth=auth)

# Access examples
print(all_examples["/users"]["get"]["curl"])
print(all_examples["/users"]["post"]["python"])
```

## Common Patterns

### GET with Query Parameters

```python
spec = {
    "parameters": [
        {"name": "page", "in": "query", "schema": {"type": "integer"}, "example": 1},
        {"name": "limit", "in": "query", "schema": {"type": "integer"}, "example": 10}
    ]
}

curl = gen.generate_curl("/users", "GET", spec)
# Output: curl -X GET https://api.example.com/users?page=1&limit=10
```

### POST with Body

```python
spec = {
    "requestBody": {
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "example": "John Doe"},
                        "age": {"type": "integer", "example": 30}
                    }
                }
            }
        }
    }
}

python = gen.generate_python("/users", "POST", spec, auth=auth)
```

### Path Parameters

```python
spec = {
    "parameters": [
        {"name": "id", "in": "path", "schema": {"type": "string"}, "example": "123"}
    ]
}

curl = gen.generate_curl("/users/{id}", "GET", spec)
# Output: curl -X GET https://api.example.com/users/123
```

## Authentication Types

### Bearer Token
```python
auth = {"type": "bearer", "token": "SECRET_TOKEN"}
```

### API Key
```python
auth = {"type": "apikey", "name": "X-API-Key", "value": "YOUR_KEY"}
```

### Basic Auth
```python
auth = {"type": "basic", "credentials": "base64_encoded"}
```

## Output Examples

### cURL
```bash
curl -X POST https://api.example.com/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"name": "John Doe", "email": "john@example.com"}'
```

### Python
```python
import requests

headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer TOKEN"
}

data = {"name": "John Doe", "email": "john@example.com"}

response = requests.post(
    "https://api.example.com/users",
    headers=headers,
    json=data
)

if response.status_code == 200:
    print(response.json())
else:
    print(f"Error: {response.status_code}")
    print(response.text)
```

### JavaScript
```javascript
const requestData = {"name": "John Doe", "email": "john@example.com"};

const url = "https://api.example.com/users";

const options = {
  "method": "POST",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer TOKEN"
  },
  "body": JSON.stringify(requestData)
};

fetch(url, options)
  .then(response => {
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  })
  .then(data => console.log('Success:', data))
  .catch(error => console.error('Error:', error));
```

## Pro Tips

1. **Set Base URL:** `gen.set_base_url("https://api.staging.example.com")`
2. **Add Examples to Schema:** Include `"example"` fields for better output
3. **Required Fields Only:** Only required fields are included by default
4. **Error Handling:** Module gracefully handles malformed specs
5. **Logging:** Uses structlog for debugging

## Documentation

- **Full Usage Guide:** `EXAMPLE_GENERATOR_USAGE.md`
- **Implementation Details:** `EXAMPLE_GENERATOR_IMPLEMENTATION.md`
- **Module Documentation:** Inline docstrings in `example_generator.py`

## Support

For issues or questions:
1. Check the full usage guide
2. Review inline documentation
3. Check implementation details for advanced features

**Status:** Production Ready ✅
**Version:** 1.0.0
**Dependencies:** structlog, typing, json
