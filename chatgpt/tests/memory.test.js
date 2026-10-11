import test from 'node:test';
import assert from 'node:assert';
import fs from 'fs';
import path from 'path';
import { memoryManager } from '../src/memory/index.js';

test('Memory Manager tests', async (t) => {
  const testSessionId = `test_session_${Date.now()}`;

  await t.test('should load empty conversation for new session', () => {
    const conv = memoryManager.loadConversation(testSessionId);
    assert.strictEqual(conv.sessionId, testSessionId);
    assert.deepStrictEqual(conv.messages, []);
  });

  await t.test('should save and load conversation', () => {
    const conv = {
      sessionId: testSessionId,
      messages: [
        { role: 'user', content: 'Hello assistant' },
        { role: 'assistant', content: 'Hello human!' }
      ]
    };
    const saved = memoryManager.saveConversation(testSessionId, conv);
    assert.strictEqual(saved, true);

    const loaded = memoryManager.loadConversation(testSessionId);
    assert.strictEqual(loaded.sessionId, testSessionId);
    assert.strictEqual(loaded.messages.length, 2);
    assert.strictEqual(loaded.messages[0].content, 'Hello assistant');
  });

  await t.test('should list conversation sessions', () => {
    const list = memoryManager.listConversations();
    const session = list.find(s => s.sessionId === testSessionId);
    assert.ok(session);
    assert.strictEqual(session.messageCount, 2);
  });

  await t.test('should consolidate memory if history gets too long', () => {
    const longConv = {
      sessionId: testSessionId,
      messages: [
        { role: 'system', content: 'Act as a cat.' },
        // Create 30 user-assistant turns
        ...Array.from({ length: 30 }, (_, i) => ({
          role: i % 2 === 0 ? 'user' : 'assistant',
          content: `Message ${i}`
        }))
      ]
    };

    // Before consolidation
    assert.strictEqual(longConv.messages.length, 31);

    // Trigger memory consolidation with a limit of 24
    memoryManager.consolidateMemory(longConv, 24);

    // After consolidation
    assert.ok(longConv.messages.length <= 24);
    assert.strictEqual(longConv.messages[0].role, 'system');
    assert.strictEqual(longConv.messages[0].content, 'Act as a cat.');
    assert.strictEqual(longConv.messages[1].role, 'system');
    assert.ok(longConv.messages[1].content.includes('System Notification'));
    
    // Tail should be intact (the last message is "Message 29")
    assert.strictEqual(longConv.messages[longConv.messages.length - 1].content, 'Message 29');
  });

  await t.test('should delete conversation session', () => {
    const success = memoryManager.deleteConversation(testSessionId);
    assert.strictEqual(success, true);

    const loaded = memoryManager.loadConversation(testSessionId);
    assert.deepStrictEqual(loaded.messages, []);
  });
});
