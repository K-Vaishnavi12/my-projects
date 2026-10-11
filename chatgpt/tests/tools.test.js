import test from 'node:test';
import assert from 'node:assert';
import { searchTool } from '../src/tools/search.js';
import { codeExecTool } from '../src/tools/codeExec.js';
import { imageGenTool } from '../src/tools/imageGen.js';

test('Tool Registry & Execution tests', async (t) => {

  await t.test('Search tool definitions', () => {
    assert.strictEqual(searchTool.definition.name, 'search');
    assert.ok(searchTool.definition.parameters.properties.query);
  });

  await t.test('Image generation tool definitions', () => {
    assert.strictEqual(imageGenTool.definition.name, 'imageGen');
    assert.ok(imageGenTool.definition.parameters.properties.prompt);
  });

  await t.test('Code execution tool definition', () => {
    assert.strictEqual(codeExecTool.definition.name, 'codeExec');
    assert.deepStrictEqual(
      codeExecTool.definition.parameters.properties.language.enum,
      ['javascript', 'python']
    );
  });

  await t.test('codeExec should execute javascript successfully', async () => {
    const resultStr = await codeExecTool.execute({
      language: 'javascript',
      code: 'console.log("hello" + " world");'
    });
    
    const result = JSON.parse(resultStr);
    assert.strictEqual(result.success, true);
    assert.strictEqual(result.exitCode, 0);
    assert.strictEqual(result.stdout, 'hello world');
  });

  await t.test('codeExec should execute python successfully', async () => {
    const resultStr = await codeExecTool.execute({
      language: 'python',
      code: 'print("hello from python")'
    });

    const result = JSON.parse(resultStr);
    assert.strictEqual(result.success, true);
    assert.strictEqual(result.exitCode, 0);
    assert.strictEqual(result.stdout, 'hello from python');
  });

  await t.test('codeExec should handle infinite loop timeouts safely', async () => {
    const start = Date.now();
    const resultStr = await codeExecTool.execute({
      language: 'javascript',
      code: 'while(true) {}'
    });
    const duration = Date.now() - start;

    const result = JSON.parse(resultStr);
    assert.strictEqual(result.success, false);
    assert.ok(result.error.includes('timed out'));
    // Ensure timeout interrupted it in ~5s
    assert.ok(duration >= 4800 && duration < 6500, `Duration was: ${duration}`);
  });

  await t.test('codeExec should return exit code error for invalid scripts', async () => {
    const resultStr = await codeExecTool.execute({
      language: 'javascript',
      code: 'throw new Error("Syntax Error Test");'
    });

    const result = JSON.parse(resultStr);
    assert.strictEqual(result.success, false);
    assert.ok(result.exitCode !== 0);
    assert.ok(result.stderr.includes('Syntax Error Test'));
  });

  await t.test('imageGen should return local cached path for pollinations fallback', async () => {
    const resultStr = await imageGenTool.execute({
      prompt: 'a cute cyber monkey eating a banana'
    });

    const result = JSON.parse(resultStr);
    assert.strictEqual(result.success, true);
    assert.ok(result.url.startsWith('/generated_images/'));
    assert.ok(result.provider === 'Pollinations' || result.provider === 'Harness Vector Gen');
  });
});
