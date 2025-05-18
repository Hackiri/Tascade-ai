/**
 * complexity.js
 * Data models for task complexity
 */

/**
 * Complexity assessment schema
 * @typedef {Object} ComplexityAssessment
 * @property {string} level - Complexity level (low, medium, high, very_high)
 * @property {number} score - Overall complexity score
 * @property {Object} metrics - Metrics used for assessment
 * @property {Object} scores - Individual metric scores
 * @property {Array} recommendations - Recommendations based on complexity
 * @property {string} assessedAt - ISO timestamp of when the assessment was made
 */

/**
 * Create a new complexity assessment object
 * @param {string} level - Complexity level
 * @param {number} score - Overall complexity score
 * @param {Object} metrics - Metrics used for assessment
 * @param {Object} scores - Individual metric scores
 * @param {Array} recommendations - Recommendations based on complexity
 * @returns {ComplexityAssessment} New complexity assessment object
 */
export function createComplexityAssessment(level, score, metrics, scores, recommendations) {
  return {
    level,
    score,
    metrics,
    scores,
    recommendations,
    assessedAt: new Date().toISOString()
  };
}

/**
 * Validate a complexity assessment object
 * @param {Object} assessment - Complexity assessment to validate
 * @returns {boolean} True if valid, false otherwise
 */
export function validateComplexityAssessment(assessment) {
  if (!assessment) return false;
  
  // Check required fields
  if (!assessment.level || typeof assessment.level !== 'string') return false;
  if (typeof assessment.score !== 'number') return false;
  
  // Validate level values
  const validLevels = ['low', 'medium', 'high', 'very_high'];
  if (!validLevels.includes(assessment.level)) return false;
  
  return true;
}

/**
 * Get a simplified version of the complexity assessment for storage
 * @param {ComplexityAssessment} assessment - Full complexity assessment
 * @returns {Object} Simplified assessment for storage
 */
export function getStorableComplexity(assessment) {
  if (!assessment) return null;
  
  return {
    level: assessment.level,
    score: assessment.score,
    assessedAt: assessment.assessedAt || new Date().toISOString()
  };
}

/**
 * Compare two complexity assessments
 * @param {ComplexityAssessment} a - First assessment
 * @param {ComplexityAssessment} b - Second assessment
 * @returns {number} -1 if a is less complex, 0 if equal, 1 if a is more complex
 */
export function compareComplexity(a, b) {
  if (!a || !b) return 0;
  
  const levelMap = {
    'low': 1,
    'medium': 2,
    'high': 3,
    'very_high': 4
  };
  
  const levelA = levelMap[a.level] || 0;
  const levelB = levelMap[b.level] || 0;
  
  if (levelA < levelB) return -1;
  if (levelA > levelB) return 1;
  
  // If levels are the same, compare scores
  if (a.score < b.score) return -1;
  if (a.score > b.score) return 1;
  
  return 0;
}

export default {
  createComplexityAssessment,
  validateComplexityAssessment,
  getStorableComplexity,
  compareComplexity
};
