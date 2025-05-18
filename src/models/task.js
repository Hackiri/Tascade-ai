/**
 * task.js
 * Data model for tasks in Tascade AI
 */

import { v4 as uuidv4 } from 'uuid';
import { validateComplexityAssessment } from './complexity.js';

/**
 * Task status enum
 */
export const TASK_STATUS = {
  PENDING: 'pending',
  IN_PROGRESS: 'in-progress',
  COMPLETED: 'completed',
  BLOCKED: 'blocked',
  CANCELLED: 'cancelled'
};

/**
 * Task priority enum
 */
export const TASK_PRIORITY = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical'
};

/**
 * Task schema
 * @typedef {Object} Task
 * @property {string} id - Unique task ID
 * @property {string} title - Task title
 * @property {string} description - Task description
 * @property {string} status - Task status
 * @property {string} priority - Task priority
 * @property {string} assignee - Task assignee
 * @property {Array} subtasks - Array of subtask objects
 * @property {Array} dependencies - Array of task IDs this task depends on
 * @property {Object} complexity - Task complexity assessment
 * @property {Array} relatedFiles - Array of files related to this task
 * @property {Array} verificationCriteria - Array of verification criteria
 * @property {Object} metadata - Additional task metadata
 * @property {string} createdAt - ISO timestamp of when the task was created
 * @property {string} updatedAt - ISO timestamp of when the task was last updated
 */

/**
 * Create a new task
 * @param {string} title - Task title
 * @param {string} description - Task description
 * @param {string} priority - Task priority
 * @param {string} assignee - Task assignee
 * @param {Object} options - Additional task options
 * @returns {Task} New task object
 */
export function createTask(title, description, priority = TASK_PRIORITY.MEDIUM, assignee = null, options = {}) {
  const now = new Date().toISOString();
  
  return {
    id: options.id || uuidv4(),
    title,
    description,
    status: options.status || TASK_STATUS.PENDING,
    priority,
    assignee,
    subtasks: options.subtasks || [],
    dependencies: options.dependencies || [],
    complexity: options.complexity || null,
    relatedFiles: options.relatedFiles || [],
    verificationCriteria: options.verificationCriteria || [],
    metadata: options.metadata || {},
    createdAt: options.createdAt || now,
    updatedAt: now
  };
}

/**
 * Validate a task object
 * @param {Object} task - Task to validate
 * @returns {boolean} True if valid, false otherwise
 */
export function validateTask(task) {
  if (!task) return false;
  
  // Check required fields
  if (!task.id || typeof task.id !== 'string') return false;
  if (!task.title || typeof task.title !== 'string') return false;
  
  // Validate status
  if (task.status && !Object.values(TASK_STATUS).includes(task.status)) {
    return false;
  }
  
  // Validate priority
  if (task.priority && !Object.values(TASK_PRIORITY).includes(task.priority)) {
    return false;
  }
  
  // Validate complexity if present
  if (task.complexity && !validateComplexityAssessment(task.complexity)) {
    return false;
  }
  
  // Validate subtasks
  if (task.subtasks && !Array.isArray(task.subtasks)) {
    return false;
  }
  
  // Validate dependencies
  if (task.dependencies && !Array.isArray(task.dependencies)) {
    return false;
  }
  
  return true;
}

/**
 * Update a task with new data
 * @param {Task} task - Existing task
 * @param {Object} updates - Updates to apply
 * @returns {Task} Updated task
 */
export function updateTask(task, updates) {
  if (!task || !updates) return task;
  
  const updatedTask = {
    ...task,
    ...updates,
    updatedAt: new Date().toISOString()
  };
  
  // Ensure we don't overwrite these fields unless explicitly provided
  if (!updates.id) updatedTask.id = task.id;
  if (!updates.createdAt) updatedTask.createdAt = task.createdAt;
  
  return updatedTask;
}

/**
 * Check if a task has circular dependencies
 * @param {string} taskId - Task ID to check
 * @param {Array} allTasks - Array of all tasks
 * @param {Set} visited - Set of visited task IDs (for recursion)
 * @param {Set} recursionStack - Set of task IDs in current recursion stack
 * @returns {boolean} True if circular dependencies exist, false otherwise
 */
export function hasCircularDependencies(taskId, allTasks, visited = new Set(), recursionStack = new Set()) {
  // Mark current node as visited and add to recursion stack
  visited.add(taskId);
  recursionStack.add(taskId);
  
  // Find the task
  const task = allTasks.find(t => t.id === taskId);
  if (!task) return false;
  
  // Check all dependencies
  for (const depId of (task.dependencies || [])) {
    // If not visited, check recursively
    if (!visited.has(depId)) {
      if (hasCircularDependencies(depId, allTasks, visited, recursionStack)) {
        return true;
      }
    }
    // If already in recursion stack, we found a cycle
    else if (recursionStack.has(depId)) {
      return true;
    }
  }
  
  // Remove from recursion stack
  recursionStack.delete(taskId);
  return false;
}

export default {
  TASK_STATUS,
  TASK_PRIORITY,
  createTask,
  validateTask,
  updateTask,
  hasCircularDependencies
};
