# CLI Enhancements

This document describes the CLI improvements implemented for FileFlow Manager, addressing items from the polish checklist (CHK054-061).

## Overview

The enhanced CLI provides:
- **TTY detection** for appropriate output formatting
- **Pagination** for long outputs
- **Standardized JSON output** for scripting
- **Consistent error handling** with exit codes
- **Better pipe/redirect support**
- **Interactive confirmations** with fallbacks

## Architecture

### Core Modules

**`output.py`** - Output utilities:
- `ExitCode` - Standard exit codes (CHK058)
- `OutputFormat` - TTY-aware output (CHK054)
- `JSONOutput` - Standardized JSON responses (CHK060)
- `Paginator` - Automatic pagination (CHK056)
- Helper functions for formatting

**`enhanced_commands.py`** - Example enhanced commands:
- Demonstrates best practices
- Shows pagination, JSON output, TTY handling
- Examples for future command updates

## Features

### 1. TTY Detection (CHK054)

Automatically detects if output is piped or redirected:

```python
from fileflow_cli.output import OutputFormat

out = OutputFormat()

if out.is_tty:
    # Terminal - use colors and interactive features
    out.print("[green]Success![/green]")
else:
    # Piped - use plain text
    out.print_plain("Success!")
```

**Behavior**:
- **Terminal**: Colored output, rich formatting, interactive prompts
- **Piped**: Plain text, no colors, no prompts, compact JSON

**Examples**:
```bash
# Terminal - shows colors
fileflow rules list

# Piped - plain text
fileflow rules list | grep screenshot

# JSON for scripts
fileflow rules list --output json | jq '.data[0].name'
```

### 2. Pagination (CHK056)

Automatic pagination for long outputs:

```python
from fileflow_cli.output import Paginator

paginator = Paginator(items, auto_detect=True)

# Auto-detects terminal height
if paginator.should_paginate():
    page_items = paginator.get_page(page_num)
else:
    page_items = paginator.get_all()
```

**Features**:
- Auto-detects terminal height
- Shows "Page X of Y" footer
- Suggests next page command
- Disabled when output is piped

**Examples**:
```bash
# View first page (auto-sized to terminal)
fileflow history

# View specific page
fileflow history --page 2

# Disable pagination
fileflow history --no-pagination

# Piped output ignores pagination
fileflow history | wc -l
```

### 3. JSON Output (CHK060)

Standardized JSON format for all commands:

```python
from fileflow_cli.output import JSONOutput, ExitCode

# Success response
JSONOutput.print(
    JSONOutput.success(
        data=results,
        message="Operation completed",
        metadata={"total": len(results)}
    )
)

# Error response
JSONOutput.print(
    JSONOutput.error(
        error="Configuration not found",
        code=ExitCode.CONFIG_ERROR,
        details={"path": str(config_path)}
    )
)
```

**Success Response Format**:
```json
{
  "success": true,
  "data": [...],
  "message": "Optional success message",
  "metadata": {
    "total_items": 42,
    "filters_applied": true
  }
}
```

**Error Response Format**:
```json
{
  "success": false,
  "error": "Error message",
  "error_code": 3,
  "error_name": "CONFIG_ERROR",
  "details": {
    "config_path": "/path/to/config.toml"
  }
}
```

**Examples**:
```bash
# JSON output
fileflow rules list --output json

# Pipe to jq
fileflow rules list --output json | jq '.data[] | select(.enabled)'

# Check for errors
fileflow scan --output json && echo "Success" || echo "Failed"
```

### 4. Exit Codes (CHK058)

Standardized exit codes for all commands:

```python
from fileflow_cli.output import ExitCode

# Success
sys.exit(ExitCode.SUCCESS)  # 0

# Errors with specific codes
sys.exit(ExitCode.CONFIG_ERROR)  # 3
sys.exit(ExitCode.FILE_NOT_FOUND)  # 4
sys.exit(ExitCode.PERMISSION_ERROR)  # 5
```

**Exit Code Reference**:
| Code | Name | Description |
|------|------|-------------|
| 0 | SUCCESS | Command completed successfully |
| 1 | GENERAL_ERROR | General error |
| 2 | INVALID_USAGE | Invalid command usage |
| 3 | CONFIG_ERROR | Configuration error |
| 4 | FILE_NOT_FOUND | File not found |
| 5 | PERMISSION_ERROR | Permission denied |
| 6 | DATABASE_ERROR | Database error |
| 7 | OPERATION_CANCELLED | Operation cancelled by user |

**Usage in Scripts**:
```bash
#!/bin/bash

fileflow scan
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "Scan successful"
elif [ $EXIT_CODE -eq 3 ]; then
    echo "Configuration error - check config file"
elif [ $EXIT_CODE -eq 5 ]; then
    echo "Permission error - check file permissions"
else
    echo "Scan failed with code $EXIT_CODE"
fi
```

### 5. Stdin/Pipe Handling (CHK055)

Commands adapt to redirected stdin:

```python
from fileflow_cli.output import confirm_action

# Automatically handles both cases
if confirm_action("Delete files?", default=False):
    delete_files()
```

**Behavior**:
- **Interactive terminal**: Shows confirmation prompt
- **Redirected stdin**: Uses default value (no prompt)

**Examples**:
```bash
# Interactive - prompts for confirmation
fileflow files duplicates --interactive

# Piped - uses defaults (no prompts)
echo "y" | fileflow files duplicates --auto-delete

# Batch mode
fileflow files duplicates --auto-delete < /dev/null
```

### 6. No Duplicates Found (CHK057)

Handles empty results gracefully:

