import test from 'node:test';
import assert from 'node:assert';
import { providerBridge } from '../src/providers/index.js';
import { OpenAIProvider } from '../src/providers/openai.js';
import { GeminiProvider } from '../src/providers/gemini.js';
import { AnthropicProvider } from '../src/providers/anthropic.js';

test('Provider bridge and mapping tests', async (t) => {

  await t.test('Provider factory should return correct class mappings', () => {
    const gemini = providerBridge.getProvider('gemini-1.5-flash');
    assert.ok(gemini instanceof GeminiProvider);

    const openai = providerBridge.getProvider('gpt-4o-mini');
    assert.ok(openai instanceof OpenAIProvider);

    const anthropic = providerBridge.getProvider('claude-3-5-sonnet-20241022');
    assert.ok(anthropic instanceof AnthropicProvider);
  });

  await t.test('OpenAI Adapter mapping verification', () => {
    const provider = new OpenAIProvider();
    const mockHistory = [
      { role: 'system', content: 'You are helpful.' },
      { role: 'user', content: 'Search this.' },
      {
        role: 'assistant',
        content: '',
        toolCalls: [{ id: 'call_1', name: 'search', args: { query: 'test' } }]
      },
      { role: 'tool', name: 'search', toolCallId: 'call_1', content: 'success' }
    ];

    const mapped = provider.mapMessages(mockHistory);
    assert.strictEqual(mapped.length, 4);
    assert.strictEqual(mapped[0].role, 'system');
    assert.strictEqual(mapped[1].role, 'user');
    
    // Assistant message must map tool calls
    assert.strictEqual(mapped[2].role, 'assistant');
    assert.strictEqual(mapped[2].tool_calls[0].id, 'call_1');
    assert.strictEqual(mapped[2].tool_calls[0].function.name, 'search');
    
    // Tool result message mapping
    assert.strictEqual(mapped[3].role, 'tool');
    assert.strictEqual(mapped[3].tool_call_id, 'call_1');
    assert.strictEqual(mapped[3].content, 'success');
  });

  await t.test('Gemini Adapter mapping verification', () => {
    const provider = new GeminiProvider();
    const mockHistory = [
      { role: 'system', content: 'System instruction.' },
      { role: 'user', content: 'Hello' },
      {
        role: 'assistant',
        content: '',
        toolCalls: [{ id: 'call_1', name: 'search', args: { query: 'gemini' } }]
      },
      { role: 'tool', name: 'search', toolCallId: 'call_1', content: 'success result' }
    ];

    const { systemInstruction, contents } = provider.mapMessages(mockHistory);
    assert.strictEqual(systemInstruction, 'System instruction.');
    
    // system is stripped from contents list
    assert.strictEqual(contents.length, 3);
    assert.strictEqual(contents[0].role, 'user');
    assert.strictEqual(contents[0].parts[0].text, 'Hello');
    
    // Assistant tool calls mapping
    assert.strictEqual(contents[1].role, 'model');
    assert.strictEqual(contents[1].parts[0].functionCall.name, 'search');
    assert.strictEqual(contents[1].parts[0].functionCall.args.query, 'gemini');

    // Tool response mapping
    assert.strictEqual(contents[2].role, 'user');
    assert.strictEqual(contents[2].parts[0].functionResponse.name, 'search');
    assert.strictEqual(contents[2].parts[0].functionResponse.response.result, 'success result');
  });

  await t.test('Anthropic Adapter mapping verification with role merging', () => {
    const provider = new AnthropicProvider();
    const mockHistory = [
      { role: 'system', content: 'Claude prompt.' },
      { role: 'user', content: 'Hello' },
      // Consecutive user messages (or tool results mapped to user role)
      { role: 'tool', name: 'search', toolCallId: 'call_1', content: 'search match' },
      { role: 'user', content: 'Analyze this match.' }
    ];

    const { system, messages } = provider.mapMessages(mockHistory);
    assert.strictEqual(system, 'Claude prompt.');
    
    // Consecutive user roles should be merged into a single user message with multiple content blocks
    assert.strictEqual(messages.length, 1);
    assert.strictEqual(messages[0].role, 'user');
    assert.strictEqual(messages[0].content.length, 3); // 1 text + 1 tool_result + 1 text
    
    assert.strictEqual(messages[0].content[0].text, 'Hello');
    assert.strictEqual(messages[0].content[1].type, 'tool_result');
    assert.strictEqual(messages[0].content[1].content, 'search match');
    assert.strictEqual(messages[0].content[2].text, 'Analyze this match.');
  });
});
