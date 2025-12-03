# ExampleGenerator Module Usage Guide

## Overview

The `ExampleGenerator` module generates code examples (cURL, Python, JavaScript) from OpenAPI specifications for API documentation.

## Installation

```bash
pip install structlog
```

## Basic Usage

```python
from example_generator import ExampleGenerator

# Initialize with base URL
generator = ExampleGenerator(base_url="https://api.example.com")

# Define an OpenAPI operation spec
operation_spec = {
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "schema": {"type": "string"}
        }
    ],
    "requestBody": {
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email"}
                    },
                    "required": ["name", "email"]
                }
            }
        }
    }
}

# Generate examples
auth_config = {"type": "bearer", "token": "YOUR_TOKEN"}

curl_example = generator.generate_curl(
    "/users/{id}",
    "POST",
    operation_spec,
    auth=auth_config
)

python_example = generator.generate_python(
    "/users/{id}",
    "POST",
    operation_spec,
    auth=auth_config
)

javascript_example = generator.generate_javascript(
    "/users/{id}",
    "POST",
    operation_spec,
    auth=auth_config
)
```

## Generated Examples

### cURL Example

```bash
curl -X POST https://api.example.com/users/string \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
  "name": "string",
  "email": "user@example.com"
}'
```

### Python Example

```python
import requests

# API request
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_TOKEN"
}

data = {
    "name": "string",
    "email": "user@example.com"
}

response = requests.post(
    "https://api.example.com/users/string",
    headers=headers,
    json=data
)

# Check response
if response.status_code == 200:
    print(response.json())
else:
    print(f"Error: {response.status_code}")
    print(response.text)
```

### JavaScript Example

```javascript
// API request using fetch

const requestData = {
  "name": "string",
  "email": "user@example.com"
};

const url = "https://api.example.com/users/string";

const options = {
  "method": "POST",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_TOKEN"
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
  .then(data => {
    console.log('Success:', data);
  })
  .catch(error => {
    console.error('Error:', error);
  });
```

## Authentication Methods

### Bearer Token

```python
auth = {
    "type": "bearer",
    "token": "your_token_here"
}
```

### API Key

```python
auth = {
    "type": "apikey",
    "name": "X-API-Key",  # Header name
    "value": "your_api_key_here"
}
```

### Basic Authentication

```python
auth = {
    "type": "basic",
    "credentials": "base64_encoded_credentials"
}
```

## Generate Examples for All Operations

```python
# Complete OpenAPI specification
openapi_spec = {
    "paths": {
        "/users": {
            "get": {
                "parameters": [
                    {
                        "name": "page",
                        "in": "query",
                        "schema": {"type": "integer"}
                    }
                ]
            },
            "post": {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

# Generate all examples
all_examples = generator.generate_all_examples(
    openapi_spec,
    auth={"type": "bearer", "token": "TOKEN"}
)

# Access examples by path and method
print(all_examples["/users"]["get"]["curl"])
print(all_examples["/users"]["post"]["python"])
```

## Generate Examples for Single Operation

```python
examples = generator.generate_examples_for_operation(
    path="/users/{id}",
    method="POST",
    operation_spec=operation_spec,
    auth=auth_config,
    languages=["curl", "python"]  # Optional: specify languages
)

# Returns: {"curl": "...", "python": "..."}
```

## Advanced Features

### Query Parameters (GET Requests)

```python
get_spec = {
    "parameters": [
        {
            "name": "page",
            "in": "query",
            "schema": {"type": "integer"},
            "example": 1
        },
        {
            "name": "limit",
            "in": "query",
            "schema": {"type": "integer"},
            "example": 10
        }
    ]
}

curl = generator.generate_curl("/users", "GET", get_spec)
# Output: curl -X GET https://api.example.com/users?page=1&limit=10
```

### Path Parameters

Path parameters are automatically replaced with example values:

```python
spec = {
    "parameters": [
        {
            "name": "userId",
            "in": "path",
            "schema": {"type": "string"},
            "example": "12345"
        }
    ]
}

curl = generator.generate_curl("/users/{userId}", "GET", spec)
# Output: curl -X GET https://api.example.com/users/12345
```

### Custom Header Parameters

