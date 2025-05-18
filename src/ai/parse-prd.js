/**
 * PRD Parsing Module for Tascade AI
 * 
 * This module provides functionality to parse PRD files and generate tasks using AI.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import { generateStructuredData } from './providers.js';
import config from '../config/index.js';

// Get the directory of the current module
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Task schema for validation
 * This defines the expected structure of a task generated from a PRD
 */
const taskSchema = {
  id: 'number',
  title: 'string',
  description: 'string',
  priority: 'string',
  dependencies: 'array',
  status: 'string'
};

/**
 * Validate a task object against the schema
 * @param {Object} task - The task object to validate
 * @returns {boolean} - True if valid, false otherwise
 */
function validateTask(task) {
  for (const [key, type] of Object.entries(taskSchema)) {
    if (key === 'dependencies') {
      if (!Array.isArray(task[key])) {
        return false;
      }
    } else if (typeof task[key] !== type) {
      return false;
    }
  }
  return true;
}

/**
 * Generate the system prompt for PRD parsing
 * @returns {string} - The system prompt
 */
function generateSystemPrompt() {
  return `You are a task decomposition expert. Your job is to analyze a Product Requirements Document (PRD) and break it down into concrete, actionable tasks.

Follow these guidelines:
1. Each task should be specific, clear, and actionable
2. Tasks should cover all requirements in the PRD
3. Include dependencies between tasks where appropriate
4. Assign a priority (high, medium, low) to each task
5. Provide a detailed description for each task

You must return a valid JSON object with the following structure:
{
  "tasks": [
    {
      "id": 1,
      "title": "Task title",
      "description": "Detailed description of the task",
      "priority": "high|medium|low",
      "dependencies": [list of task IDs this task depends on],
      "status": "pending"
    },
    // more tasks...
  ],
  "metadata": {
    "projectName": "Name extracted from the PRD",
    "totalTasks": number of tasks,
    "sourceFile": "Name of the source file",
    "generatedAt": "Current timestamp"
  }
}`;
}

/**
 * Generate the user prompt for PRD parsing
 * @param {string} prdContent - The content of the PRD file
 * @param {number} numTasks - The desired number of tasks
 * @returns {string} - The user prompt
 */
function generateUserPrompt(prdContent, numTasks) {
  return `Here is a Product Requirements Document (PRD) that needs to be broken down into tasks:

${prdContent}

Please generate ${numTasks} tasks based on this PRD. Make sure to follow the JSON structure specified in the system prompt.`;
}

/**
 * Parse a PRD file and generate tasks
 * @param {string} prdPath - Path to the PRD file
 * @param {string} tasksPath - Path to save the generated tasks
 * @param {number} numTasks - Number of tasks to generate
 * @param {Object} options - Additional options
 * @param {string} options.provider - AI provider to use (anthropic, openai)
 * @param {boolean} options.force - Whether to overwrite existing tasks file
 * @returns {Promise<Object>} - The generated tasks
 */
async function parsePRD(prdPath, tasksPath, numTasks = 10, options = {}) {
  // Get default number of tasks from config if available
  const defaultNumTasks = config.ai.task_generation.default_subtasks || 10;
  
  // Use options with defaults from config
  const { 
    provider = 'anthropic', 
    force = false,
    priority = config.ai.task_generation.default_priority || 'medium'
  } = options;
  
  // Use provided numTasks or default from config
  numTasks = numTasks || defaultNumTasks;
  
  // Check if the PRD file exists
  if (!fs.existsSync(prdPath)) {
    throw new Error(`PRD file not found: ${prdPath}`);
  }
  
  // Check if the tasks file already exists
  if (fs.existsSync(tasksPath) && !force) {
    throw new Error(`Tasks file already exists: ${tasksPath}. Use --force to overwrite.`);
  }
  
  // Read the PRD file
  const prdContent = fs.readFileSync(prdPath, 'utf-8');
  
  // Generate prompts
  const systemPrompt = generateSystemPrompt();
  const userPrompt = generateUserPrompt(prdContent, numTasks);
  
  console.log(`Generating ${numTasks} tasks from PRD using ${provider}...`);
  
  try {
    // Generate tasks using AI
    const result = await generateStructuredData({
      prompt: userPrompt,
      systemPrompt: systemPrompt,
      provider
    });
    
    // Validate the result
    if (!result || !result.tasks || !Array.isArray(result.tasks)) {
      throw new Error('Invalid response from AI: missing tasks array');
    }
    
    // Validate each task
    for (const task of result.tasks) {
      if (!validateTask(task)) {
        throw new Error(`Invalid task format: ${JSON.stringify(task)}`);
      }
    }
    
    // Add metadata if missing
    if (!result.metadata) {
      result.metadata = {
        projectName: path.basename(prdPath, path.extname(prdPath)),
        totalTasks: result.tasks.length,
        sourceFile: path.basename(prdPath),
        generatedAt: new Date().toISOString()
      };
    }
    
    // Write the tasks to the output file
    fs.writeFileSync(tasksPath, JSON.stringify(result, null, 2), 'utf-8');
    
    console.log(`Successfully generated ${result.tasks.length} tasks and saved to ${tasksPath}`);
    
    return result;
  } catch (error) {
    throw new Error(`Failed to generate tasks: ${error.message}`);
  }
}

export default parsePRD;
