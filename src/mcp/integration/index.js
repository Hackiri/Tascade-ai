/**
 * index.js
 * Main integration module for Tascade AI MCP server
 */

import { registerComplexityTools } from './complexity_integration.js';

/**
 * Register all feature integrations with the MCP server
 * @param {Object} mcpServer - The MCP server instance
 * @param {Object} options - Integration options
 */
export function registerFeatureIntegrations(mcpServer, options = {}) {
  // Register complexity tools
  registerComplexityTools(mcpServer);
  
  // Register other feature integrations as they are developed
  // registerDependencyTools(mcpServer);
  // registerVerificationTools(mcpServer);
  // registerProgressVisualizationTools(mcpServer);
  
  console.log('Registered all feature integrations with MCP server');
}

export default {
  registerFeatureIntegrations
};
