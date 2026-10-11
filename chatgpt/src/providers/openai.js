import OpenAI from 'openai';
import { logger } from '../utils/logger.js';

export class OpenAIProvider {
  constructor() {
    this.client = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY || 'dummy-key'
    });
  }

  /**
   * Map internal messages to OpenAI API message format
   */
  mapMessages(messages) {
    return messages.map(msg => {
      if (msg.role === 'tool') {
        return {
          role: 'tool',
          tool_call_id: msg.toolCallId,
          content: msg.content
        };
      }
      if (msg.role === 'assistant' && msg.toolCalls) {
        return {
          role: 'assistant',
          content: msg.content || null,
          tool_calls: msg.toolCalls.map(tc => ({
            id: tc.id,
            type: 'function',
            function: {
              name: tc.name,
              arguments: typeof tc.args === 'string' ? tc.args : JSON.stringify(tc.args)
            }
          }))
        };
      }
      return {
        role: msg.role,
        content: msg.content
      };
    });
  }

  /**
   * Generate response from OpenAI
   */
  async generate(messages, tools, options = {}) {
    logger.info('Calling OpenAI model generation...');
    const mapped = this.mapMessages(messages);
    const formattedTools = tools && tools.length ? tools : undefined;

    try {
      const response = await this.client.chat.completions.create({
        model: options.model || 'gpt-4o-mini',
        messages: mapped,
        tools: formattedTools,
        temperature: options.temperature ?? 0.7,
        max_tokens: options.maxTokens ?? 2048
      });

      const choice = response.choices[0];
      const result = {
        content: choice.message.content || '',
        toolCalls: null
      };

      if (choice.message.tool_calls && choice.message.tool_calls.length) {
        result.toolCalls = choice.message.tool_calls.map(tc => ({
          id: tc.id,
          name: tc.function.name,
          args: JSON.parse(tc.function.arguments)
        }));
      }

      logger.success('OpenAI call succeeded');
      return result;
    } catch (err) {
      logger.error('OpenAI call failed', err);
      throw err;
    }
  }

  /**
   * Stream completions from OpenAI (for text only, tools are executed non-streamed for simplicity)
   */
  async *stream(messages, options = {}) {
    const mapped = this.mapMessages(messages);
    try {
      const response = await this.client.chat.completions.create({
        model: options.model || 'gpt-4o-mini',
        messages: mapped,
        temperature: options.temperature ?? 0.7,
        max_tokens: options.maxTokens ?? 2048,
        stream: true
      });

      for await (const chunk of response) {
        const text = chunk.choices[0]?.delta?.content || '';
        if (text) yield text;
      }
    } catch (err) {
      logger.error('OpenAI streaming failed', err);
      throw err;
    }
  }
}
