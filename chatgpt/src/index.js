import express from 'express';
import dotenv from 'dotenv';
import path from 'path';
import fs from 'fs';
import { logger } from './utils/logger.js';
import { memoryManager } from './memory/index.js';
import { toolRegistry } from './tools/index.js';
import { providerBridge } from './providers/index.js';

// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static(path.resolve('public')));

const CONFIG_PATH = path.resolve('config/config.json');
const PROMPTS_DIR = path.resolve('config/system_prompts');

// Helper to load configurations
function loadConfig() {
  try {
    if (fs.existsSync(CONFIG_PATH)) {
      return JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'));
    }
  } catch (err) {
    logger.error('Failed to load config file', err);
  }
  return {
    defaultModel: 'llama3:latest',
    activePrompt: 'default',
    temperature: 0.7,
    maxTokens: 4096
  };
}

// Helper to write configurations
function saveConfig(config) {
  try {
    fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2), 'utf-8');
    logger.info('Updated configuration saved.');
    return true;
  } catch (err) {
    logger.error('Failed to save config file', err);
    return false;
  }
}

// API Routes

// 1. Get current configs
app.get('/api/config', (req, res) => {
  const config = loadConfig();
  const models = providerBridge.getSupportedModels();
  
  // Read current system prompt text
  let promptText = '';
  const promptPath = path.join(PROMPTS_DIR, `${config.activePrompt}.txt`);
  if (fs.existsSync(promptPath)) {
    promptText = fs.readFileSync(promptPath, 'utf-8');
  }

  res.json({
    ...config,
    models,
    promptText
  });
});

// 2. Update configs
app.post('/api/config', (req, res) => {
  const { defaultModel, activePrompt, temperature, maxTokens } = req.body;
  const config = loadConfig();

  if (defaultModel) config.defaultModel = defaultModel;
  if (activePrompt) {
    const promptPath = path.join(PROMPTS_DIR, `${activePrompt}.txt`);
    if (!fs.existsSync(promptPath)) {
      return res.status(400).json({ error: `System prompt ${activePrompt} does not exist.` });
    }
    config.activePrompt = activePrompt;
  }
  if (temperature !== undefined) config.temperature = parseFloat(temperature);
  if (maxTokens !== undefined) config.maxTokens = parseInt(maxTokens);

  if (saveConfig(config)) {
    res.json({ success: true, config });
  } else {
    res.status(500).json({ error: 'Failed to write configuration.' });
  }
});

// 3. List available prompts
app.get('/api/prompts', (req, res) => {
  try {
    const files = fs.readdirSync(PROMPTS_DIR).filter(file => file.endsWith('.txt'));
    const prompts = files.map(file => {
      const name = file.replace('.txt', '');
      const content = fs.readFileSync(path.join(PROMPTS_DIR, file), 'utf-8');
      return { name, content };
    });
    res.json(prompts);
  } catch (err) {
    logger.error('Failed to read system prompts', err);
    res.status(500).json({ error: 'Failed to load system prompts.' });
  }
});

// 4. List conversation sessions
app.get('/api/history', (req, res) => {
  const list = memoryManager.listConversations();
  res.json(list);
});

// 5. Get details of a conversation session
app.get('/api/history/:sessionId', (req, res) => {
  const session = memoryManager.loadConversation(req.params.sessionId);
  res.json(session);
});

// 6. Delete a conversation session
app.delete('/api/history/:sessionId', (req, res) => {
  const success = memoryManager.deleteConversation(req.params.sessionId);
  res.json({ success });
});

