/**
 * verification_generator.js
 * Verification criteria generator for Tascade AI
 * Based on superior implementations from MCP Shrimp Task Manager
 */

import { COMPLEXITY_LEVEL, COMPLEXITY_THRESHOLDS } from './enhanced_task_complexity.js';

/**
 * Verification criteria types
 */
export const VERIFICATION_TYPE = {
  FUNCTIONAL: 'functional',
  PERFORMANCE: 'performance',
  SECURITY: 'security',
  COMPATIBILITY: 'compatibility',
  DOCUMENTATION: 'documentation',
  CODE_QUALITY: 'code_quality',
  TESTING: 'testing'
};

/**
 * Generate verification criteria based on task complexity
 * @param {Object} task - The task to generate criteria for
 * @returns {Array} Array of verification criteria
 */
export function generateVerificationCriteria(task) {
  const criteria = [];
  
  // Determine complexity level if not already set
  const complexityLevel = task.complexity ? task.complexity.level : COMPLEXITY_LEVEL.MEDIUM;
  
  // Add basic functional criteria for all tasks
  criteria.push({
    type: VERIFICATION_TYPE.FUNCTIONAL,
    description: `The implementation fulfills the requirements specified in the task description: "${task.title}"`,
    required: true
  });
  
  // Add code quality criteria for all tasks
  criteria.push({
    type: VERIFICATION_TYPE.CODE_QUALITY,
    description: 'The code follows project coding standards and conventions',
    required: true
  });
  
  // Add documentation criteria for all tasks
  criteria.push({
    type: VERIFICATION_TYPE.DOCUMENTATION,
    description: 'The implementation includes appropriate documentation (comments, JSDoc, etc.)',
    required: true
  });
  
  // Add criteria based on complexity level
  if (complexityLevel === COMPLEXITY_LEVEL.MEDIUM || 
      complexityLevel === COMPLEXITY_LEVEL.HIGH || 
      complexityLevel === COMPLEXITY_LEVEL.VERY_HIGH) {
    
    // Add testing criteria for medium+ complexity
    criteria.push({
      type: VERIFICATION_TYPE.TESTING,
      description: 'The implementation includes appropriate tests',
      required: true
    });
    
    // Add performance criteria for medium+ complexity
    criteria.push({
      type: VERIFICATION_TYPE.PERFORMANCE,
      description: 'The implementation performs efficiently and does not introduce performance regressions',
      required: complexityLevel !== COMPLEXITY_LEVEL.MEDIUM
    });
  }
  
  // Add additional criteria for high and very high complexity tasks
  if (complexityLevel === COMPLEXITY_LEVEL.HIGH || complexityLevel === COMPLEXITY_LEVEL.VERY_HIGH) {
    // Add security criteria for high+ complexity
    criteria.push({
      type: VERIFICATION_TYPE.SECURITY,
      description: 'The implementation follows security best practices and does not introduce vulnerabilities',
      required: true
    });
    
    // Add compatibility criteria for high+ complexity
    criteria.push({
      type: VERIFICATION_TYPE.COMPATIBILITY,
      description: 'The implementation is compatible with the existing codebase and dependencies',
      required: true
    });
    
    // Add edge case handling for high+ complexity
    criteria.push({
      type: VERIFICATION_TYPE.FUNCTIONAL,
      description: 'The implementation handles edge cases and error conditions appropriately',
      required: true
    });
  }
  
  // Add specific criteria for very high complexity tasks
  if (complexityLevel === COMPLEXITY_LEVEL.VERY_HIGH) {
    // Add scalability criteria for very high complexity
    criteria.push({
      type: VERIFICATION_TYPE.PERFORMANCE,
      description: 'The implementation is scalable and can handle increased load or data volume',
      required: true
    });
    
    // Add maintainability criteria for very high complexity
    criteria.push({
      type: VERIFICATION_TYPE.CODE_QUALITY,
      description: 'The implementation is maintainable and follows SOLID principles',
      required: true
    });
    
    // Add comprehensive testing criteria for very high complexity
    criteria.push({
      type: VERIFICATION_TYPE.TESTING,
      description: 'The implementation includes comprehensive tests covering edge cases and failure scenarios',
      required: true
    });
  }
  
  // Add criteria based on related files
  if (task.relatedFiles && task.relatedFiles.length > 0) {
    const fileTypes = getUniqueFileTypes(task.relatedFiles);
    
    // Add criteria for UI files
    if (fileTypes.includes('css') || fileTypes.includes('scss') || fileTypes.includes('html')) {
      criteria.push({
        type: VERIFICATION_TYPE.COMPATIBILITY,
        description: 'The UI implementation is responsive and works across different screen sizes',
        required: false
      });
    }
    
    // Add criteria for API files
    if (task.description && (task.description.includes('API') || task.description.includes('endpoint'))) {
      criteria.push({
        type: VERIFICATION_TYPE.FUNCTIONAL,
        description: 'The API endpoints return appropriate status codes and error messages',
        required: true
      });
    }
  }
  
  // Add criteria based on task dependencies
  if (task.dependencies && task.dependencies.length > 0) {
    criteria.push({
      type: VERIFICATION_TYPE.COMPATIBILITY,
      description: `The implementation integrates correctly with dependent tasks (${task.dependencies.length} dependencies)`,
      required: true
    });
  }
  
  return criteria;
}

/**
 * Get unique file types from related files
 * @param {Array} relatedFiles - Array of related files
 * @returns {Array} Array of unique file extensions
 */
function getUniqueFileTypes(relatedFiles) {
  const extensions = relatedFiles.map(file => {
    const parts = file.path.split('.');
    return parts.length > 1 ? parts.pop().toLowerCase() : '';
  });
  
  return [...new Set(extensions)].filter(ext => ext);
}

/**
 * Format verification criteria for display
 * @param {Array} criteria - Array of verification criteria
 * @returns {string} Formatted criteria
 */
export function formatVerificationCriteria(criteria) {
  return criteria.map((criterion, index) => {
    const requirementLabel = criterion.required ? '[Required]' : '[Optional]';
    return `${index + 1}. ${criterion.description} ${requirementLabel} [${criterion.type}]`;
  }).join('\n');
}

export default {
  VERIFICATION_TYPE,
  generateVerificationCriteria,
  formatVerificationCriteria
};