```python
spec = {
    "parameters": [
        {
            "name": "X-Request-ID",
            "in": "header",
            "schema": {"type": "string"},
            "example": "abc-123"
        }
    ]
}
```

### Complex Request Bodies

The module supports complex nested schemas:

```python
spec = {
    "requestBody": {
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "user": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "address": {
                                    "type": "object",
                                    "properties": {
                                        "street": {"type": "string"},
                                        "city": {"type": "string"}
                                    }
                                }
                            }
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                }
            }
        }
    }
}
```

### Update Base URL

```python
generator.set_base_url("https://api.staging.example.com")
```

## Schema Type Support

The module automatically generates appropriate example values for:

- `string` - "string"
- `integer` - 1
- `number` - 1.0
- `boolean` - true
- `array` - [item]
- `object` - {key: value}

### Format Support

- `email` - "user@example.com"
- `date` - "2024-01-01"
- `date-time` - "2024-01-01T00:00:00Z"
- `uuid` - "550e8400-e29b-41d4-a716-446655440000"

## Error Handling

The module gracefully handles errors and provides informative error messages:

```python
all_examples = generator.generate_all_examples(openapi_spec)

# If generation fails for an operation, error messages are included:
# {
#   "/path": {
#     "method": {
#       "curl": "# Error generating example: <error message>",
#       "python": "# Error generating example: <error message>",
#       "javascript": "// Error generating example: <error message>"
#     }
#   }
# }
```

## Logging

The module uses `structlog` for structured logging:

```python
import structlog

# Configure logging as needed
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ]
)
```

## Complete Example

```python
from example_generator import ExampleGenerator

# Initialize
generator = ExampleGenerator(base_url="https://api.myservice.com")

# Define OpenAPI spec
spec = {
    "paths": {
        "/products/{id}": {
            "get": {
                "parameters": [
                    {"name": "id", "in": "path", "schema": {"type": "string"}}
                ]
            },
            "put": {
                "parameters": [
                    {"name": "id", "in": "path", "schema": {"type": "string"}}
                ],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "price": {"type": "number"}
                                },
                                "required": ["name", "price"]
                            }
                        }
                    }
                }
            }
        }
    }
}

# Generate all examples
auth = {"type": "bearer", "token": "SECRET_TOKEN"}
examples = generator.generate_all_examples(spec, auth=auth)

# Use examples in documentation
for path, methods in examples.items():
    print(f"\n## Endpoint: {path}")
    for method, language_examples in methods.items():
        print(f"\n### {method.upper()}")
        for language, code in language_examples.items():
            print(f"\n#### {language.upper()}")
            print(f"```{language}")
            print(code)
            print("```")
```

## Integration with Documentation Generators

The module is designed to integrate seamlessly with documentation generators:

```python
# Generate examples for Swagger UI
swagger_examples = {}
for path, methods in examples.items():
    swagger_examples[path] = {}
    for method, lang_examples in methods.items():
        swagger_examples[path][method] = {
            "x-code-samples": [
                {"lang": "Shell", "source": lang_examples["curl"]},
                {"lang": "Python", "source": lang_examples["python"]},
                {"lang": "JavaScript", "source": lang_examples["javascript"]}
            ]
        }
```

## Best Practices

1. **Provide Explicit Examples**: Include `example` fields in your OpenAPI spec for better-looking examples
2. **Use Descriptive Names**: Parameter names affect generated example values
3. **Required Fields**: Only required fields are included by default in request bodies
4. **Authentication**: Always provide auth configuration for protected endpoints
5. **Base URL**: Set the correct base URL for your environment (dev, staging, prod)

## Troubleshooting

### Examples Look Generic

Add explicit `example` fields to your OpenAPI schema:

```python
{
    "properties": {
        "name": {
            "type": "string",
            "example": "John Doe"  # Add this
        }
    }
}
```

### Path Parameters Not Replaced

Ensure path parameters are defined in the `parameters` array:

```python
{
    "parameters": [
        {
            "name": "id",
            "in": "path",  # Must be "path"
            "schema": {"type": "string"}
        }
    ]
}
```

### Authentication Headers Missing

Verify auth configuration is passed correctly:

```python
auth = {"type": "bearer", "token": "YOUR_TOKEN"}
generator.generate_curl(path, method, spec, auth=auth)  # Pass auth
```
