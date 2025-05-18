# Task Decomposition Prompt

## Parent Task Information
- **Title**: ${title}
- **Description**: ${description}
- **Priority**: ${priority}

## Project Rules
${project_rules}

## Custom Instructions
${custom_instructions}

## Decomposition Instructions
Break down the parent task into smaller, actionable subtasks. For each subtask:

1. Create a clear, concise title
2. Provide a detailed description
3. Identify dependencies between subtasks (if any)
4. Estimate the effort required for each subtask

## Response Format
Format your response as a JSON array of subtask objects:
```json
[
  {
    "title": "<subtask_title>",
    "description": "<detailed_description>",
    "dependencies": [<subtask_numbers>],
    "estimated_effort_hours": <number>
  },
  ...
]
```

Guidelines:
- Each subtask should be focused on a single objective
- Subtasks should be roughly equal in size when possible
- Include all necessary steps to complete the parent task
- Consider the project rules in your decomposition
- Number subtasks starting from 1
- Dependencies should reference subtask numbers (e.g., [1, 3] means this subtask depends on subtasks 1 and 3)
