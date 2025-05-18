/**
 * complexity_integration.js
 * MCP integration for task complexity features
 */

import { assessTaskComplexity, COMPLEXITY_LEVEL } from '../../utils/task_complexity.js';
import { getStorableComplexity } from '../../models/complexity.js';
import TascadeMCPServer from '../server.js';

/**
 * Register task complexity tools with the MCP server
 * @param {TascadeMCPServer} mcpServer - The MCP server instance
 */
export function registerComplexityTools(mcpServer) {
  // Register assess-complexity tool
  mcpServer.tool(
    'assess-complexity',
    {
      description: 'Assess the complexity of a task',
      params: {
        taskId: {
          type: 'string',
          description: 'ID of the task to assess'
        }
      }
    },
    async ({ taskId }, context) => {
      // Get the task from the database
      const task = await context.db.getTask(taskId);
      
      if (!task) {
        throw new Error(`Task with ID ${taskId} not found`);
      }
      
      // Assess task complexity
      const complexityAssessment = assessTaskComplexity(task);
      
      // Update task with complexity assessment
      const updatedTask = {
        ...task,
        complexity: getStorableComplexity(complexityAssessment),
        updatedAt: new Date().toISOString()
      };
      
      // Save updated task
      await context.db.updateTask(updatedTask);
      
      return {
        task: updatedTask,
        complexity: complexityAssessment
      };
    }
  );
  
  // Register suggest-splitting tool
  mcpServer.tool(
    'suggest-task-splitting',
    {
      description: 'Suggest how to split a complex task into smaller subtasks',
      params: {
        taskId: {
          type: 'string',
          description: 'ID of the task to split'
        },
        maxSubtasks: {
          type: 'number',
          description: 'Maximum number of subtasks to create',
          default: 5
        }
      }
    },
    async ({ taskId, maxSubtasks }, context) => {
      // Get the task from the database
      const task = await context.db.getTask(taskId);
      
      if (!task) {
        throw new Error(`Task with ID ${taskId} not found`);
      }
      
      // Assess task complexity if not already assessed
      let complexityAssessment;
      if (!task.complexity) {
        complexityAssessment = assessTaskComplexity(task);
        task.complexity = getStorableComplexity(complexityAssessment);
      }
      
      // Only suggest splitting for high or very high complexity tasks
      if (task.complexity.level !== COMPLEXITY_LEVEL.HIGH && 
          task.complexity.level !== COMPLEXITY_LEVEL.VERY_HIGH) {
        return {
          canSplit: false,
          reason: `Task complexity (${task.complexity.level}) is not high enough to warrant splitting`
        };
      }
      
      // Generate subtask suggestions based on task description and complexity
      const subtaskSuggestions = await generateSubtaskSuggestions(task, maxSubtasks, context);
      
      return {
        canSplit: true,
        task,
        subtaskSuggestions
      };
    }
  );
  
  // Register complexity-metrics tool
  mcpServer.tool(
    'complexity-metrics',
    {
      description: 'Get project-wide complexity metrics',
      params: {
        projectId: {
          type: 'string',
          description: 'ID of the project to analyze',
          optional: true
        }
      }
    },
    async ({ projectId }, context) => {
      // Get all tasks or tasks for a specific project
      const tasks = projectId 
        ? await context.db.getTasksByProject(projectId)
        : await context.db.getAllTasks();
      
      // Ensure all tasks have complexity assessment
      const enhancedTasks = tasks.map(task => {
        if (!task.complexity) {
          const complexityAssessment = assessTaskComplexity(task);
          task.complexity = getStorableComplexity(complexityAssessment);
        }
        return task;
      });
      
      // Calculate complexity metrics
      const metrics = calculateComplexityMetrics(enhancedTasks);
      
      return metrics;
    }
  );
  
  // Register verify-by-complexity tool
  mcpServer.tool(
    'verify-by-complexity',
    {
      description: 'Generate verification criteria based on task complexity',
      params: {
        taskId: {
          type: 'string',
          description: 'ID of the task to generate verification criteria for'
        }
      }
    },
    async ({ taskId }, context) => {
      // Get the task from the database
      const task = await context.db.getTask(taskId);
      
      if (!task) {
        throw new Error(`Task with ID ${taskId} not found`);
      }
      
      // Assess task complexity if not already assessed
      if (!task.complexity) {
        const complexityAssessment = assessTaskComplexity(task);
        task.complexity = getStorableComplexity(complexityAssessment);
      }
      
      // Generate verification criteria based on complexity
      const verificationCriteria = generateVerificationCriteria(task);
      
      return {
        task,
        verificationCriteria
      };
    }
  );
}

/**
 * Generate subtask suggestions based on task description and complexity
 * @param {Object} task - The task to split
 * @param {number} maxSubtasks - Maximum number of subtasks to create
 * @param {Object} context - MCP context
 * @returns {Array} Subtask suggestions
 */
