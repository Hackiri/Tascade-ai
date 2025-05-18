/**
 * enhanced_task_complexity.js
 * Enhanced task complexity assessment for Tascade AI
 * Based on superior implementations from MCP Shrimp Task Manager
 */

import chalk from 'chalk';

/**
 * Task complexity levels
 */
export const COMPLEXITY_LEVEL = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  VERY_HIGH: 'very_high'
};

/**
 * Thresholds for task complexity metrics
 */
export const COMPLEXITY_THRESHOLDS = {
  DESCRIPTION_LENGTH: {
    MEDIUM: 200,
    HIGH: 500,
    VERY_HIGH: 1000
  },
  SUBTASKS_COUNT: {
    MEDIUM: 3,
    HIGH: 5,
    VERY_HIGH: 8
  },
  DEPENDENCIES_COUNT: {
    MEDIUM: 2,
    HIGH: 4,
    VERY_HIGH: 6
  },
  NOTES_LENGTH: {
    MEDIUM: 100,
    HIGH: 300,
    VERY_HIGH: 600
  },
  IMPLEMENTATION_GUIDE_LENGTH: {
    MEDIUM: 150,
    HIGH: 400,
    VERY_HIGH: 800
  },
  VERIFICATION_CRITERIA_LENGTH: {
    MEDIUM: 100,
    HIGH: 300,
    VERY_HIGH: 500
  }
};

/**
 * Assess task complexity based on multiple metrics
 * @param {Object} task - The task to assess
 * @returns {Object} Complexity assessment
 */
