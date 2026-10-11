import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { logger } from '../utils/logger.js';

const TEMP_DIR = path.resolve('temp_run');

if (!fs.existsSync(TEMP_DIR)) {
  fs.mkdirSync(TEMP_DIR, { recursive: true });
}

export const codeExecTool = {
  definition: {
    name: 'codeExec',
    description: 'Execute arbitrary JavaScript or Python code locally and return stdout/stderr.',
    parameters: {
      type: 'object',
      properties: {
        language: {
          type: 'string',
          enum: ['javascript', 'python'],
          description: 'The programming language of the code to run.'
        },
        code: {
          type: 'string',
          description: 'The code to execute. Output must be printed to console (stdout) to be captured.'
        }
      },
      required: ['language', 'code']
    }
  },

  async execute({ language, code }) {
    logger.info(`Executing ${language} script...`);
    const fileId = crypto.randomBytes(8).toString('hex');
    const ext = language === 'javascript' ? 'js' : 'py';
    const filepath = path.join(TEMP_DIR, `script_${fileId}.${ext}`);

    try {
      fs.writeFileSync(filepath, code, 'utf-8');

      const cmd = language === 'javascript' ? 'node' : 'python';
      const args = [filepath];

      return await new Promise((resolve) => {
        logger.debug(`Spawning subprocess: ${cmd} ${filepath}`);
        const child = spawn(cmd, args, {
          env: {}, // Strip environment variables for basic safety
          timeout: 5000 // Subprocess timeout at OS level if supported
        });

        let stdout = '';
        let stderr = '';
        let killed = false;

        // Backup timeout logic
        const timer = setTimeout(() => {
          killed = true;
          child.kill('SIGKILL');
          logger.warn(`Subprocess for ${language} timed out after 5000ms`);
        }, 5000);

        child.stdout.on('data', (data) => {
          stdout += data.toString();
        });

        child.stderr.on('data', (data) => {
          stderr += data.toString();
        });

        child.on('error', (err) => {
          clearTimeout(timer);
          logger.error(`Subprocess execution failed`, err);
          resolve(JSON.stringify({
            success: false,
            error: `Failed to start process: ${err.message}`,
            stdout: stdout.trim(),
            stderr: stderr.trim()
          }));
        });

        child.on('exit', (code, signal) => {
          clearTimeout(timer);
          if (killed || signal === 'SIGKILL') {
            resolve(JSON.stringify({
              success: false,
              error: 'Execution timed out (maximum 5 seconds allowed).',
              stdout: stdout.trim(),
              stderr: stderr.trim()
            }));
          } else {
            logger.success(`Code execution finished with exit code: ${code}`);
            resolve(JSON.stringify({
              success: code === 0,
              exitCode: code,
              stdout: stdout.trim(),
              stderr: stderr.trim()
            }));
          }
        });
      });
    } catch (err) {
      logger.error('Error setting up code execution', err);
      return JSON.stringify({
        success: false,
        error: `Setup failed: ${err.message}`,
        stdout: '',
        stderr: ''
      });
    } finally {
      // Clean up the temporary file
      try {
        if (fs.existsSync(filepath)) {
          fs.unlinkSync(filepath);
        }
      } catch (err) {
        logger.error(`Failed to clean up temp file: ${filepath}`, err);
      }
    }
  }
};
