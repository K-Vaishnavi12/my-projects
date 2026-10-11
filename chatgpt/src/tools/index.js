import { searchTool } from './search.js';
import { codeExecTool } from './codeExec.js';
import { imageGenTool } from './imageGen.js';
import { logger } from '../utils/logger.js';

const registry = {
  search: searchTool,
  codeExec: codeExecTool,
  imageGen: imageGenTool
};

export const toolRegistry = {
  /**
   * Get all registered tools
   */
  getTools() {
    return Object.values(registry);
  },

  /**
   * Format tool definitions for OpenAI
   */
  getOpenAITools() {
    return Object.values(registry).map(tool => ({
      type: 'function',
      function: tool.definition
    }));
  },

  /**
   * Format tool definitions for Gemini
   */
  getGeminiTools() {
    return Object.values(registry).map(tool => tool.definition);
  },

  /**
   * Format tool definitions for Anthropic
   */
  getAnthropicTools() {
    return Object.values(registry).map(tool => ({
      name: tool.definition.name,
      description: tool.definition.description,
      input_schema: tool.definition.parameters
    }));
  },

  /**
   * Execute a tool by name with arguments
   */
  async executeTool(name, args) {
    const tool = registry[name];
    if (!tool) {
      logger.error(`Attempted to execute unregistered tool: ${name}`);
      return JSON.stringify({ error: `Tool ${name} not found.` });
    }

    try {
      logger.info(`Invoking tool: ${name} with arguments:`, args);
      const parsedArgs = typeof args === 'string' ? JSON.parse(args) : args;
      const result = await tool.execute(parsedArgs);
      logger.debug(`Tool ${name} completed successfully.`);
      return result;
    } catch (err) {
      logger.error(`Error executing tool: ${name}`, err);
      return JSON.stringify({ error: `Execution error in tool ${name}: ${err.message}` });
    }
  }
};
