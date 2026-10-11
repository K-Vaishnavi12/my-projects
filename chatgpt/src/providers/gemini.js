import { GoogleGenerativeAI } from '@google/generative-ai';
import { logger } from '../utils/logger.js';

export class GeminiProvider {
  constructor() {
    this.apiKey = process.env.GEMINI_API_KEY || '';
    this.genAI = this.apiKey ? new GoogleGenerativeAI(this.apiKey) : null;
  }

  /**
   * Separate system instruction and map remaining messages to Gemini content format
   */
  mapMessages(messages) {
    let systemInstruction = '';
    const contents = [];

    for (const msg of messages) {
      if (msg.role === 'system') {
        // Collect system prompts
        systemInstruction += (systemInstruction ? '\n' : '') + msg.content;
        continue;
      }

      if (msg.role === 'user') {
        contents.push({
          role: 'user',
          parts: [{ text: msg.content }]
        });
      } else if (msg.role === 'assistant') {
        const parts = [];
        if (msg.content) {
          parts.push({ text: msg.content });
        }
        if (msg.toolCalls && msg.toolCalls.length) {
          msg.toolCalls.forEach(tc => {
            parts.push({
              functionCall: {
                name: tc.name,
                args: typeof tc.args === 'string' ? JSON.parse(tc.args) : tc.args
              }
            });
          });
        }
        contents.push({
          role: 'model',
          parts
        });
      } else if (msg.role === 'tool') {
        contents.push({
          role: 'user',
          parts: [{
            functionResponse: {
              name: msg.name,
              response: { result: msg.content }
            }
          }]
        });
      }
    }

    return { systemInstruction, contents };
  }

  /**
   * Generate completion
   */
  async generate(messages, tools, options = {}) {
    logger.info('Calling Gemini model generation...');
    if (!this.genAI) {
      throw new Error('GEMINI_API_KEY is not configured in environment.');
    }

    const { systemInstruction, contents } = this.mapMessages(messages);
    const modelName = options.model || 'gemini-2.0-flash';

    // Format tools if provided
    const toolDeclarations = tools && tools.length 
      ? [{ functionDeclarations: tools }]
      : undefined;

    try {
      const model = this.genAI.getGenerativeModel({
        model: modelName,
        systemInstruction: systemInstruction || undefined,
        tools: toolDeclarations
      });

      const response = await model.generateContent({
        contents,
        generationConfig: {
          temperature: options.temperature ?? 0.7,
          maxOutputTokens: options.maxTokens ?? 4096
        }
      });

      const responseText = response.response.text();
      const functionCalls = response.response.functionCalls;

      const result = {
        content: responseText || '',
        toolCalls: null
      };

      if (functionCalls && functionCalls.length) {
        result.toolCalls = functionCalls.map((fc, index) => ({
          id: `gemini-call-${Date.now()}-${index}`,
          name: fc.name,
          args: fc.args
        }));
      }

      logger.success('Gemini call succeeded');
      return result;
    } catch (err) {
      // In some SDK versions, calling .text() on tool calls throws an error. Let's catch it.
      if (err.message && err.message.includes('FunctionCall')) {
        try {
          const model = this.genAI.getGenerativeModel({ model: modelName });
          const response = await model.generateContent({ contents, tools: toolDeclarations });
          const functionCalls = response.response.functionCalls;
          if (functionCalls && functionCalls.length) {
            logger.success('Gemini call succeeded (function call content only)');
            return {
              content: '',
              toolCalls: functionCalls.map((fc, index) => ({
                id: `gemini-call-${Date.now()}-${index}`,
                name: fc.name,
                args: fc.args
              }))
            };
          }
        } catch (innerErr) {
          logger.error('Gemini retry failed', innerErr);
        }
      }
      logger.error('Gemini call failed', err);
      throw err;
    }
  }

  /**
   * Stream content (text only)
   */
  async *stream(messages, options = {}) {
    if (!this.genAI) {
      throw new Error('GEMINI_API_KEY is not configured in environment.');
    }
    const { systemInstruction, contents } = this.mapMessages(messages);
    const modelName = options.model || 'gemini-2.0-flash';

    try {
      const model = this.genAI.getGenerativeModel({
        model: modelName,
        systemInstruction: systemInstruction || undefined
      });

      const result = await model.generateContentStream({
        contents,
        generationConfig: {
          temperature: options.temperature ?? 0.7,
          maxOutputTokens: options.maxTokens ?? 4096
        }
      });

      for await (const chunk of result.stream) {
        const text = chunk.text();
        if (text) yield text;
      }
    } catch (err) {
      logger.error('Gemini streaming failed', err);
      throw err;
    }
  }
}
