/**
 * AI Provider Integration for Tascade AI
 * 
 * This module provides integration with various AI providers for task generation.
 */

import fetch from 'node-fetch';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs';
import config from '../config/index.js';

// Get the directory of the current module
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Get the API key for a provider from environment variables
 * @param {string} provider - The provider name
 * @returns {string|null} - The API key or null if not found
 */
function getApiKey(provider) {
  const keyMap = {
    'anthropic': 'ANTHROPIC_API_KEY',
    'openai': 'OPENAI_API_KEY',
    'perplexity': 'PERPLEXITY_API_KEY',
    'google': 'GOOGLE_API_KEY'
  };

  const envKey = keyMap[provider];
  if (!envKey) return null;

  return process.env[envKey] || null;
}

/**
 * Generate structured data using Anthropic Claude
 * @param {Object} params - Parameters for the API call
 * @param {string} params.prompt - The prompt for the AI
 * @param {string} params.systemPrompt - The system prompt
 * @returns {Promise<Object>} - The generated object
 */
async function generateWithAnthropic(params) {
  // Use API key from config or environment variable
  const apiKey = config.ai.providers.anthropic.api_key || getApiKey('anthropic');
  
  if (!apiKey) {
    throw new Error('ANTHROPIC_API_KEY environment variable is not set. Please set it to use Anthropic Claude.');
  }
  
  const { prompt, systemPrompt } = params;
  const anthropicConfig = config.ai.providers.anthropic;
  
  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: anthropicConfig.model,
        max_tokens: anthropicConfig.max_tokens,
        temperature: anthropicConfig.temperature,
        system: systemPrompt,
        messages: [
          {
            role: 'user',
            content: prompt
          }
        ]
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Anthropic API error: ${errorData.error?.message || response.statusText}`);
    }
    
    const data = await response.json();
    
    // Extract JSON from the response
    const content = data.content[0].text;
    const jsonMatch = content.match(/```json\n([\s\S]+?)\n```/) || 
                      content.match(/```([\s\S]+?)```/) || 
                      content.match(/{[\s\S]+}/); 
    
    if (jsonMatch) {
      try {
        return JSON.parse(jsonMatch[1] || jsonMatch[0]);
      } catch (parseError) {
        throw new Error(`Failed to parse JSON from Anthropic response: ${parseError.message}`);
      }
    } else {
      throw new Error('No valid JSON found in Anthropic response');
    }
  } catch (error) {
    throw new Error(`Error calling Anthropic API: ${error.message}`);
  }
}

/**
 * Generate structured data using OpenAI
 * @param {Object} params - Parameters for the API call
 * @param {string} params.prompt - The prompt for the AI
 * @param {string} params.systemPrompt - The system prompt
 * @returns {Promise<Object>} - The generated object
 */
async function generateWithOpenAI(params) {
  // Use API key from config or environment variable
  const apiKey = config.ai.providers.openai.api_key || getApiKey('openai');
  if (!apiKey) {
    throw new Error('OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.');
  }

  const { prompt, systemPrompt } = params;
  const openaiConfig = config.ai.providers.openai;

  try {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: openaiConfig.model,
        messages: [
          {
            role: 'system',
            content: systemPrompt
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: openaiConfig.temperature,
        max_tokens: openaiConfig.max_tokens,
        response_format: { type: 'json_object' }
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`OpenAI API error: ${errorData.error?.message || response.statusText}`);
    }

    const data = await response.json();
    const content = data.choices[0].message.content;
    
    try {
      return JSON.parse(content);
    } catch (e) {
      throw new Error(`Failed to parse JSON from OpenAI response: ${e.message}`);
    }
  } catch (error) {
    throw new Error(`Error calling OpenAI API: ${error.message}`);
  }
}

/**
 * Generate structured data using the configured AI provider
 * @param {Object} params - Parameters for the API call
 * @param {string} params.prompt - The prompt for the AI
 * @param {string} params.systemPrompt - The system prompt
 * @param {string} params.provider - The AI provider to use (anthropic, openai)
 * @returns {Promise<Object>} - The generated object
 */
/**
 * Generate structured data using Perplexity
 * @param {Object} params - Parameters for the API call
 * @param {string} params.prompt - The prompt for the AI
 * @param {string} params.systemPrompt - The system prompt
 * @returns {Promise<Object>} - The generated object
 */
async function generateWithPerplexity(params) {
  // Use API key from config or environment variable
  const apiKey = config.ai.providers.perplexity.api_key || getApiKey('perplexity');
  if (!apiKey) {
    throw new Error('Perplexity API key not found. Please set the PERPLEXITY_API_KEY environment variable.');
  }

  const { prompt, systemPrompt } = params;
  const perplexityConfig = config.ai.providers.perplexity;

  try {
    const response = await fetch('https://api.perplexity.ai/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: perplexityConfig.model,
        messages: [
          {
            role: 'system',
            content: systemPrompt
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: perplexityConfig.temperature,
        max_tokens: perplexityConfig.max_tokens
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Perplexity API error: ${errorData.error?.message || response.statusText}`);
    }

    const data = await response.json();
    const content = data.choices[0].message.content;
    
    try {
      // Try to parse JSON directly
      return JSON.parse(content);
    } catch (e) {
      // If direct parsing fails, try to extract JSON from markdown code blocks
      const jsonMatch = content.match(/```json\n([\s\S]+?)\n```/) || 
                        content.match(/```([\s\S]+?)```/) || 
                        content.match(/{[\s\S]+}/);
      
      if (jsonMatch) {
        try {
          return JSON.parse(jsonMatch[1] || jsonMatch[0]);
        } catch (parseError) {
          throw new Error(`Failed to parse JSON from Perplexity response: ${parseError.message}`);
        }
      } else {
        throw new Error('No valid JSON found in Perplexity response');
      }
    }
  } catch (error) {
    throw new Error(`Error calling Perplexity API: ${error.message}`);
  }
}

/**
 * Generate structured data using the configured AI provider
 * @param {Object} params - Parameters for the API call
 * @param {string} params.prompt - The prompt for the AI
 * @param {string} params.systemPrompt - The system prompt
 * @param {string} params.provider - The AI provider to use (anthropic, openai, perplexity)
 * @returns {Promise<Object>} - The generated object
 */
async function generateStructuredData(params) {
  const { provider = 'anthropic' } = params;
  
  // Select the appropriate provider function
  switch (provider.toLowerCase()) {
    case 'anthropic':
      return await generateWithAnthropic(params);
    case 'openai':
      return await generateWithOpenAI(params);
    case 'perplexity':
      return await generateWithPerplexity(params);
    default:
      throw new Error(`Unsupported AI provider: ${provider}. Supported providers are: anthropic, openai, perplexity`);
  }
}

export { generateStructuredData };
