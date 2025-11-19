# P-TEMPLATE-VALIDATION: Artifact Template Validation Protocol

## Metadata
- **Protocol ID**: P-TEMPLATE-VALIDATION
- **Category**: System
- **Version**: 1.0
- **Last Updated**: 2025-11-19
- **Applicable Agents**: All agents that create artifacts with template parameters

## Objective

Ensure all artifact templates include required parameters before creation, preventing downstream agent failures caused by missing or invalid parameters. This protocol provides a standardized validation framework for enforcing parameter requirements across all DevGru agents.

## Trigger

Execute this protocol **before creating any artifact** that uses template parameters, including:
- Artifact files (JSON, YAML, Markdown, CSV, etc.)
- Protocol executions that require specific parameters
- Agent delegation requests with parameter dependencies
- Handoff documents between agents

## Prerequisites

- Agent specification Part VII defines required and optional parameters for each artifact
- Parameter Registry (`/docs/specifications/parameter_registry.md`) documents system-wide parameters
- Schema definitions exist for artifacts (see `/docs/schemas/`)

## Steps

### Step 1: Parameter Declaration Review

**Objective**: Verify artifact specification declares parameter requirements

**Actions**:
1. Locate artifact definition in agent specification Part VII
2. Identify declared required parameters
3. Identify declared optional parameters
4. Note any parameter format constraints (patterns, types, ranges)

**Example Part VII Declaration**:
```markdown
#### feature_performance_{{feature_id}}.json
**Schema**: feature_performance_schema:1.0
**Required Parameters**:
- `{{feature_id}}`: Unique feature identifier (pattern: FT-[A-Z0-9]+)
- `{{issue_number}}`: GitHub issue number (positive integer)
- `{{created_timestamp}}`: ISO 8601 creation timestamp

**Optional Parameters**:
- `{{stakeholder_id}}`: Associated stakeholder (pattern: STK-[A-Z0-9]+)
- `{{tags}}`: Comma-separated feature tags
```

**Output**: List of required and optional parameters for validation

---

### Step 2: Required Parameter Validation

**Objective**: Ensure all required parameters are present and not null/empty

**Actions**:
1. For each required parameter in declaration:
   - Check if parameter value exists
   - Verify value is not null, undefined, or empty string
   - Verify value is not a placeholder (e.g., "TBD", "TODO", "MISSING")

2. If any required parameter is missing:
   - Log error with missing parameter name(s)
   - Identify source of parameter (GH-1, upstream agent, delegation request)
   - **HALT artifact creation**

**Validation Logic** (pseudocode):
```python
def validate_required_params(artifact_name, required_params, param_values):
    missing = []
    for param in required_params:
        if param not in param_values or not param_values[param]:
            missing.append(param)
        if param_values[param] in ["TBD", "TODO", "MISSING", ""]:
            missing.append(param)

    if missing:
        raise ValidationError(f"Missing required parameters for {artifact_name}: {missing}")

    return True
```

**Error Handling**:
- **Error Message Format**: `"Validation failed for {artifact_name}: Missing required parameters {param_list}"`
- **Action**: Do NOT create artifact, return error to calling agent/protocol
- **Recovery**: Request missing parameters from upstream source (GH-1, delegating agent, ProductOwner)

**Output**:
- ✅ Success: All required parameters present
- ❌ Failure: Validation error with specific missing parameters

---

### Step 3: Parameter Format Validation

**Objective**: Validate parameter values match expected types and patterns

**Actions**:
1. For each parameter (required and optional if present):
   - Validate type (integer, string, timestamp, etc.)
   - Validate format/pattern if specified
   - Validate value constraints (ranges, enums, etc.)

2. If format validation fails:
   - Log error with parameter name and expected format
   - Include actual value received (for debugging)
   - **HALT artifact creation**

**Common Parameter Validations**:

| Parameter | Type | Pattern/Constraint | Validation |
|-----------|------|-------------------|------------|
| `{{issue_number}}` | integer | `^[1-9][0-9]*$` | Positive integer, no leading zeros |
| `{{feature_id}}` | string | `^FT-[A-Z0-9]+$` | Feature ID format |
| `{{stakeholder_id}}` | string | `^STK-[A-Z0-9]+$` | Stakeholder ID format |
| `{{delegation_id}}` | integer | `^[1-9][0-9]*$` | Positive integer, no leading zeros |
| `{{timestamp}}` | string | ISO 8601 | Valid datetime format |
| `{{priority}}` | integer | `[1-4]` | Value between 1-4 |
| `{{quarter}}` | string | `^Q[1-4]-\d{4}$` | Format: Q1-2024 |