```python
if not duplicates:
    if output_format == "json":
        JSONOutput.print(
            JSONOutput.success(
                data=[],
                message="No duplicate files found",
                metadata={"files_scanned": total_files}
            )
        )
    else:
        out.print("[green]✓ No duplicate files found[/green]")
        out.print("Your file system is clean!")
    sys.exit(ExitCode.SUCCESS)
```

**Examples**:
```bash
# Terminal - friendly message
$ fileflow files duplicates
✓ No duplicate files found
Your file system is clean!

# JSON - structured response
$ fileflow files duplicates --output json
{
  "success": true,
  "data": [],
  "message": "No duplicate files found",
  "metadata": {
    "files_scanned": 1523
  }
}
```

## Usage Patterns

### Basic Command Structure

```python
def my_command(
    # Filtering options
    filter: Optional[str] = None,

    # Pagination options
    limit: int = 50,
    page: int = 1,
    no_pagination: bool = False,

    # Output options
    output_format: str = "table",
) -> None:
    """
    Command description.

    Examples:
        # Basic usage
        fileflow my-command

        # JSON output
        fileflow my-command --output json

        # Paginated
        fileflow my-command --page 2
    """
    out = OutputFormat()

    try:
        # ... command logic ...

        # Handle output format
        if output_format == "json":
            JSONOutput.print(JSONOutput.success(data=results))
        elif output_format == "simple":
            for item in results:
                print(item)
        else:
            # Table with pagination
            paginator = Paginator(results)
            # ... display table ...

        sys.exit(ExitCode.SUCCESS)

    except Exception as e:
        if output_format == "json":
            JSONOutput.print(
                JSONOutput.error(str(e), code=ExitCode.GENERAL_ERROR)
            )
        else:
            out.print(f"[red]Error: {e}[/red]")
        sys.exit(ExitCode.GENERAL_ERROR)
```

### Output Format Best Practices

1. **Always provide JSON option** for scriptability:
   ```python
   --output/--format json|table|simple
   ```

2. **Use TTY detection** for colored output:
   ```python
   out = OutputFormat()
   if out.should_use_color:
       # Use rich formatting
   else:
       # Use plain text
   ```

3. **Paginate long results** in interactive mode:
   ```python
   if out.should_paginate and not no_pagination:
       # Show paginated output
   ```

4. **Handle empty results** gracefully:
   ```python
   if not results:
       # Friendly message, not error
       sys.exit(ExitCode.SUCCESS)
   ```

5. **Provide examples** in help text:
   ```python
   """
   Examples:
       # Basic usage
       fileflow command

       # With options
       fileflow command --option value
   """
   ```

## Migration Guide

### Updating Existing Commands

1. **Import utilities**:
   ```python
   from fileflow_cli.output import (
       ExitCode,
       JSONOutput,
       OutputFormat,
       Paginator,
   )
   ```

2. **Add output format option**:
   ```python
   output_format: str = "table"
   ```

3. **Replace console with OutputFormat**:
   ```python
   # Old:
   console.print("[green]Success[/green]")

   # New:
   out = OutputFormat()
   out.print("[green]Success[/green]")
   ```

4. **Add JSON output support**:
   ```python
   if output_format == "json":
       JSONOutput.print(JSONOutput.success(data=results))
       sys.exit(ExitCode.SUCCESS)
   ```

5. **Add pagination for lists**:
   ```python
   paginator = Paginator(items, auto_detect=True)
   if paginator.should_paginate():
       page_items = paginator.get_page(page)
   ```

6. **Use consistent exit codes**:
   ```python
   sys.exit(ExitCode.SUCCESS)
   sys.exit(ExitCode.CONFIG_ERROR)
   ```

## Testing

### Test TTY Behavior

```bash
# Test colored output (terminal)
fileflow rules list

# Test plain output (piped)
fileflow rules list | cat

# Test JSON output
fileflow rules list --output json > rules.json
```

### Test Pagination

```bash
# Create many rules to test pagination
for i in {1..100}; do
    fileflow rules create --name "Rule $i" --priority $i
done

# Test pagination
fileflow rules list  # Should show first page
fileflow rules list --page 2  # Should show second page
fileflow rules list --no-pagination  # Should show all
```

### Test Exit Codes

```bash
# Test success
fileflow scan && echo "Success" || echo "Failed"

# Test error handling
fileflow rules show nonexistent || echo "Exit code: $?"

# Test with invalid config
mv ~/.config/fileflow/fileflow.toml ~/.config/fileflow/fileflow.toml.bak
fileflow scan || echo "Config error: $?"
mv ~/.config/fileflow/fileflow.toml.bak ~/.config/fileflow/fileflow.toml
```

### Test JSON Output

```bash
# Test valid JSON
fileflow rules list --output json | jq '.'

# Test error JSON
fileflow rules show nonexistent --output json | jq '.error'

# Test filtering with jq
fileflow rules list --output json | jq '.data[] | select(.enabled)'
```

## Future Improvements

- [ ] Add `--verbose` and `--quiet` flags
- [ ] Support `--color=auto|always|never` option
- [ ] Add CSV output format
- [ ] Implement `--watch` mode for continuous monitoring
- [ ] Add progress bars for long operations
- [ ] Support custom output templates

## References

- **CHK054**: TTY detection for piped output
- **CHK055**: Stdin redirection handling
- **CHK056**: Pagination for long outputs
- **CHK057**: Empty results handling
- **CHK058**: Consistent exit codes
- **CHK059**: Help text formatting (see examples in commands)
- **CHK060**: Standardized JSON output
- **CHK061**: Kebab-case command names (already implemented)
