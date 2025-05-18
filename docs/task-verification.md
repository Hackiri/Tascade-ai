# Task Verification

Tascade AI includes a comprehensive task verification system that helps ensure tasks are completed correctly and thoroughly.

## Overview

The verification system:
- Generates criteria based on task complexity
- Uses a scoring system to evaluate task completion
- Categorizes criteria by type (functionality, quality, etc.)
- Distinguishes between required and optional criteria
- Provides an overall verification score

## Using Task Verification

### Verify a Task

```bash
tascade-ai verify --task <task-id> --interactive
```

This command will:
1. Generate verification criteria based on task complexity
2. Prompt you to confirm satisfaction for each criterion
3. Calculate a verification score
4. Determine if the task can be marked as complete

### Generate Verification Criteria

```bash
tascade-ai complexity --verify <task-id>
```

This command generates verification criteria without starting the verification process, allowing you to review what will be checked.

## Verification Criteria Types

Criteria are categorized by type:

- **Functionality**: Does the implementation work as expected?
- **Quality**: Does the implementation meet quality standards?
- **Performance**: Does the implementation perform efficiently?
- **Documentation**: Is the implementation well-documented?
- **Testing**: Has the implementation been properly tested?

## Required vs. Optional Criteria

Criteria are marked as either:

- **Required**: Must be satisfied for the task to be considered complete
- **Optional**: Enhances the implementation but not strictly necessary

## Verification Scoring

The verification system uses a scoring mechanism:
- Each criterion has a weight based on importance
- Required criteria have higher weights than optional ones
- A minimum score threshold must be met for task completion
- The threshold varies based on task complexity

## Example Verification Session

```
Verifying Task #123: Implement user authentication
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Functionality Criteria:
[REQUIRED] User can register with email and password ✓
[REQUIRED] User can log in with correct credentials ✓
[REQUIRED] User is redirected after successful login ✓
[OPTIONAL] Password reset functionality works ✗

Quality Criteria:
[REQUIRED] Input validation is implemented ✓
[REQUIRED] Error messages are clear and helpful ✓
[OPTIONAL] Form fields have proper accessibility attributes ✓

Testing Criteria:
[REQUIRED] Unit tests cover authentication logic ✓
[OPTIONAL] Integration tests for the login flow ✗

Verification Score: 85/100 (PASS)
Task can be marked as complete.
```

## Integration with Other Features

The verification system is integrated with:
- **Task Complexity**: More complex tasks have more verification criteria
- **Task Execution**: Verification can be triggered after execution
- **Task Splitting**: Subtasks inherit relevant verification criteria