export function assessTaskComplexity(task) {
  // Calculate metrics
  const metrics = {
    descriptionLength: task.description ? task.description.length : 0,
    subtasksCount: task.subtasks ? task.subtasks.length : 0,
    dependenciesCount: task.dependencies ? task.dependencies.length : 0,
    notesLength: task.notes ? task.notes.length : 0,
    hasNotes: !!task.notes,
    implementationGuideLength: task.implementationGuide ? task.implementationGuide.length : 0,
    verificationCriteriaLength: task.verificationCriteria ? task.verificationCriteria.length : 0
  };

  // Determine complexity level for each metric
  let level = COMPLEXITY_LEVEL.LOW;

  // Description length assessment
  if (metrics.descriptionLength >= COMPLEXITY_THRESHOLDS.DESCRIPTION_LENGTH.VERY_HIGH) {
    level = COMPLEXITY_LEVEL.VERY_HIGH;
  } else if (metrics.descriptionLength >= COMPLEXITY_THRESHOLDS.DESCRIPTION_LENGTH.HIGH) {
    level = COMPLEXITY_LEVEL.HIGH;
  } else if (metrics.descriptionLength >= COMPLEXITY_THRESHOLDS.DESCRIPTION_LENGTH.MEDIUM) {
    level = COMPLEXITY_LEVEL.MEDIUM;
  }

  // Subtasks count assessment (take highest level)
  if (metrics.subtasksCount >= COMPLEXITY_THRESHOLDS.SUBTASKS_COUNT.VERY_HIGH) {
    level = COMPLEXITY_LEVEL.VERY_HIGH;
  } else if (metrics.subtasksCount >= COMPLEXITY_THRESHOLDS.SUBTASKS_COUNT.HIGH && 
             level !== COMPLEXITY_LEVEL.VERY_HIGH) {
    level = COMPLEXITY_LEVEL.HIGH;
  } else if (metrics.subtasksCount >= COMPLEXITY_THRESHOLDS.SUBTASKS_COUNT.MEDIUM && 
             level !== COMPLEXITY_LEVEL.HIGH && 
             level !== COMPLEXITY_LEVEL.VERY_HIGH) {
    level = COMPLEXITY_LEVEL.MEDIUM;
  }

  // Dependencies count assessment (take highest level)
  if (metrics.dependenciesCount >= COMPLEXITY_THRESHOLDS.DEPENDENCIES_COUNT.VERY_HIGH) {
    level = COMPLEXITY_LEVEL.VERY_HIGH;
  } else if (metrics.dependenciesCount >= COMPLEXITY_THRESHOLDS.DEPENDENCIES_COUNT.HIGH && 
             level !== COMPLEXITY_LEVEL.VERY_HIGH) {
    level = COMPLEXITY_LEVEL.HIGH;
  } else if (metrics.dependenciesCount >= COMPLEXITY_THRESHOLDS.DEPENDENCIES_COUNT.MEDIUM && 
             level !== COMPLEXITY_LEVEL.HIGH && 
             level !== COMPLEXITY_LEVEL.VERY_HIGH) {
    level = COMPLEXITY_LEVEL.MEDIUM;
  }

  // Notes length assessment (take highest level)
  if (metrics.notesLength >= COMPLEXITY_THRESHOLDS.NOTES_LENGTH.VERY_HIGH) {
    level = COMPLEXITY_LEVEL.VERY_HIGH;
  } else if (metrics.notesLength >= COMPLEXITY_THRESHOLDS.NOTES_LENGTH.HIGH && 
             level !== COMPLEXITY_LEVEL.VERY_HIGH) {
    level = COMPLEXITY_LEVEL.HIGH;
  } else if (metrics.notesLength >= COMPLEXITY_THRESHOLDS.NOTES_LENGTH.MEDIUM && 
             level !== COMPLEXITY_LEVEL.HIGH && 
             level !== COMPLEXITY_LEVEL.VERY_HIGH) {
    level = COMPLEXITY_LEVEL.MEDIUM;
  }

  // Implementation guide length assessment (take highest level)
  if (metrics.implementationGuideLength >= COMPLEXITY_THRESHOLDS.IMPLEMENTATION_GUIDE_LENGTH.VERY_HIGH) {
    level = COMPLEXITY_LEVEL.VERY_HIGH;
  } else if (metrics.implementationGuideLength >= COMPLEXITY_THRESHOLDS.IMPLEMENTATION_GUIDE_LENGTH.HIGH && 
             level !== COMPLEXITY_LEVEL.VERY_HIGH) {
    level = COMPLEXITY_LEVEL.HIGH;
  } else if (metrics.implementationGuideLength >= COMPLEXITY_THRESHOLDS.IMPLEMENTATION_GUIDE_LENGTH.MEDIUM && 
             level !== COMPLEXITY_LEVEL.HIGH && 
             level !== COMPLEXITY_LEVEL.VERY_HIGH) {
    level = COMPLEXITY_LEVEL.MEDIUM;
  }

  // Verification criteria length assessment (take highest level)
  if (metrics.verificationCriteriaLength >= COMPLEXITY_THRESHOLDS.VERIFICATION_CRITERIA_LENGTH.VERY_HIGH) {
    level = COMPLEXITY_LEVEL.VERY_HIGH;
  } else if (metrics.verificationCriteriaLength >= COMPLEXITY_THRESHOLDS.VERIFICATION_CRITERIA_LENGTH.HIGH && 
             level !== COMPLEXITY_LEVEL.VERY_HIGH) {
    level = COMPLEXITY_LEVEL.HIGH;
  } else if (metrics.verificationCriteriaLength >= COMPLEXITY_THRESHOLDS.VERIFICATION_CRITERIA_LENGTH.MEDIUM && 
             level !== COMPLEXITY_LEVEL.HIGH && 
             level !== COMPLEXITY_LEVEL.VERY_HIGH) {
    level = COMPLEXITY_LEVEL.MEDIUM;
  }

  // Generate recommendations based on complexity level
  const recommendations = generateComplexityRecommendations(level, metrics);

  // Calculate overall score (0-100)
  const overallScore = calculateComplexityScore(metrics);

  return {
    level,
    overallScore,
    metrics,
    recommendations
  };
}

/**
 * Generate recommendations based on complexity level and metrics
 * @param {string} level - Complexity level
 * @param {Object} metrics - Task metrics
 * @returns {Array} Array of recommendations
 */
