/**
 * MCP Context Manager
 * 
 * Manages context for MCP operations, particularly for task generation
 * Implements sequential thinking and context tracking
 */

export class MCPContextManager {
  /**
   * Create a new MCP Context Manager
   * @param {Object} options - Configuration options
   * @param {boolean} options.debug - Enable debug logging
   */
  constructor(options = {}) {
    const { debug = false } = options;
    
    this.debug = debug;
    this.contexts = new Map();
    this.activeContext = null;
    this.contextHistory = [];
    this.maxHistoryLength = 10;
  }
  
  /**
   * Create a new context
   * @param {string} contextId - Context identifier
   * @param {Object} initialData - Initial context data
   * @returns {string} The context ID
   */
  createContext(contextId, initialData = {}) {
    if (!contextId) {
      contextId = `ctx_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    }
    
    if (this.contexts.has(contextId)) {
      this._log(`Context ${contextId} already exists, updating instead`, 'warn');
      return this.updateContext(contextId, initialData);
    }
    
    const context = {
      id: contextId,
      created: new Date(),
      updated: new Date(),
      data: { ...initialData },
      history: [],
      steps: []
    };
    
    this.contexts.set(contextId, context);
    this.activeContext = contextId;
    this._log(`Created context: ${contextId}`, 'info');
    
    return contextId;
  }
  
  /**
   * Get a context by ID
   * @param {string} contextId - Context identifier
   * @returns {Object|null} The context object or null if not found
   */
  getContext(contextId) {
    if (!contextId && this.activeContext) {
      contextId = this.activeContext;
    }
    
    if (!contextId) {
      this._log('No context ID provided and no active context', 'error');
      return null;
    }
    
    const context = this.contexts.get(contextId);
    
    if (!context) {
      this._log(`Context not found: ${contextId}`, 'error');
      return null;
    }
    
    return context;
  }
  
  /**
   * Update a context with new data
   * @param {string} contextId - Context identifier
   * @param {Object} data - Data to update
   * @param {boolean} merge - Whether to merge with existing data or replace
   * @returns {string} The context ID
   */
  updateContext(contextId, data, merge = true) {
    const context = this.getContext(contextId);
    
    if (!context) {
      return this.createContext(contextId, data);
    }
    
    // Save the previous state in history
    context.history.push({
      timestamp: new Date(),
      data: { ...context.data }
    });
    
    // Limit history size
    if (context.history.length > this.maxHistoryLength) {
      context.history.shift();
    }
    
    // Update the context data
    if (merge) {
      context.data = {
        ...context.data,
        ...data
      };
    } else {
      context.data = { ...data };
    }
    
    context.updated = new Date();
    this._log(`Updated context: ${contextId}`, 'info');
    
    return contextId;
  }
  
  /**
   * Add a step to the context's sequential thinking process
   * @param {string} contextId - Context identifier
   * @param {string} stepName - Name of the step
   * @param {Object} stepData - Data associated with the step
   * @returns {Object} The added step
   */
  addStep(contextId, stepName, stepData = {}) {
    const context = this.getContext(contextId);
    
    if (!context) {
      this._log(`Cannot add step: context ${contextId} not found`, 'error');
      return null;
    }
    
    const step = {
      name: stepName,
      timestamp: new Date(),
      data: stepData,
      index: context.steps.length
    };
    
    context.steps.push(step);
    context.updated = new Date();
    
    this._log(`Added step ${stepName} to context ${contextId}`, 'info');
    return step;
  }
  
  /**
   * Get all steps in a context
   * @param {string} contextId - Context identifier
   * @returns {Array} Array of steps
   */
  getSteps(contextId) {
    const context = this.getContext(contextId);
    
    if (!context) {
      return [];
    }
    
    return context.steps;
  }
  
  /**
   * Get the last step in a context
   * @param {string} contextId - Context identifier
   * @returns {Object|null} The last step or null if no steps
   */
  getLastStep(contextId) {
    const steps = this.getSteps(contextId);
    
    if (steps.length === 0) {
      return null;
    }
    
    return steps[steps.length - 1];
  }
  
  /**
   * Delete a context
   * @param {string} contextId - Context identifier
   * @returns {boolean} True if deleted, false otherwise
   */
  deleteContext(contextId) {
    if (!this.contexts.has(contextId)) {
      this._log(`Context not found: ${contextId}`, 'warn');
      return false;
    }
    
    // Add to history before deleting
    this.contextHistory.push({
      id: contextId,
      deleted: new Date(),
      data: this.contexts.get(contextId)
    });
    
    // Limit history size
    if (this.contextHistory.length > this.maxHistoryLength) {
      this.contextHistory.shift();
    }
    
    // Delete the context
    this.contexts.delete(contextId);
    
    // Reset active context if it was the deleted one
    if (this.activeContext === contextId) {
      this.activeContext = null;
    }
    
    this._log(`Deleted context: ${contextId}`, 'info');
    return true;
  }
  
  /**
   * Set the active context
   * @param {string} contextId - Context identifier
   * @returns {boolean} True if set, false otherwise
   */
  setActiveContext(contextId) {
    if (!this.contexts.has(contextId)) {
      this._log(`Cannot set active context: ${contextId} not found`, 'error');
      return false;
    }
    
    this.activeContext = contextId;
    this._log(`Set active context: ${contextId}`, 'info');
    return true;
  }
  
  /**
   * Get the active context
   * @returns {Object|null} The active context or null if none
   */
  getActiveContext() {
    if (!this.activeContext) {
      return null;
    }
    
    return this.getContext(this.activeContext);
  }
  
  /**
   * Export a context to a serializable object
   * @param {string} contextId - Context identifier
   * @returns {Object|null} The serialized context or null if not found
   */
  exportContext(contextId) {
    const context = this.getContext(contextId);
    
    if (!context) {
      return null;
    }
    
    return {
      id: context.id,
      created: context.created.toISOString(),
      updated: context.updated.toISOString(),
      data: context.data,
      steps: context.steps.map(step => ({
        ...step,
        timestamp: step.timestamp.toISOString()
      })),
      history: context.history.map(item => ({
        ...item,
        timestamp: item.timestamp.toISOString()
      }))
    };
  }
  
  /**
   * Import a context from a serialized object
   * @param {Object} serializedContext - The serialized context
   * @returns {string} The context ID
   */
  importContext(serializedContext) {
    if (!serializedContext || !serializedContext.id) {
      this._log('Invalid serialized context', 'error');
      return null;
    }
    
    const { id, data, steps = [], history = [] } = serializedContext;
    
    // Create the context
    this.createContext(id, data);
    const context = this.contexts.get(id);
    
    // Set created and updated timestamps
    if (serializedContext.created) {
      context.created = new Date(serializedContext.created);
    }
    
    if (serializedContext.updated) {
      context.updated = new Date(serializedContext.updated);
    }
    
    // Import steps
    context.steps = steps.map(step => ({
      ...step,
      timestamp: new Date(step.timestamp)
    }));
    
    // Import history
    context.history = history.map(item => ({
      ...item,
      timestamp: new Date(item.timestamp)
    }));
    
    this._log(`Imported context: ${id}`, 'info');
    return id;
  }
  
  /**
   * Log a message with the appropriate level
   * @param {string} message - Message to log
   * @param {string} level - Log level (debug, info, warn, error)
   * @private
   */
  _log(message, level = 'debug') {
    if (!this.debug && level === 'debug') {
      return;
    }
    
    const timestamp = new Date().toISOString();
    const prefix = `[MCPContextManager][${level.toUpperCase()}][${timestamp}]`;
    
    switch (level) {
      case 'error':
        console.error(`${prefix} ${message}`);
        break;
      case 'warn':
        console.warn(`${prefix} ${message}`);
        break;
      case 'info':
        console.info(`${prefix} ${message}`);
        break;
      default:
        console.log(`${prefix} ${message}`);
    }
  }
}

/**
 * Create a new MCP Context Manager
 * @param {Object} options - Configuration options
 * @returns {MCPContextManager} A new MCP Context Manager instance
 */
export function createMCPContextManager(options = {}) {
  return new MCPContextManager(options);
}
