/**
 * Configuration loader for Tascade AI
 * 
 * This module loads configuration from config files and environment variables.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

// Get the directory of the current module
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Default configuration
const defaultConfig = {
  ai: {
    providers: {
      anthropic: {
        model: 'claude-3-opus-20240229',
        max_tokens: 4000,
        temperature: 0.7
      },
      openai: {
        model: 'gpt-4-turbo',
        max_tokens: 4000,
        temperature: 0.7
      },
      perplexity: {
        model: 'sonar-medium-online',
        max_tokens: 4000,
        temperature: 0.7
      }
    },
    task_generation: {
      default_subtasks: 10,
      default_priority: 'medium'
    }
  }
};

/**
 * Load configuration from config files and environment variables
 * @returns {Object} - The merged configuration
 */
function loadConfig() {
  let config = { ...defaultConfig };
  
  // Try to load configuration from config file
  const configPath = path.join(dirname(__dirname), '..', 'config', 'default.json');
  
  if (fs.existsSync(configPath)) {
    try {
      const fileConfig = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
      config = deepMerge(config, fileConfig);
    } catch (error) {
      console.warn(`Warning: Failed to load config file: ${error.message}`);
    }
  }
  
  // Override with environment variables
  if (process.env.ANTHROPIC_API_KEY) {
    config.ai.providers.anthropic.api_key = process.env.ANTHROPIC_API_KEY;
  }
  
  if (process.env.OPENAI_API_KEY) {
    config.ai.providers.openai.api_key = process.env.OPENAI_API_KEY;
  }
  
  if (process.env.PERPLEXITY_API_KEY) {
    config.ai.providers.perplexity.api_key = process.env.PERPLEXITY_API_KEY;
  }
  
  if (process.env.MODEL) {
    config.ai.providers.anthropic.model = process.env.MODEL;
  }
  
  if (process.env.PERPLEXITY_MODEL) {
    config.ai.providers.perplexity.model = process.env.PERPLEXITY_MODEL;
  }
  
  if (process.env.MAX_TOKENS) {
    const maxTokens = parseInt(process.env.MAX_TOKENS, 10);
    if (!isNaN(maxTokens)) {
      config.ai.providers.anthropic.max_tokens = maxTokens;
      config.ai.providers.openai.max_tokens = maxTokens;
      config.ai.providers.perplexity.max_tokens = maxTokens;
    }
  }
  
  if (process.env.TEMPERATURE) {
    const temperature = parseFloat(process.env.TEMPERATURE);
    if (!isNaN(temperature)) {
      config.ai.providers.anthropic.temperature = temperature;
      config.ai.providers.openai.temperature = temperature;
      config.ai.providers.perplexity.temperature = temperature;
    }
  }
  
  if (process.env.DEFAULT_SUBTASKS) {
    const defaultSubtasks = parseInt(process.env.DEFAULT_SUBTASKS, 10);
    if (!isNaN(defaultSubtasks)) {
      config.ai.task_generation.default_subtasks = defaultSubtasks;
    }
  }
  
  if (process.env.DEFAULT_PRIORITY) {
    config.ai.task_generation.default_priority = process.env.DEFAULT_PRIORITY;
  }
  
  return config;
}

/**
 * Deep merge two objects
 * @param {Object} target - The target object
 * @param {Object} source - The source object
 * @returns {Object} - The merged object
 */
function deepMerge(target, source) {
  const output = { ...target };
  
  if (isObject(target) && isObject(source)) {
    Object.keys(source).forEach(key => {
      if (isObject(source[key])) {
        if (!(key in target)) {
          Object.assign(output, { [key]: source[key] });
        } else {
          output[key] = deepMerge(target[key], source[key]);
        }
      } else {
        Object.assign(output, { [key]: source[key] });
      }
    });
  }
  
  return output;
}

/**
 * Check if a value is an object
 * @param {*} item - The value to check
 * @returns {boolean} - True if the value is an object, false otherwise
 */
function isObject(item) {
  return (item && typeof item === 'object' && !Array.isArray(item));
}

// Export the configuration
const config = loadConfig();
export default config;
