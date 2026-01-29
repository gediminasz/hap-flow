# hap-flow

Workflow system based on hapless

## Environment Variables

### HAP_FLOW_PROJECT_DIR

When workflow tasks are executed, they have access to the `HAP_FLOW_PROJECT_DIR` environment variable. This variable contains the absolute path to the directory where the `hap-flow` command was invoked (the project root).

This allows tasks to reference files relative to the project root, regardless of their working directory.

**Example:**

```bash
#!/usr/bin/env bash

# Read a configuration file from the project root
cat "${HAP_FLOW_PROJECT_DIR}/config.yaml"

# Access data files relative to the project
python "${HAP_FLOW_PROJECT_DIR}/scripts/process.py" \
    --input "${HAP_FLOW_PROJECT_DIR}/data/input.csv"
```