**Validation Logic** (pseudocode):
```python
import re
from datetime import datetime

def validate_param_format(param_name, param_value, param_spec):
    # Type validation
    if param_spec.type == "integer" and not isinstance(param_value, int):
        raise ValidationError(f"{param_name} must be integer, got {type(param_value)}")

    # Pattern validation
    if param_spec.pattern and not re.match(param_spec.pattern, str(param_value)):
        raise ValidationError(f"{param_name} does not match pattern {param_spec.pattern}: {param_value}")

    # Range validation
    if param_spec.minimum and param_value < param_spec.minimum:
        raise ValidationError(f"{param_name} below minimum {param_spec.minimum}: {param_value}")

    if param_spec.maximum and param_value > param_spec.maximum:
        raise ValidationError(f"{param_name} above maximum {param_spec.maximum}: {param_value}")

    return True
```

**Error Handling**:
- **Error Message Format**: `"Format validation failed for {param_name}: Expected {pattern}, got {value}"`
- **Action**: Do NOT create artifact, return error with expected format
- **Recovery**: Request correctly formatted parameter from source

**Output**:
- ✅ Success: All parameters match expected formats
- ❌ Failure: Format validation error with specific parameter and expected format

---

### Step 4: Schema Validation (If Applicable)

**Objective**: Validate complete artifact structure against JSON Schema

**Actions**:
1. If artifact has centralized schema (see `/docs/schemas/`):
   - Load schema definition from schema registry
   - Construct artifact data structure with parameter values
   - Validate artifact against schema using JSON Schema validator

2. If schema validation fails:
   - Log detailed validation errors (missing fields, type mismatches, constraint violations)
   - **HALT artifact creation**

**Schema Validation Logic** (pseudocode):
```python
import jsonschema

def validate_against_schema(artifact_data, schema_path):
    with open(schema_path) as f:
        schema = json.load(f)

    try:
        jsonschema.validate(artifact_data, schema)
        return True
    except jsonschema.ValidationError as e:
        raise ValidationError(f"Schema validation failed: {e.message}")
```

**Error Handling**:
- **Error Message Format**: `"Schema validation failed for {artifact_name}: {validation_errors}"`
- **Action**: Do NOT create artifact, return detailed schema errors
- **Recovery**: Fix artifact structure or parameter values to match schema

**Output**:
- ✅ Success: Artifact validates against schema
- ❌ Failure: Schema validation error with detailed mismatch information

---

### Step 5: Parameter Availability Check

**Objective**: Verify parameters are available from correct sources

**Actions**:
1. Identify expected source for each parameter:
   - `{{issue_number}}`: From GH-1 protocol execution
   - `{{feature_id}}`: Generated by ProductOwner or provided in delegation
   - `{{delegation_id}}`: From P-DELEGATION-DEFAULT parent issue
   - `{{stakeholder_id}}`: From stakeholder registry or delegation request

2. If parameter unavailable from expected source:
   - Log warning about missing parameter source
   - Check if parameter can be obtained from alternative source
   - If no valid source exists: **HALT and request parameter**

**Parameter Propagation Rules**:

| Parameter | Primary Source | Propagation Path | Fallback |
|-----------|---------------|------------------|----------|
| `{{issue_number}}` | GH-1 protocol | All child workflows | None - must exist |
| `{{feature_id}}` | ProductOwner generation | Delegation request | Error if missing |
| `{{delegation_id}}` | P-DELEGATION-DEFAULT | Delegated agent context | Parent issue number |
| `{{stakeholder_id}}` | Stakeholder registry | Delegation/handoff | Optional in most cases |

**Error Handling**:
- **Error Message Format**: `"Parameter {param_name} unavailable from expected source {source}"`
- **Action**: Request parameter from upstream agent or halt workflow
- **Recovery**: Execute upstream protocol (e.g., GH-1) or request delegation parameter

**Output**:
- ✅ Success: All parameters available from valid sources
- ❌ Failure: Parameter unavailable, workflow halted pending upstream input

