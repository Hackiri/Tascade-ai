/**
 * feature_integration.js
 * Utility functions for integrating different features in Tascade AI
 */

import { assessTaskComplexity, COMPLEXITY_LEVEL } from './task_complexity.js';
import { createComplexityIndicator } from '../cli/ui/complexity.js';

/**
 * Integrate task complexity with task display
 * @param {Object} task - Task object
 * @param {Object} options - Display options
 * @returns {Object} Enhanced task object with complexity information
 */
export function integrateComplexityWithTask(task, options = {}) {
  // If task already has complexity assessment, use it
  if (!task.complexity) {
    // Otherwise, assess complexity on the fly
    const complexityAssessment = assessTaskComplexity(task);
    task.complexity = {
      level: complexityAssessment.level,
      score: complexityAssessment.overallScore,
      assessedAt: new Date().toISOString()
    };
  }
  
  // Add complexity indicator to task display
  task.complexityIndicator = createComplexityIndicator(task.complexity.level);
  
  return task;
}

/**
 * Integrate task complexity with task splitting
 * @param {Object} task - Task object
 * @returns {boolean} True if task should be split based on complexity
 */
export function shouldSplitTaskByComplexity(task) {
  if (!task.complexity) {
    const complexityAssessment = assessTaskComplexity(task);
    task.complexity = {
      level: complexityAssessment.level,
      score: complexityAssessment.overallScore
    };
  }
  
  // Suggest splitting for high and very high complexity tasks
  return task.complexity.level === COMPLEXITY_LEVEL.HIGH || 
         task.complexity.level === COMPLEXITY_LEVEL.VERY_HIGH;
}

/**
 * Integrate task complexity with dependency management
 * @param {Object} task - Task object
 * @param {Array} allTasks - All tasks in the project
 * @returns {Object} Dependency analysis result
 */
export function analyzeDependenciesByComplexity(task, allTasks) {
  if (!task.complexity) {
    const complexityAssessment = assessTaskComplexity(task);
    task.complexity = {
      level: complexityAssessment.level,
      score: complexityAssessment.overallScore
    };
  }
  
  // Get task dependencies
  const dependencies = task.dependencies || [];
  
  // Get dependent tasks
  const dependentTasks = allTasks.filter(t => 
    (t.dependencies || []).includes(task.id)
  );
  
  // Analyze complexity of dependencies
  const dependenciesComplexity = dependencies.map(depId => {
    const depTask = allTasks.find(t => t.id === depId);
    if (!depTask) return null;
    
    if (!depTask.complexity) {
      const complexityAssessment = assessTaskComplexity(depTask);
      depTask.complexity = {
        level: complexityAssessment.level,
        score: complexityAssessment.overallScore
      };
    }
    
    return {
      id: depId,
      complexity: depTask.complexity
    };
  }).filter(Boolean);
  
  // Calculate average complexity score of dependencies
  const avgComplexityScore = dependenciesComplexity.length > 0 
    ? dependenciesComplexity.reduce((sum, dep) => sum + dep.complexity.score, 0) / dependenciesComplexity.length
    : 0;
  
  return {
    dependencies,
    dependentTasks,
    dependenciesComplexity,
    avgComplexityScore,
    isComplexDependencyChain: avgComplexityScore > 1.5
  };
}

/**
 * Integrate task complexity with verification criteria
 * @param {Object} task - Task object
 * @returns {Array} Suggested verification criteria based on complexity
 */
