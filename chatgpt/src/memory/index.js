import fs from 'fs';
import path from 'path';
import { logger } from '../utils/logger.js';

const DATA_DIR = path.resolve('.data/conversations');

// Ensure data directory exists
if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

export const memoryManager = {
  /**
   * Load conversation history from JSON file
   */
  loadConversation(sessionId) {
    const filePath = path.join(DATA_DIR, `${sessionId}.json`);
    try {
      if (fs.existsSync(filePath)) {
        const data = fs.readFileSync(filePath, 'utf-8');
        const parsed = JSON.parse(data);
        logger.debug(`Loaded conversation: ${sessionId} (${parsed.messages.length} messages)`);
        return parsed;
      }
    } catch (err) {
      logger.error(`Failed to load conversation for session: ${sessionId}`, err);
    }
    logger.debug(`Creating new conversation session: ${sessionId}`);
    return { sessionId, messages: [] };
  },

  /**
   * Save conversation history to JSON file
   */
  saveConversation(sessionId, conversation) {
    const filePath = path.join(DATA_DIR, `${sessionId}.json`);
    try {
      fs.writeFileSync(filePath, JSON.stringify(conversation, null, 2), 'utf-8');
      logger.debug(`Saved conversation: ${sessionId}`);
      return true;
    } catch (err) {
      logger.error(`Failed to save conversation for session: ${sessionId}`, err);
      return false;
    }
  },

  /**
   * Add message to session and auto-consolidate
   */
  addMessage(sessionId, role, content, meta = {}) {
    const conversation = this.loadConversation(sessionId);
    const message = {
      role,
      content,
      timestamp: new Date().toISOString(),
      ...meta
    };
    conversation.messages.push(message);
    
    // Auto-prune context window if it gets too long
    this.consolidateMemory(conversation);
    
    this.saveConversation(sessionId, conversation);
    return conversation;
  },

  /**
   * Consolidate memory using Head-Tail pruning (Middle-Out)
   * This retains the system prompt (Head) and the most recent conversations (Tail)
   */
  consolidateMemory(conversation, maxHistoryLimit = 24) {
    // If the conversation is small, do nothing
    if (conversation.messages.length <= maxHistoryLimit) {
      return;
    }

    logger.info(`Consolidating memory for session ${conversation.sessionId}: current size ${conversation.messages.length}`);

    const systemMessages = conversation.messages.filter(msg => msg.role === 'system');
    const nonSystemMessages = conversation.messages.filter(msg => msg.role !== 'system');

    // Keep the last 14 non-system messages
    const tailLimit = maxHistoryLimit - systemMessages.length - 1; // leave room for truncation marker
    const tailMessages = nonSystemMessages.slice(-tailLimit);

    // Form the new message history
    const consolidated = [
      ...systemMessages,
      {
        role: 'system',
        content: `[System Notification: Older messages in this chat session were archived to optimize memory usage and context space.]`,
        timestamp: new Date().toISOString()
      },
      ...tailMessages
    ];

    conversation.messages = consolidated;
    logger.success(`Memory consolidated. New size: ${conversation.messages.length}`);
  },

  /**
   * List all conversation sessions sorted by last modified time
   */
  listConversations() {
    try {
      const files = fs.readdirSync(DATA_DIR).filter(file => file.endsWith('.json'));
      const sessions = files.map(file => {
        const filePath = path.join(DATA_DIR, file);
        const stats = fs.statSync(filePath);
        const content = fs.readFileSync(filePath, 'utf-8');
        const parsed = JSON.parse(content);
        
        // Find first user message for a snippet title, or fallback to sessionId
        const firstUserMsg = parsed.messages.find(msg => msg.role === 'user');
        const title = firstUserMsg 
          ? (firstUserMsg.content.substring(0, 40) + (firstUserMsg.content.length > 40 ? '...' : ''))
          : 'New Conversation';

        return {
          sessionId: file.replace('.json', ''),
          title,
          updatedAt: stats.mtime.toISOString(),
          messageCount: parsed.messages.length
        };
      });

      return sessions.sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
    } catch (err) {
      logger.error('Failed to list conversations', err);
      return [];
    }
  },

  deleteConversation(sessionId) {
    const filePath = path.join(DATA_DIR, `${sessionId}.json`);
    try {
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
        logger.success(`Deleted conversation file for: ${sessionId}`);
        return true;
      }
    } catch (err) {
      logger.error(`Failed to delete conversation: ${sessionId}`, err);
    }
    return false;
  }
};