---

### Step 6: Validation Success - Proceed with Artifact Creation

**Objective**: Create artifact with validated parameters

**Actions**:
1. All validation checks passed
2. Substitute parameter values into artifact template
3. Create artifact file with validated content
4. Log successful validation and artifact creation

**Success Log Format**:
```
✅ P-TEMPLATE-VALIDATION: SUCCESS
Artifact: {artifact_name}
Required Parameters: {param_list}
Optional Parameters: {param_list}
Schema: {schema_name}:{version}
Created: {timestamp}
```

**Output**: Validated artifact created successfully

---

## Outputs

### Success Case
- ✅ **Validated Artifact**: Artifact file created with all required parameters
- **Validation Log**: Record of successful parameter validation
- **Artifact Metadata**: Schema reference, parameter values, creation timestamp

### Failure Cases

#### Missing Required Parameter
```
❌ P-TEMPLATE-VALIDATION: FAILURE
Artifact: feature_performance_FT-001.json
Error: Missing required parameters: {{feature_id}}
Required: {{feature_id}}, {{issue_number}}, {{created_timestamp}}
Provided: {{issue_number}}=123, {{created_timestamp}}=2025-10-16T10:00:00Z
Action: Request {{feature_id}} from ProductOwner or upstream delegation
```

#### Invalid Parameter Format
```
❌ P-TEMPLATE-VALIDATION: FAILURE
Artifact: stakeholder_profile_STK-001.yaml
Error: Format validation failed for {{stakeholder_id}}
Expected: ^STK-[A-Z0-9]+$
Received: "stakeholder_001"
Action: Use correct format: STK-001
```

#### Schema Validation Failure
```
❌ P-TEMPLATE-VALIDATION: FAILURE
Artifact: rice_scoring_Q1-2025.json
Error: Schema validation failed
Details:
  - Missing required field: "confidence"
  - Invalid type for "reach.value": expected integer, got string
Schema: rice_scoring_schema:1.0
Action: Fix artifact structure to match schema
```

---

## Error Handling and Recovery

### Recovery Strategies by Error Type

1. **Missing Required Parameter**:
   - **Cause**: Parameter not provided by upstream source
   - **Recovery**:
     - If from GH-1: Re-execute `gh issue view {{issue_number}}`
     - If from delegation: Comment on delegation issue requesting parameter
     - If generated (e.g., feature_id): Request ProductOwner to generate ID

2. **Invalid Format**:
   - **Cause**: Parameter value doesn't match expected pattern
   - **Recovery**:
     - Transform value to correct format if possible (e.g., add prefix)
     - Request correction from source if transformation not safe
     - Document correct format in error message for manual fix

3. **Schema Mismatch**:
   - **Cause**: Artifact structure doesn't match schema definition
   - **Recovery**:
     - Review schema at `/docs/schemas/{category}/{schema}_v{version}.json`
     - Add missing required fields
     - Correct field types/formats
     - Re-validate against schema

4. **Parameter Unavailable**:
   - **Cause**: Expected parameter source doesn't exist or is inaccessible
   - **Recovery**:
     - Check if alternative source exists (e.g., parent issue metadata)
     - If optional parameter: Omit and continue
     - If required parameter: Escalate to delegating agent or ProductOwner

---

## Integration with Existing Protocols

### GH-1 Protocol
P-TEMPLATE-VALIDATION depends on GH-1 providing `{{issue_number}}` as the primary workflow identifier. All artifacts requiring `{{issue_number}}` must execute GH-1 first.

### P-DELEGATION-DEFAULT
When delegating tasks, delegating agent MUST provide all required parameters for delegated agent's artifacts. P-TEMPLATE-VALIDATION runs in delegated agent to verify parameter completeness.

**Delegation Parameter Validation**:
```markdown
## Step 1.3: Validate Delegation Parameters
Execute P-TEMPLATE-VALIDATION for delegation issue:
- Required: {{parent_issue}}, {{delegating_agent}}, {{assigned_agent}}
- Optional: {{priority}}, {{tags}}, {{deadline}}
```

### P-TDD Protocol
Before writing tests, validate that `{{issue_number}}` and optional `{{component}}` parameters are available:

