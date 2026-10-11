import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import OpenAI from 'openai';
import { logger } from '../utils/logger.js';

const GENERATED_DIR = path.resolve('public/generated_images');

if (!fs.existsSync(GENERATED_DIR)) {
  fs.mkdirSync(GENERATED_DIR, { recursive: true });
}

export const imageGenTool = {
  definition: {
    name: 'imageGen',
    description: 'Generate a highly detailed, creative image from a text prompt and return its local URL.',
    parameters: {
      type: 'object',
      properties: {
        prompt: {
          type: 'string',
          description: 'A detailed, visually rich description of the image to generate.'
        }
      },
      required: ['prompt']
    }
  },

  async execute({ prompt }) {
    logger.info(`Requesting image generation for: "${prompt}"`);
    let sourceUrl = '';
    let isFallback = false;

    // 1. Try OpenAI DALL-E if key is configured
    if (process.env.OPENAI_API_KEY) {
      try {
        logger.debug('Attempting OpenAI DALL-E generation...');
        const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
        const response = await openai.images.generate({
          model: 'dall-e-3',
          prompt: prompt,
          n: 1,
          size: '1024x1024',
          response_format: 'url'
        });
        if (response.data && response.data[0] && response.data[0].url) {
          sourceUrl = response.data[0].url;
          logger.success('OpenAI DALL-E generated image successfully');
        }
      } catch (err) {
        logger.error('OpenAI DALL-E generation failed, falling back to free generator...', err);
      }
    }

    // 2. Fall back to Pollinations AI (free, reliable, high quality generator)
    if (!sourceUrl) {
      isFallback = true;
      const seed = Math.floor(Math.random() * 1000000);
      sourceUrl = `https://image.pollinations.ai/prompt/${encodeURIComponent(prompt)}?width=1024&height=1024&seed=${seed}&nologo=true&private=true`;
      logger.info('Using Pollinations AI fallback image generator url: ' + sourceUrl);
    }

    // 3. Download and cache the image locally so the link doesn't expire (especially OpenAI DALL-E links expire in 1 hour)
    try {
      logger.debug(`Downloading image from source: ${sourceUrl.substring(0, 100)}...`);
      const response = await fetch(sourceUrl);
      if (!response.ok) {
        throw new Error(`Failed to fetch image from source: ${response.statusText}`);
      }
      const arrayBuffer = await response.arrayBuffer();
      const buffer = Buffer.from(arrayBuffer);

      const fileId = crypto.randomBytes(8).toString('hex');
      const filename = `image_${fileId}.png`;
      const filepath = path.join(GENERATED_DIR, filename);

      fs.writeFileSync(filepath, buffer);
      const relativeUrl = `/generated_images/${filename}`;
      logger.success(`Image saved locally to ${relativeUrl}`);

      return JSON.stringify({
        success: true,
        prompt,
        url: relativeUrl,
        provider: isFallback ? 'Pollinations' : 'DALL-E 3',
        cached: true
      });
    } catch (error) {
      logger.error('Failed to fetch image online, generating fallback vector SVG', error);
      
      try {
        const fileId = crypto.randomBytes(8).toString('hex');
        const filename = `image_${fileId}.svg`;
        const filepath = path.join(GENERATED_DIR, filename);
        
        // Generate beautiful neon vector SVG
        const svgContent = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" width="1024" height="1024">
          <defs>
            <linearGradient id="bg-grad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#0b0b0f" />
              <stop offset="50%" stop-color="#1e1b4b" />
              <stop offset="100%" stop-color="#4c1d95" />
            </linearGradient>
            <linearGradient id="text-grad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#a78bfa" />
              <stop offset="100%" stop-color="#ec4899" />
            </linearGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="15" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
          <rect width="1024" height="1024" fill="url(#bg-grad)" />
          <path d="M0 128 H1024 M0 256 H1024 M0 384 H1024 M0 512 H1024 M0 640 H1024 M0 768 H1024 M0 896 H1024" stroke="rgba(255,255,255,0.02)" stroke-width="2" />
          <path d="M128 0 V1024 M256 0 V1024 M384 0 V1024 M512 0 V1024 M640 0 V1024 M768 0 V1024 M896 0 V1024" stroke="rgba(255,255,255,0.02)" stroke-width="2" />
          
          <circle cx="512" cy="400" r="180" fill="none" stroke="#8b5cf6" stroke-width="4" filter="url(#glow)" opacity="0.6" />
          <circle cx="512" cy="400" r="220" fill="none" stroke="#ec4899" stroke-width="2" filter="url(#glow)" opacity="0.4" />
          
          <g transform="translate(448, 320) scale(1.5)">
            <path d="M40 0 C45 15 50 35 45 55 C40 70 30 85 10 90 C-10 95 -25 80 -30 60 C-35 40 -30 20 -20 5" fill="none" stroke="#f59e0b" stroke-width="12" stroke-linecap="round" filter="url(#glow)" />
            <path d="M40 0 C45 15 50 35 45 55 C40 70 30 85 10 90 C-10 95 -25 80 -30 60 C-35 40 -30 20 -20 5" fill="none" stroke="#fbbf24" stroke-width="6" stroke-linecap="round" />
          </g>
          
          <rect x="112" y="680" width="800" height="180" rx="20" fill="rgba(0, 0, 0, 0.6)" stroke="rgba(255, 255, 255, 0.1)" stroke-width="2" />
          <text x="512" y="745" font-family="'Outfit', sans-serif" font-size="28" font-weight="800" fill="url(#text-grad)" text-anchor="middle">NEURAL CANVAS FALLBACK</text>
          <text x="512" y="805" font-family="'Inter', sans-serif" font-size="20" font-weight="500" fill="#e4e4e7" text-anchor="middle">Prompt: "${prompt.replace(/"/g, '&quot;')}"</text>
        </svg>`;
        
        fs.writeFileSync(filepath, svgContent, 'utf-8');
        const relativeUrl = `/generated_images/${filename}`;
        logger.success(`Image generation fallback generated locally at ${relativeUrl}`);
        
        return JSON.stringify({
          success: true,
          prompt,
          url: relativeUrl,
          provider: 'Harness Vector Gen',
          cached: true,
          fallback: true
        });
      } catch (innerErr) {
        logger.error('Failed to write fallback SVG', innerErr);
        return JSON.stringify({
          success: false,
          error: `Image generation and local SVG rendering failed: ${error.message}`,
          prompt
        });
      }
    }
  }
};
