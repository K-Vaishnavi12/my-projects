import Anthropic from '@anthropic-ai/sdk';
import { logger } from '../utils/logger.js';

export class AnthropicProvider {
  constructor() {
    this.client = new Anthropic({
      apiKey: process.env.ANTHROPIC_API_KEY || 'dummy-key'
    });
  }

  /**
   * Map internal messages to Anthropic strict user/assistant alternating format
   */
  mapMessages(messages) {
    let system = '';
    const rawMapped = [];

    for (const msg of messages) {
      if (msg.role === 'system') {
        system += (system ? '\n' : '') + msg.content;
        continue;
      }

      if (msg.role === 'user') {
        rawMapped.push({
          role: 'user',
          content: msg.content
        });
      } else if (msg.role === 'assistant') {
        const contentBlocks = [];
        if (msg.content) {
          contentBlocks.push({ type: 'text', text: msg.content });
        }
        if (msg.toolCalls && msg.toolCalls.length) {
          msg.toolCalls.forEach(tc => {
            contentBlocks.push({
              type: 'tool_use',
              id: tc.id,
              name: tc.name,
              input: typeof tc.args === 'string' ? JSON.parse(tc.args) : tc.args
            });
          });
        }
        // If contentBlocks is empty (should not happen normally but as fallback)
        rawMapped.push({
          role: 'assistant',
          content: contentBlocks.length ? contentBlocks : [{ type: 'text', text: '' }]
        });
      } else if (msg.role === 'tool') {
        rawMapped.push({
          role: 'user',
          content: [{
            type: 'tool_result',
            tool_use_id: msg.toolCallId,
            content: msg.content
          }]
        });
      }
    }

    // Merge consecutive roles into single message content blocks
    const alternating = [];
    for (const msg of rawMapped) {
      if (alternating.length > 0 && alternating[alternating.length - 1].role === msg.role) {
        const lastMsg = alternating[alternating.length - 1];
        
        // Convert both contents to arrays of blocks if they aren't already
        const lastBlocks = Array.isArray(lastMsg.content) 
          ? lastMsg.content 
          : [{ type: 'text', text: lastMsg.content }];
          
        const currentBlocks = Array.isArray(msg.content)
          ? msg.content
          : [{ type: 'text', text: msg.content }];

        lastMsg.content = [...lastBlocks, ...currentBlocks];
      } else {
        alternating.push(msg);
      }
    }

    return { system, messages: alternating };
  }

  /**
   * Generate content
   */
  async generate(messages, tools, options = {}) {
    logger.info('Calling Anthropic model generation...');
    const { system, messages: mappedMessages } = this.mapMessages(messages);
    const modelName = options.model || 'claude-3-5-sonnet-20241022';

    // Format tools for Anthropic
    const formattedTools = tools && tools.length ? tools : undefined;

    try {
      const response = await this.client.messages.create({
        model: modelName,
        system: system || undefined,
        messages: mappedMessages,
        tools: formattedTools,
        max_tokens: options.maxTokens ?? 2048,
        temperature: options.temperature ?? 0.7
      });

      const result = {
        content: '',
        toolCalls: null
      };

      const toolCalls = [];

      response.content.forEach(block => {
        if (block.type === 'text') {
          result.content += block.text;
        } else if (block.type === 'tool_use') {
          toolCalls.push({
            id: block.id,
            name: block.name,
            args: block.input
          });
        }
      });

      if (toolCalls.length) {
        result.toolCalls = toolCalls;
      }

      logger.success('Anthropic call succeeded');
      return result;
    } catch (err) {
      logger.error('Anthropic call failed', err);
      throw err;
    }
  }

  /**
   * Stream content (text only)
   */
  async *stream(messages, options = {}) {
    const { system, messages: mappedMessages } = this.mapMessages(messages);
    const modelName = options.model || 'claude-3-5-sonnet-20241022';

    try {
      const response = await this.client.messages.create({
        model: modelName,
        system: system || undefined,
        messages: mappedMessages,
        max_tokens: options.maxTokens ?? 2048,
        temperature: options.temperature ?? 0.7,
        stream: true
      });

      for await (const chunk of response) {
        if (chunk.type === 'content_block_delta' && chunk.delta?.text) {
          yield chunk.delta.text;
        }
      }
    } catch (err) {
      logger.error('Anthropic streaming failed', err);
      throw err;
    }
  }
}
