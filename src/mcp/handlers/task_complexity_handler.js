/**
 * task_complexity_handler.js
 * Handles task complexity assessment requests in the MCP server
 */

import { assessTaskComplexity } from '../../utils/task_complexity.js';
import { getStorableComplexity } from '../../models/complexity.js';
import { updateTask } from '../../models/task.js';

/**
 * Handle assess-task-complexity command
 * @param {Object} params - Command parameters
 * @param {Object} context - MCP context
 * @returns {Promise<Object>} Command result
 */
export async function handleAssessTaskComplexity(params, context) {
  const { taskId } = params;
  
  if (!taskId) {
    return {
      error: 'Task ID is required'
    };
  }
  
  try {
    // Get the task
    const task = await context.db.getTask(taskId);
    
    if (!task) {
      return {
        error: `Task with ID ${taskId} not found`
      };
    }
    
    // Assess task complexity
    const complexityAssessment = assessTaskComplexity(task);
    
    // Update task with complexity assessment
    const updatedTask = updateTask(task, {
      complexity: getStorableComplexity(complexityAssessment)
    });
    
    // Save updated task
    await context.db.updateTask(updatedTask);
    
    return {
      success: true,
      task: updatedTask,
      complexity: complexityAssessment
    };
  } catch (error) {
    console.error('Error assessing task complexity:', error);
    
    return {
      error: `Failed to assess task complexity: ${error.message}`
    };
  }
}

/**
 * Handle update-task-complexity command
 * @param {Object} params - Command parameters
 * @param {Object} context - MCP context
 * @returns {Promise<Object>} Command result
 */
export async function handleUpdateTaskComplexity(params, context) {
  const { taskId, complexity } = params;
  
  if (!taskId) {
    return {
      error: 'Task ID is required'
    };
  }
  
  if (!complexity) {
    return {
      error: 'Complexity data is required'
    };
  }
  
  try {
    // Get the task
    const task = await context.db.getTask(taskId);
    
    if (!task) {
      return {
        error: `Task with ID ${taskId} not found`
      };
    }
    
    // Update task with complexity data
    const updatedTask = updateTask(task, {
      complexity: {
        ...complexity,
        assessedAt: complexity.assessedAt || new Date().toISOString()
      }
    });
    
    // Save updated task
    await context.db.updateTask(updatedTask);
    
    return {
      success: true,
      task: updatedTask
    };
  } catch (error) {
    console.error('Error updating task complexity:', error);
    
    return {
      error: `Failed to update task complexity: ${error.message}`
    };
  }
}

export default {
  handleAssessTaskComplexity,
  handleUpdateTaskComplexity
};
