# Task Analysis Prompt

## Task Information
- **Title**: ${title}
- **Description**: ${description}
- **Status**: ${status}
- **Priority**: ${priority}
- **Dependencies**: ${dependencies}

## Analysis Instructions
Analyze the above task and provide the following:

1. **Complexity Assessment**: Rate the complexity on a scale of 1-10 and explain your reasoning.
2. **Effort Estimation**: Estimate the effort required in hours.
3. **Key Considerations**: List important factors to consider when implementing this task.
4. **Potential Challenges**: Identify potential challenges or blockers.
5. **Recommendations**: Provide actionable recommendations for completing this task efficiently.

## Response Format
Format your response as a JSON object with the following structure:
```json
{
  "complexity_score": <number 1-10>,
  "estimated_effort_hours": <number>,
  "factors": {
    "<factor_name>": <value>,
    ...
  },
  "challenges": [
    "<challenge_description>",
    ...
  ],
  "recommendations": [
    "<recommendation>",
    ...
  ]
}
```

Be thorough but concise in your analysis. Focus on practical insights that will help the developer complete the task efficiently.