```markdown
## Step 2.1: Validate Required Parameters
Execute P-TEMPLATE-VALIDATION:
- Required: {{issue_number}}
- Optional: {{component}}, {{test_tags}}

If validation fails: Halt and request parameters from delegating agent
```

### P-FEATURE-DEV Protocol
Feature development requires `{{feature_id}}` from ProductOwner. Validate before implementation:

```markdown
## Step 1: Feature Context Analysis
Execute P-TEMPLATE-VALIDATION:
- Required: {{issue_number}}, {{feature_id}}
- Optional: {{stakeholder_ids}}, {{target_version}}
```

---

## Benefits

✅ **Prevent downstream failures** by catching missing parameters early in workflow
✅ **Clear error messages** that specify exactly which parameters are missing and their expected formats
✅ **Automated validation** reduces manual checks and human error
✅ **Type safety** through schema and format validation
✅ **Protocol robustness** by enforcing parameter propagation rules
✅ **Faster debugging** with detailed validation logs
✅ **Consistency** across all agents through standardized validation
✅ **Self-documenting** workflows with explicit parameter requirements

---

## Examples

### Example 1: Successful Validation

**Context**: BackendEngineer creating test results artifact

```markdown
Artifact: test_results_123.json
Required Parameters: {{issue_number}}
Optional Parameters: {{test_tags}}

Validation Steps:
1. ✅ Parameter declaration found in BackendEngineer Part VII
2. ✅ Required parameter {{issue_number}} = 123 (from GH-1)
3. ✅ Format validation: 123 matches pattern ^[1-9][0-9]*$
4. ✅ Schema validation: artifact structure matches test_results_schema:1.0
5. ✅ Parameter available from GH-1 protocol

Result: ✅ Artifact created successfully
```

### Example 2: Missing Required Parameter

**Context**: ProductOwner creating feature performance artifact

```markdown
Artifact: feature_performance_FT-001.json
Required Parameters: {{feature_id}}, {{issue_number}}
Optional Parameters: {{stakeholder_id}}

Validation Steps:
1. ✅ Parameter declaration found in ProductOwner Part VII
2. ❌ Required parameter {{feature_id}} = MISSING
3. ❌ Required parameter {{issue_number}} = 123

Result: ❌ Validation failed
Error: Missing required parameters: {{feature_id}}
Action: ProductOwner must generate feature_id before creating artifact
Recovery: Execute feature ID generation workflow, then retry validation
```

### Example 3: Invalid Parameter Format

**Context**: SystemArchitect creating ASR documentation

```markdown
Artifact: asr_analysis_123.md
Required Parameters: {{issue_number}}, {{stakeholder_ids}}

Validation Steps:
1. ✅ Parameter declaration found in SystemArchitect Part VII
2. ✅ Required parameter {{issue_number}} = 123
3. ❌ Required parameter {{stakeholder_ids}} = "stakeholder_001,stakeholder_002"

Result: ❌ Format validation failed
Error: {{stakeholder_ids}} values must match pattern ^STK-[A-Z0-9]+$
Received: "stakeholder_001,stakeholder_002"
Expected: "STK-001,STK-002"
Action: Convert stakeholder identifiers to correct format
```

---

## Related Protocols

- **GH-1**: GitHub Issue Triage - Provides `{{issue_number}}` to all workflows
- **P-DELEGATION-DEFAULT**: Agent Delegation - Validates delegation parameters
- **P-TDD**: Test-Driven Development - Validates test artifact parameters
- **P-FEATURE-DEV**: Feature Development - Validates feature parameters
- **P-HANDOFF-***: All handoff protocols - Validates handoff parameters

---

## Related Documentation

- **Schema Registry**: `/docs/schemas/README.md` - Centralized schema definitions
- **Parameter Registry**: `/docs/specifications/parameter_registry.md` - System-wide parameter documentation
- **CONTRIBUTING.md Section 11**: Schema Reference Standards
- **Agent Specification Template**: Part VII Data Contracts format with parameter requirements

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-16 | Initial protocol creation | DevGru Core Team |

---

## Notes

- This protocol is **mandatory** for all artifact creation workflows
- Validation failures MUST halt workflow to prevent cascade failures
- Parameter requirements MUST be documented in agent Part VII specifications
- Schema validation is strongly recommended but optional if no schema exists
- For new artifacts, create schema in `/docs/schemas/` before implementing validation