async function generateSubtaskSuggestions(task, maxSubtasks, context) {
  // This would ideally use AI to generate subtasks based on the task description
  // For now, we'll use a simple heuristic approach
  
  const suggestions = [];
  
  // Add planning subtask for high complexity tasks
  suggestions.push({
    title: `Plan implementation approach for: ${task.title}`,
    description: 'Create a detailed plan for implementing this complex task',
    priority: task.priority,
    estimatedHours: 2
  });
  
  // Add research subtask for very high complexity tasks
  if (task.complexity.level === COMPLEXITY_LEVEL.VERY_HIGH) {
    suggestions.push({
      title: `Research best practices for: ${task.title}`,
      description: 'Research industry best practices and approaches for this complex task',
      priority: task.priority,
      estimatedHours: 4
    });
  }
  
  // Add implementation subtasks based on task description length
  const descriptionWords = task.description.split(/\\s+/);
  const keyPhrases = extractKeyPhrases(descriptionWords);
  
  // Create implementation subtasks based on key phrases
  keyPhrases.slice(0, maxSubtasks - suggestions.length).forEach(phrase => {
    suggestions.push({
      title: `Implement: ${phrase}`,
      description: `Implement the ${phrase} component of the main task`,
      priority: task.priority,
      estimatedHours: 4
    });
  });
  
  // Always add testing and documentation subtasks for complex tasks
  suggestions.push({
    title: `Test implementation of: ${task.title}`,
    description: 'Create and run tests for the implementation',
    priority: task.priority,
    estimatedHours: 3
  });
  
  suggestions.push({
    title: `Document implementation of: ${task.title}`,
    description: 'Create documentation for the implementation',
    priority: task.priority,
    estimatedHours: 2
  });
  
  return suggestions.slice(0, maxSubtasks);
}

/**
 * Extract key phrases from words
 * @param {Array} words - Array of words
 * @returns {Array} Key phrases
 */
function extractKeyPhrases(words) {
  // This is a simplified implementation
  // In a real system, this would use NLP techniques
  
  const phrases = [];
  let currentPhrase = [];
  
  words.forEach(word => {
    if (word.length > 5 || /^[A-Z]/.test(word)) {
      currentPhrase.push(word);
    } else if (currentPhrase.length > 0) {
      if (currentPhrase.length >= 2) {
        phrases.push(currentPhrase.join(' '));
      }
      currentPhrase = [];
    }
  });
  
  // Add the last phrase if it exists
  if (currentPhrase.length >= 2) {
    phrases.push(currentPhrase.join(' '));
  }
  
  return phrases.length > 0 ? phrases : ['Core functionality'];
}

/**
 * Calculate complexity metrics for a set of tasks
 * @param {Array} tasks - Array of tasks with complexity assessments
 * @returns {Object} Complexity metrics
 */
function calculateComplexityMetrics(tasks) {
  // Group tasks by complexity level
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
  
  // Calculate complexity distribution
  const complexityDistribution = {};
  Object.entries(tasksByComplexity).forEach(([level, levelTasks]) => {
    complexityDistribution[level] = (levelTasks.length / tasks.length) * 100;
  });
  
  // Calculate average complexity score
  const avgComplexityScore = tasks.reduce((sum, task) => sum + task.complexity.score, 0) / tasks.length;
  
  return {
    taskCount: tasks.length,
    tasksByComplexity,
    completionByComplexity,
    complexityDistribution,
    avgComplexityScore,
    weightedProgress
  };
}

/**
 * Generate verification criteria based on task complexity
 * @param {Object} task - Task with complexity assessment
 * @returns {Array} Verification criteria
 */
function generateVerificationCriteria(task) {
  const criteria = [];
  
  // Basic verification criteria for all tasks
  criteria.push({
    id: 'basic-functionality',
    description: 'Basic functionality works as expected',
    type: 'manual',
    required: true
  });
  
  // Add more verification criteria based on complexity
  if (task.complexity.level === COMPLEXITY_LEVEL.MEDIUM) {
    criteria.push({
      id: 'edge-cases',
      description: 'Edge cases are handled properly',
      type: 'manual',
      required: true
    });
  }
  
  if (task.complexity.level === COMPLEXITY_LEVEL.HIGH || 
      task.complexity.level === COMPLEXITY_LEVEL.VERY_HIGH) {
    criteria.push({
      id: 'performance',
      description: 'Performance meets requirements',
      type: 'automated',
      required: true
    });
    
    criteria.push({
      id: 'error-handling',
      description: 'Error cases are handled gracefully',
      type: 'manual',
      required: true
    });
    
    criteria.push({
      id: 'security',
      description: 'Security considerations are addressed',
      type: 'manual',
      required: true
    });
  }
  
  if (task.complexity.level === COMPLEXITY_LEVEL.VERY_HIGH) {
    criteria.push({
      id: 'scalability',
      description: 'Solution is scalable for future growth',
      type: 'review',
      required: true
    });
    
    criteria.push({
      id: 'documentation',
      description: 'Comprehensive documentation is provided',
      type: 'review',
      required: true
    });
    
    criteria.push({
      id: 'code-quality',
      description: 'Code quality meets team standards',
      type: 'review',
      required: true
    });
  }
  
  return criteria;
}

export default {
  registerComplexityTools
};