function generateComplexityRecommendations(level, metrics) {
  const recommendations = [];

  // Low complexity task recommendations
  if (level === COMPLEXITY_LEVEL.LOW) {
    recommendations.push("This task has low complexity and can be executed directly");
    recommendations.push("Set clear completion criteria to ensure proper verification");
  }
  // Medium complexity task recommendations
  else if (level === COMPLEXITY_LEVEL.MEDIUM) {
    recommendations.push("This task has moderate complexity, plan execution steps carefully");
    recommendations.push("Consider executing in phases and checking progress regularly");
    if (metrics.dependenciesCount > 0) {
      recommendations.push("Verify completion status and output quality of all dependency tasks");
    }
  }
  // High complexity task recommendations
  else if (level === COMPLEXITY_LEVEL.HIGH) {
    recommendations.push("This task has high complexity, perform thorough analysis and planning first");
    recommendations.push("Consider breaking down the task into smaller, independently executable subtasks");
    recommendations.push("Establish clear milestones and checkpoints to track progress and quality");
    if (metrics.dependenciesCount > COMPLEXITY_THRESHOLDS.DEPENDENCIES_COUNT.MEDIUM) {
      recommendations.push("Create a dependency graph to ensure correct execution order");
    }
  }
  // Very high complexity task recommendations
  else if (level === COMPLEXITY_LEVEL.VERY_HIGH) {
    recommendations.push("⚠️ This task has very high complexity, strongly recommend splitting into multiple tasks");
    recommendations.push("Perform detailed analysis and planning before execution, clearly define scope and interfaces");
    recommendations.push("Conduct risk assessment to identify potential obstacles and develop mitigation strategies");
    recommendations.push("Establish specific testing and verification criteria for each subtask");
    if (metrics.descriptionLength >= COMPLEXITY_THRESHOLDS.DESCRIPTION_LENGTH.VERY_HIGH) {
      recommendations.push("Task description is very long, organize key points into a structured execution list");
    }
    if (metrics.dependenciesCount >= COMPLEXITY_THRESHOLDS.DEPENDENCIES_COUNT.HIGH) {
      recommendations.push("Too many dependencies, reevaluate task boundaries to ensure reasonable task division");
    }
  }

  return recommendations;
}

/**
 * Calculate complexity score based on metrics
 * @param {Object} metrics - Task metrics
 * @returns {number} Complexity score (0-100)
 */
function calculateComplexityScore(metrics) {
  // Weight factors for each metric
  const weights = {
    descriptionLength: 0.25,
    subtasksCount: 0.2,
    dependenciesCount: 0.3,
    notesLength: 0.1,
    implementationGuideLength: 0.1,
    verificationCriteriaLength: 0.05
  };

  // Calculate normalized scores for each metric (0-100)
  const scores = {
    descriptionLength: Math.min(100, (metrics.descriptionLength / COMPLEXITY_THRESHOLDS.DESCRIPTION_LENGTH.VERY_HIGH) * 100),
    subtasksCount: Math.min(100, (metrics.subtasksCount / COMPLEXITY_THRESHOLDS.SUBTASKS_COUNT.VERY_HIGH) * 100),
    dependenciesCount: Math.min(100, (metrics.dependenciesCount / COMPLEXITY_THRESHOLDS.DEPENDENCIES_COUNT.VERY_HIGH) * 100),
    notesLength: Math.min(100, (metrics.notesLength / COMPLEXITY_THRESHOLDS.NOTES_LENGTH.VERY_HIGH) * 100),
    implementationGuideLength: Math.min(100, (metrics.implementationGuideLength / COMPLEXITY_THRESHOLDS.IMPLEMENTATION_GUIDE_LENGTH.VERY_HIGH) * 100),
    verificationCriteriaLength: Math.min(100, (metrics.verificationCriteriaLength / COMPLEXITY_THRESHOLDS.VERIFICATION_CRITERIA_LENGTH.VERY_HIGH) * 100)
  };

  // Calculate weighted average score
  let weightedScore = 0;
  let totalWeight = 0;

  for (const [metric, score] of Object.entries(scores)) {
    if (metric in weights) {
      weightedScore += score * weights[metric];
      totalWeight += weights[metric];
    }
  }

  return totalWeight > 0 ? weightedScore / totalWeight : 0;
}

/**
 * Get color for complexity level
 * @param {string} level - Complexity level
 * @returns {Function} Chalk color function
 */
export function getComplexityColor(level) {
  switch (level) {
    case COMPLEXITY_LEVEL.LOW:
      return chalk.green;
    case COMPLEXITY_LEVEL.MEDIUM:
      return chalk.blue;
    case COMPLEXITY_LEVEL.HIGH:
      return chalk.yellow;
    case COMPLEXITY_LEVEL.VERY_HIGH:
      return chalk.red;
    default:
      return chalk.white;
  }
}

export default {
  COMPLEXITY_LEVEL,
  COMPLEXITY_THRESHOLDS,
  assessTaskComplexity,
  getComplexityColor
};
