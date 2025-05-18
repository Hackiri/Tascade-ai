# Task Complexity Assessment

Tascade AI includes a sophisticated task complexity assessment system that helps you understand and manage complex tasks more effectively.

## Overview

The complexity assessment evaluates multiple metrics to provide a comprehensive view of task complexity:

- **Description Length**: Longer descriptions often indicate more complex tasks
- **Subtasks Count**: Tasks with many subtasks are typically more complex
- **Dependencies**: Tasks with many dependencies are harder to manage
- **Notes and Implementation Guides**: Detailed notes may indicate complexity
- **Verification Criteria**: More verification points suggest higher complexity

## Using Complexity Assessment

### Analyze Task Complexity

```bash
tascade-ai complexity --analyze <task-id>
```

This command will:
1. Evaluate the task based on multiple metrics
2. Display a complexity score (0-100)
3. Provide a complexity level (Low, Medium, High, Very High)
4. Show visual indicators for each complexity factor
5. Offer recommendations based on the complexity level

### View Project Complexity Metrics

```bash
tascade-ai complexity --metrics --detailed
```

This command displays:
- Distribution of task complexity across your project
- Average complexity score
- Breakdown by complexity level
- Recommendations for managing project complexity

## Visual Indicators

Tascade AI uses color-coded indicators to represent complexity:
- **Green**: Low complexity (0-25)
- **Blue**: Medium complexity (26-50)
- **Yellow**: High complexity (51-75)
- **Red**: Very High complexity (76-100)

## Recommendations

Based on complexity level, Tascade AI provides recommendations:

- **Low Complexity**: Direct execution, minimal planning needed
- **Medium Complexity**: Consider breaking into 2-3 subtasks
- **High Complexity**: Break into 3-5 subtasks, create implementation guide
- **Very High Complexity**: Break into 5+ subtasks, create detailed plan, consider team collaboration

## Integration with Other Features

The complexity assessment is integrated with:
- **Task Splitting**: Suggests how to split complex tasks
- **Task Execution**: Checks complexity before execution
- **Task Verification**: Generates criteria based on complexity

## Example Output

```
Task Complexity Analysis for Task #123:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Complexity Score: 78/100 (Very High)

Factors:
[██████████] Description Length: 85%
[████████  ] Subtasks Count: 70%
[███████   ] Dependencies: 65%
[████████  ] Notes & Guides: 75%
[███████████] Verification Criteria: 95%

Recommendation:
This task is very complex. Consider breaking it into 5+ subtasks,
creating a detailed implementation guide, and collaborating with team members.
```
