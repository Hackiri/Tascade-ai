/**
 * task_complexity.js
 * Utility functions for assessing task complexity
 */

/**
 * Complexity thresholds for different metrics
 */
export const COMPLEXITY_THRESHOLDS = {
  DESCRIPTION_LENGTH: {
    MEDIUM: 500,  // Over 500 chars is medium complexity
    HIGH: 1000,   // Over 1000 chars is high complexity
    VERY_HIGH: 2000 // Over 2000 chars is very high complexity
  },
  SUBTASKS_COUNT: {
    MEDIUM: 3,    // Over 3 subtasks is medium complexity
    HIGH: 7,      // Over 7 subtasks is high complexity
    VERY_HIGH: 15 // Over 15 subtasks is very high complexity
  },
  DEPENDENCIES_COUNT: {
    MEDIUM: 2,    // Over 2 dependencies is medium complexity
    HIGH: 5,      // Over 5 dependencies is high complexity
    VERY_HIGH: 10 // Over 10 dependencies is very high complexity
  }
};

/**
 * Complexity levels
 */
export const COMPLEXITY_LEVEL = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  VERY_HIGH: 'very_high'
};

/**
 * Assess task complexity based on various metrics
 * @param {Object} task - The task object to assess
 * @returns {Object} Complexity assessment result
 */
export function assessTaskComplexity(task) {
  // Calculate metrics
  const metrics = {
    descriptionLength: task.description ? task.description.length : 0,
    subtasksCount: task.subtasks ? task.subtasks.length : 0,
    dependenciesCount: task.dependencies ? task.dependencies.length : 0
  };
  
  // Calculate scores for each metric (0-3)
  const scores = {
    description: calculateMetricScore(
      metrics.descriptionLength,
      COMPLEXITY_THRESHOLDS.DESCRIPTION_LENGTH
    ),
    subtasks: calculateMetricScore(
      metrics.subtasksCount,
      COMPLEXITY_THRESHOLDS.SUBTASKS_COUNT
    ),
    dependencies: calculateMetricScore(
      metrics.dependenciesCount,
      COMPLEXITY_THRESHOLDS.DEPENDENCIES_COUNT
    )
  };
  
  // Calculate weighted overall score
  const overallScore = (
    scores.description * 0.4 +
    scores.subtasks * 0.3 +
    scores.dependencies * 0.3
  );
  
  // Determine complexity level
  let level = COMPLEXITY_LEVEL.LOW;
  if (overallScore >= 2.5) {
    level = COMPLEXITY_LEVEL.VERY_HIGH;
  } else if (overallScore >= 1.7) {
    level = COMPLEXITY_LEVEL.HIGH;
  } else if (overallScore >= 0.8) {
    level = COMPLEXITY_LEVEL.MEDIUM;
  }
  
  // Generate recommendations
  const recommendations = generateRecommendations(level, metrics, scores);
  
  return {
    level,
    metrics,
    scores,
    overallScore,
    recommendations
  };
}

/**
 * Calculate score for a specific metric
 * @param {number} value - Metric value
 * @param {Object} thresholds - Thresholds for the metric
 * @returns {number} Score (0-3)
 */
function calculateMetricScore(value, thresholds) {
  if (value >= thresholds.VERY_HIGH) {
    return 3;
  } else if (value >= thresholds.HIGH) {
    return 2;
  } else if (value >= thresholds.MEDIUM) {
    return 1;
  }
  return 0;
}

/**
 * Generate recommendations based on task complexity
 * @param {string} level - Complexity level
 * @param {Object} metrics - Task metrics
 * @param {Object} scores - Metric scores
 * @returns {Array} List of recommendations
 */
function generateRecommendations(level, metrics, scores) {
  const recommendations = [];
  
  // General recommendations based on overall complexity
  if (level === COMPLEXITY_LEVEL.VERY_HIGH) {
    recommendations.push('Consider breaking this task into smaller, more manageable subtasks');
    recommendations.push('Allocate additional time for implementation and review');
    recommendations.push('This task may require specialized expertise or additional resources');
  } else if (level === COMPLEXITY_LEVEL.HIGH) {
    recommendations.push('Consider breaking this task into subtasks for better management');
    recommendations.push('Plan for additional review time');
  }
  
  // Specific recommendations based on individual metrics
  if (scores.description >= 2) {
    recommendations.push('The task description is quite detailed. Consider simplifying or organizing it better');
  }
  
  if (scores.subtasks >= 2) {
    recommendations.push('This task has many subtasks. Consider grouping related subtasks');
  }
  
  if (scores.dependencies >= 2) {
    recommendations.push('This task has many dependencies. Verify all dependencies are necessary');
  }
  
  return recommendations;
}

/**
 * Format complexity level for display
 * @param {string} level - Complexity level
 * @returns {string} Formatted complexity level
 */
export function formatComplexityLevel(level) {
  switch (level) {
    case COMPLEXITY_LEVEL.LOW:
      return 'Low';
    case COMPLEXITY_LEVEL.MEDIUM:
      return 'Medium';
    case COMPLEXITY_LEVEL.HIGH:
      return 'High';
    case COMPLEXITY_LEVEL.VERY_HIGH:
      return 'Very High';
    default:
      return level;
  }
}