export function suggestVerificationCriteria(task) {
  if (!task.complexity) {
    const complexityAssessment = assessTaskComplexity(task);
    task.complexity = {
      level: complexityAssessment.level,
      score: complexityAssessment.overallScore
    };
  }
  
  const suggestedCriteria = [];
  
  // Basic verification criteria for all tasks
  suggestedCriteria.push({
    id: 'basic-functionality',
    description: 'Basic functionality works as expected',
    type: 'manual'
  });
  
  // Add more verification criteria based on complexity
  if (task.complexity.level === COMPLEXITY_LEVEL.MEDIUM) {
    suggestedCriteria.push({
      id: 'edge-cases',
      description: 'Edge cases are handled properly',
      type: 'manual'
    });
  }
  
  if (task.complexity.level === COMPLEXITY_LEVEL.HIGH || 
      task.complexity.level === COMPLEXITY_LEVEL.VERY_HIGH) {
    suggestedCriteria.push({
      id: 'performance',
      description: 'Performance meets requirements',
      type: 'automated'
    });
    
    suggestedCriteria.push({
      id: 'error-handling',
      description: 'Error cases are handled gracefully',
      type: 'manual'
    });
    
    suggestedCriteria.push({
      id: 'security',
      description: 'Security considerations are addressed',
      type: 'manual'
    });
  }
  
  if (task.complexity.level === COMPLEXITY_LEVEL.VERY_HIGH) {
    suggestedCriteria.push({
      id: 'scalability',
      description: 'Solution is scalable for future growth',
      type: 'review'
    });
    
    suggestedCriteria.push({
      id: 'documentation',
      description: 'Comprehensive documentation is provided',
      type: 'review'
    });
  }
  
  return suggestedCriteria;
}

/**
 * Integrate task complexity with project progress visualization
 * @param {Array} tasks - All tasks in the project
 * @returns {Object} Complexity-based progress metrics
 */
export function calculateComplexityBasedProgress(tasks) {
  // Ensure all tasks have complexity assessment
  tasks.forEach(task => {
    if (!task.complexity) {
      const complexityAssessment = assessTaskComplexity(task);
      task.complexity = {
        level: complexityAssessment.level,
        score: complexityAssessment.overallScore
      };
    }
  });
  
  // Group tasks by complexity
  const tasksByComplexity = {
    [COMPLEXITY_LEVEL.LOW]: tasks.filter(t => t.complexity.level === COMPLEXITY_LEVEL.LOW),
    [COMPLEXITY_LEVEL.MEDIUM]: tasks.filter(t => t.complexity.level === COMPLEXITY_LEVEL.MEDIUM),
    [COMPLEXITY_LEVEL.HIGH]: tasks.filter(t => t.complexity.level === COMPLEXITY_LEVEL.HIGH),
    [COMPLEXITY_LEVEL.VERY_HIGH]: tasks.filter(t => t.complexity.level === COMPLEXITY_LEVEL.VERY_HIGH)
  };
  
  // Calculate completion by complexity
  const completionByComplexity = {};
  Object.entries(tasksByComplexity).forEach(([level, levelTasks]) => {
    const totalTasks = levelTasks.length;
    const completedTasks = levelTasks.filter(t => t.status === 'completed').length;
    
    completionByComplexity[level] = {
      total: totalTasks,
      completed: completedTasks,
      percentage: totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0
    };
  });
  
  // Calculate weighted progress
  const weightMap = {
    [COMPLEXITY_LEVEL.LOW]: 1,
    [COMPLEXITY_LEVEL.MEDIUM]: 2,
    [COMPLEXITY_LEVEL.HIGH]: 3,
    [COMPLEXITY_LEVEL.VERY_HIGH]: 5
  };
  
  let totalWeight = 0;
  let completedWeight = 0;
  
  Object.entries(tasksByComplexity).forEach(([level, levelTasks]) => {
    const weight = weightMap[level];
    
    levelTasks.forEach(task => {
      totalWeight += weight;
      if (task.status === 'completed') {
        completedWeight += weight;
      }
    });
  });
  
  const weightedProgress = totalWeight > 0 ? (completedWeight / totalWeight) * 100 : 0;
  
  return {
    tasksByComplexity,
    completionByComplexity,
    weightedProgress
  };
}

export default {
  integrateComplexityWithTask,
  shouldSplitTaskByComplexity,
  analyzeDependenciesByComplexity,
  suggestVerificationCriteria,
  calculateComplexityBasedProgress
};
