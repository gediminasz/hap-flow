#!/usr/bin/env xonsh

print("Workflow name:", $WORKFLOW_NAME)

now = $(date)
print(f"Current date and time is {now}")
