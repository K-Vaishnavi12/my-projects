import { logger } from '../utils/logger.js';

const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';

export class OllamaProvider {
  /**
   * Map internal messages to Ollama (OpenAI-compatible) message format.
   * Ollama does not support tool_calls natively in the same way, so we
   * convert tool results into plain user messages for context injection.
   */
  mapMessages(messages) {
    const mapped = [];

    for (const msg of messages) {
      if (msg.role === 'tool') {
        // Inject tool result as a user message so the model sees it
        mapped.push({
          role: 'user',
          content: `Tool "${msg.name}" returned:\n${msg.content}`
        });
      } else if (msg.role === 'assistant' && msg.toolCalls) {
        // Represent tool call intent as plain assistant text
        const callDesc = msg.toolCalls
          .map(tc => `[Calling tool: ${tc.name} with args: ${JSON.stringify(tc.args)}]`)
          .join('\n');
        mapped.push({
          role: 'assistant',
          content: (msg.content ? msg.content + '\n' : '') + callDesc
        });
      } else {
        mapped.push({
          role: msg.role,
          content: msg.content
        });
      }
    }

    // Ollama requires messages to start with a user message (not system).
    // system role is supported as the first message only.
    return mapped;
  }

  /**
   * Generate a non-streaming response from Ollama.
   * Returns { content, toolCalls: null } — Ollama models don't do native tool calls,
   * so the agent loop will always go straight to streaming.
   */
  async generate(messages, tools, options = {}) {
    logger.info('Calling Ollama model generation...');
    const mapped = this.mapMessages(messages);
    const model = options.model || 'llama3:latest';

    try {
      const response = await fetch(`${OLLAMA_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model,
          messages: mapped,
          stream: false,
          options: {
            temperature: options.temperature ?? 0.7,
            num_predict: options.maxTokens ?? 2048
          }
        })
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`Ollama API error ${response.status}: ${text}`);
      }

      const data = await response.json();
      const content = data.message?.content || '';

      logger.success('Ollama call succeeded');
      return { content, toolCalls: null };
    } catch (err) {
      logger.error('Ollama generate failed', err);
      throw err;
    }
  }

  /**
   * Stream tokens from Ollama using NDJSON streaming.
   */
  async *stream(messages, options = {}) {
    const mapped = this.mapMessages(messages);
    const model = options.model || 'llama3:latest';

    try {
      const response = await fetch(`${OLLAMA_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model,
          messages: mapped,
          stream: true,
          options: {
            temperature: options.temperature ?? 0.7,
            num_predict: options.maxTokens ?? 2048
          }
        })
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`Ollama streaming error ${response.status}: ${text}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // keep incomplete last line

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const json = JSON.parse(line);
            const token = json.message?.content;
            if (token) yield token;
          } catch {
            // skip malformed lines
          }
        }
      }

      // flush remaining buffer
      if (buffer.trim()) {
        try {
          const json = JSON.parse(buffer);
          const token = json.message?.content;
          if (token) yield token;
        } catch {
          // ignore
        }
      }
    } catch (err) {
      logger.error('Ollama streaming failed', err);
      throw err;
    }
  }
}
