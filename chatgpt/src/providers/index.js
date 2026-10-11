import { GeminiProvider } from './gemini.js';
import { OpenAIProvider } from './openai.js';
import { AnthropicProvider } from './anthropic.js';
import { OllamaProvider } from './ollama.js';
import { logger } from '../utils/logger.js';

const providerCache = {
  gemini: null,
  openai: null,
  anthropic: null,
  ollama: null
};

// Map model names to their respective provider types
const modelToProviderMap = {
  // Google Gemini models
  'gemini-2.0-flash': 'gemini',
  'gemini-1.5-flash': 'gemini',
  'gemini-1.5-pro': 'gemini',
  
  // OpenAI models
  'gpt-4o-mini': 'openai',
  'gpt-4o': 'openai',
  'gpt-3.5-turbo': 'openai',
  
  // Anthropic models
  'claude-3-5-sonnet-20241022': 'anthropic',
  'claude-3-haiku-20240307': 'anthropic',

  // Ollama local models
  'llama3:latest': 'ollama',
  'llama3.2:3b': 'ollama',
  'mistral:latest': 'ollama',
  'gemma:2b': 'ollama'
};

export const providerBridge = {
  /**
   * Resolve provider instance for a model name
   */
  getProvider(modelName) {
    const providerType = modelToProviderMap[modelName];
    if (!providerType) {
      logger.warn(`Unknown model "${modelName}", defaulting to OpenAI provider`);
      return this._getOrCreateProvider('openai');
    }
    return this._getOrCreateProvider(providerType);
  },

  /**
   * Get list of all supported models
   */
  getSupportedModels() {
    return Object.keys(modelToProviderMap);
  },

  /**
   * Internal lazy initializer
   */
  _getOrCreateProvider(type) {
    if (providerCache[type]) {
      return providerCache[type];
    }

    logger.debug(`Initializing model provider of type: ${type}`);
    switch (type) {
      case 'gemini':
        providerCache[type] = new GeminiProvider();
        break;
      case 'openai':
        providerCache[type] = new OpenAIProvider();
        break;
      case 'anthropic':
        providerCache[type] = new AnthropicProvider();
        break;
      case 'ollama':
        providerCache[type] = new OllamaProvider();
        break;
      default:
        throw new Error(`Unsupported provider type: ${type}`);
    }

    return providerCache[type];
  }
};
