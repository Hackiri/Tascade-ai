/**
 * task_splitter.js
 * Advanced task splitting utility for Tascade AI
 * Based on superior implementations from MCP Shrimp Task Manager
 */

import { COMPLEXITY_LEVEL, COMPLEXITY_THRESHOLDS } from './enhanced_task_complexity.js';

/**
 * Analyze a task and suggest how to split it into subtasks
 * @param {Object} task - The task to split
 * @param {Object} options - Splitting options
 * @param {number} options.maxSubtasks - Maximum number of subtasks to create
 * @returns {Array} Array of suggested subtasks
 */
export function suggestTaskSplitting(task, options = {}) {
  const maxSubtasks = options.maxSubtasks || 5;
  const suggestions = [];
  
  // Only suggest splitting for high or very high complexity tasks
  if (task.complexity && 
      (task.complexity.level !== COMPLEXITY_LEVEL.HIGH && 
       task.complexity.level !== COMPLEXITY_LEVEL.VERY_HIGH)) {
    return [{
      title: 'Task does not need splitting',
      description: `Task complexity (${task.complexity.level}) is not high enough to warrant splitting`,
      priority: task.priority,
      estimatedHours: 1
    }];
  }
  
  // Add planning subtask for complex tasks
  suggestions.push({
    title: `Plan implementation approach for: ${task.title}`,
    description: 'Create a detailed plan for implementing this complex task',
    priority: task.priority,
    estimatedHours: 2,
    relatedFiles: task.relatedFiles
  });
  
  // Add research subtask for very high complexity tasks
  if (!task.complexity || task.complexity.level === COMPLEXITY_LEVEL.VERY_HIGH) {
    suggestions.push({
      title: `Research best practices for: ${task.title}`,
      description: 'Research industry best practices and approaches for this complex task',
      priority: task.priority,
      estimatedHours: 4
    });
  }
  
  // Extract key components from task description and implementation guide
  const components = extractTaskComponents(task);
  
  // Create implementation subtasks based on components
  components.slice(0, maxSubtasks - suggestions.length - 2).forEach(component => {
    suggestions.push({
      title: `Implement: ${component.name}`,
      description: component.description,
      priority: task.priority,
      estimatedHours: estimateImplementationHours(component),
      relatedFiles: component.relatedFiles
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
 * Extract key components from a task
 * @param {Object} task - The task to analyze
 * @returns {Array} Array of task components
 */
function extractTaskComponents(task) {
  const components = [];
  
  // Extract components from implementation guide if available
  if (task.implementationGuide) {
    const guideComponents = extractComponentsFromText(task.implementationGuide);
    components.push(...guideComponents);
  }
  
  // Extract components from description if needed
  if (components.length < 3 && task.description) {
    const descriptionComponents = extractComponentsFromText(task.description);
    
    // Add components that aren't already included
    descriptionComponents.forEach(component => {
      if (!components.some(c => c.name.toLowerCase().includes(component.name.toLowerCase()))) {
        components.push(component);
      }
    });
  }
  
  // Extract components from related files if available
  if (task.relatedFiles && task.relatedFiles.length > 0) {
    const fileGroups = groupRelatedFilesByType(task.relatedFiles);
    
    Object.entries(fileGroups).forEach(([type, files]) => {
      if (files.length > 0) {
        components.push({
          name: `${type} files`,
          description: `Implement changes to ${type} files: ${files.map(f => f.path.split('/').pop()).join(', ')}`,
          relatedFiles: files,
          complexity: files.length
        });
      }
    });
  }
  
  // If still not enough components, create generic ones
  if (components.length < 3) {
    components.push(
      {
        name: 'Core functionality',
        description: 'Implement the core functionality of the task',
        complexity: 3
      },
      {
        name: 'User interface',
        description: 'Implement the user interface components',
        complexity: 2
      },
      {
        name: 'Integration',
        description: 'Integrate the implementation with existing systems',
        complexity: 2
      }
    );
  }
  
  return components;
}

/**
 * Extract components from text
 * @param {string} text - The text to analyze
 * @returns {Array} Array of components
 */
function extractComponentsFromText(text) {
  const components = [];
  
  // Look for sections with headers or bullet points
  const sectionRegex = /(?:^|\n)(?:#{1,3}\s+|[\*\-]\s+)(.+?)(?=\n|$)/g;
  let match;
  
  while ((match = sectionRegex.exec(text)) !== null) {
    const sectionTitle = match[1].trim();
    if (sectionTitle.length > 3 && !components.some(c => c.name === sectionTitle)) {
      components.push({
        name: sectionTitle,
        description: `Implement the ${sectionTitle} component`,
        complexity: 2
      });
    }
  }
  
  // Look for code blocks or technical terms
  const codeBlockRegex = /```[\s\S]+?```/g;
  const codeMatches = text.match(codeBlockRegex);
  
  if (codeMatches) {
    codeMatches.forEach((codeBlock, index) => {
      const name = `Component ${index + 1}`;
      components.push({
        name,
        description: `Implement ${name} based on provided code example`,
        complexity: 3,
        codeExample: codeBlock.replace(/```/g, '').trim()
      });
    });
  }
  
  // Look for technical terms or phrases
  const technicalTerms = extractTechnicalTerms(text);
  technicalTerms.forEach(term => {
    if (!components.some(c => c.name.toLowerCase().includes(term.toLowerCase()))) {
      components.push({
        name: term,
        description: `Implement the ${term} functionality`,
        complexity: 2
      });
    }
  });
  
  return components;
}

/**
 * Extract technical terms from text
 * @param {string} text - The text to analyze
 * @returns {Array} Array of technical terms
 */
function extractTechnicalTerms(text) {
  const terms = [];
  
  // Common technical patterns
  const patterns = [
    /(\w+)\s+API/gi,
    /(\w+)\s+component/gi,
    /(\w+)\s+module/gi,
    /(\w+)\s+function/gi,
    /(\w+)\s+class/gi,
    /(\w+)\s+interface/gi,
    /(\w+)\s+service/gi,
    /implement\s+(\w+)/gi
  ];
  
  patterns.forEach(pattern => {
    let match;
    while ((match = pattern.exec(text)) !== null) {
      const term = match[1].trim();
      if (term.length > 3 && !terms.includes(term)) {
        terms.push(term);
      }
    }
  });
  
  return terms;
}

/**
 * Group related files by type
 * @param {Array} relatedFiles - Array of related files
 * @returns {Object} Grouped files by type
 */
function groupRelatedFilesByType(relatedFiles) {
  const groups = {};
  
  relatedFiles.forEach(file => {
    const extension = file.path.split('.').pop().toLowerCase();
    let type;
    
    // Determine file type
    if (['js', 'ts', 'jsx', 'tsx'].includes(extension)) {
      type = 'JavaScript';
    } else if (['css', 'scss', 'less'].includes(extension)) {
      type = 'CSS';
    } else if (['html', 'htm'].includes(extension)) {
      type = 'HTML';
    } else if (['json', 'yaml', 'yml'].includes(extension)) {
      type = 'Config';
    } else if (['md', 'txt'].includes(extension)) {
      type = 'Documentation';
    } else {
      type = 'Other';
    }
    
    if (!groups[type]) {
      groups[type] = [];
    }
    
    groups[type].push(file);
  });
  
  return groups;
}

/**
 * Estimate implementation hours based on component complexity
 * @param {Object} component - The component to estimate
 * @returns {number} Estimated hours
 */
function estimateImplementationHours(component) {
  const baseHours = 2;
  const complexityFactor = component.complexity || 2;
  
  return Math.max(1, Math.round(baseHours * (complexityFactor / 2)));
}

export default {
  suggestTaskSplitting
};