// 7. Chat endpoint (Server-Sent Events streaming agent loop)
app.post('/api/chat', async (req, res) => {
  let { sessionId, message } = req.body;
  if (!sessionId) {
    sessionId = `session_${Date.now()}`;
  }

  // Setup Server-Sent Events headers
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  const sendEvent = (event, data) => {
    res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
  };

  logger.info(`Starting chat loop for session: ${sessionId}`);

  try {
    // Add user message to history
    if (message) {
      memoryManager.addMessage(sessionId, 'user', message);
    }

    const config = loadConfig();
    
    // Load active system prompt
    let systemPrompt = 'You are a helpful assistant.';
    const promptPath = path.join(PROMPTS_DIR, `${config.activePrompt}.txt`);
    if (fs.existsSync(promptPath)) {
      systemPrompt = fs.readFileSync(promptPath, 'utf-8');
    }

    const maxIterations = 5;
    let iteration = 0;
    let loopRunning = true;

    while (loopRunning && iteration < maxIterations) {
      iteration++;
      logger.info(`Agent loop iteration: ${iteration}/${maxIterations}`);

      // Reload conversation history
      const conversation = memoryManager.loadConversation(sessionId);
      
      // Inject active system prompt at the very beginning of model history
      const fullHistory = [
        { role: 'system', content: systemPrompt },
        ...conversation.messages
      ];

      const provider = providerBridge.getProvider(config.defaultModel);
      // Ollama models don't support function-calling schemas; pass empty tools
      const isOllama = config.defaultModel in { 'llama3:latest': 1, 'llama3.2:3b': 1, 'mistral:latest': 1, 'gemma:2b': 1 };
      const tools = isOllama ? [] : toolRegistry.getOpenAITools();

      // Call LLM for tool detection or final text
      sendEvent('status', { message: 'Thinking...' });
      
      const response = await provider.generate(fullHistory, tools, {
        model: config.defaultModel,
        temperature: config.temperature,
        maxTokens: config.maxTokens
      });

      if (response.toolCalls && response.toolCalls.length) {
        logger.info(`Model requested ${response.toolCalls.length} tool execution(s).`);
        
        // Save assistant's function call message to history
        memoryManager.addMessage(sessionId, 'assistant', response.content || '', {
          toolCalls: response.toolCalls
        });

        // Execute each tool
        for (const tc of response.toolCalls) {
          sendEvent('tool_start', { name: tc.name, args: tc.args, id: tc.id });
          
          const result = await toolRegistry.executeTool(tc.name, tc.args);
          
          sendEvent('tool_end', { name: tc.name, result, id: tc.id });

          // Save tool response message to history
          memoryManager.addMessage(sessionId, 'tool', result, {
            name: tc.name,
            toolCallId: tc.id
          });
        }
        
        // Loop again to give the tool execution output back to the model
      } else {
        // No tool call, model generated text. Let's stream it to the user.
        logger.info('Model returned final text. Initiating stream to user.');
        sendEvent('status', { message: 'Streaming response...' });

        let fullText = '';
        try {
          const stream = provider.stream(fullHistory, {
            model: config.defaultModel,
            temperature: config.temperature,
            maxTokens: config.maxTokens
          });

          for await (const chunk of stream) {
            fullText += chunk;
            sendEvent('token', chunk);
          }
        } catch (streamErr) {
          // If streaming is not supported or failed, fall back to already generated response
          logger.warn('Stream failed or unsupported. Falling back to non-stream text.', streamErr);
          fullText = response.content;
          sendEvent('token', fullText);
        }

        // Save final text message to memory
        memoryManager.addMessage(sessionId, 'assistant', fullText);
        
        sendEvent('complete', { sessionId });
        loopRunning = false;
      }
    }

    if (iteration >= maxIterations) {
      logger.warn('Loop exceeded maximum iterations limit.');
      sendEvent('error', { message: 'Loop limit exceeded. The agent had too many recursive tool steps.' });
    }

  } catch (error) {
    logger.error('Error during chat processing', error);
    sendEvent('error', { message: `Internal error: ${error.message}` });
  } finally {
    res.end();
  }
});

// Start Server
app.listen(PORT, () => {
  logger.success(`Server running at http://localhost:${PORT}`);
});
