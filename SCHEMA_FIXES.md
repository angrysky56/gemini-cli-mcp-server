# Gemini CLI MCP Server - Schema Compatibility Fixes

## Overview

This document outlines the fixes applied to ensure compatibility with Gemini CLI's tool schema requirements. The Gemini CLI has specific requirements for MCP tool schemas that need to be followed for proper integration.

## Key Issues Fixed

### 1. Schema Property Compatibility

**Problem**: Gemini CLI automatically strips certain schema properties for API compatibility.

**Solution**: 
- Added explicit `additionalProperties: false` to all tool schemas
- Ensured all optional parameters have proper default values
- Removed any problematic schema constructs that might be stripped

### 2. Parameter Validation

**Problem**: Missing or improper parameter validation was causing tool execution failures.

**Solution**:
- Added comprehensive parameter validation for all tools
- Implemented proper type checking for all input parameters
- Added existence checks for file/directory parameters
- Improved error messages with specific parameter names

### 3. Required vs Optional Parameters

**Problem**: Schema definitions weren't clearly distinguishing required from optional parameters.

**Solution**:
- Explicitly defined `required` arrays with only truly required parameters
- Added default values for optional parameters
- Proper handling of missing optional parameters

### 4. Error Handling

**Problem**: Generic error handling made debugging difficult.

**Solution**:
- Added specific error types (KeyError, ValueError)
- Improved error messages with parameter names
- Added validation for parameter types and values
- Better exception handling hierarchy

## Specific Changes Made

### Tool Schema Updates

Each tool now has:
```python
inputSchema={
    "type": "object",
    "properties": {
        # ... property definitions with descriptions and types
    },
    "required": ["only_truly_required_params"],
    "additionalProperties": False  # Explicit for compatibility
}
```

### Parameter Validation

All tool execution methods now include:
- Parameter existence validation
- Type validation
- Value validation (non-empty strings, existing paths)
- Proper default value handling

### Dependencies

- Added proper import handling for `aiohttp`
- Graceful degradation when optional dependencies are missing
- Better error messages for missing dependencies

## Testing the Fixes

To test that the fixes work:

1. **Schema Validation**: The tools should now properly register with Gemini CLI without schema validation errors
2. **Parameter Handling**: All required parameters are properly validated
3. **Error Messages**: Clear, specific error messages when parameters are invalid
4. **Optional Parameters**: Default values work correctly for optional parameters

## Future Maintenance

When adding new tools:

1. Always include `additionalProperties: false` in schemas
2. Only include truly required parameters in the `required` array
3. Provide default values for optional parameters
4. Implement comprehensive parameter validation
5. Use specific error types (KeyError, ValueError) for better debugging

## Dependencies

Ensure these dependencies are available:

```bash
pip install aiohttp  # For HTTP requests in gemini_list_models
```

## Compatibility Notes

These fixes ensure compatibility with:
- Gemini CLI schema sanitization
- Vertex AI parameter requirements
- MCP protocol standards
- JSON Schema validation

The server now properly handles all the automatic transformations that Gemini CLI performs on MCP tool schemas.
