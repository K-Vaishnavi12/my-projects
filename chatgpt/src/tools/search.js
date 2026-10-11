import { logger } from '../utils/logger.js';

export const searchTool = {
  definition: {
    name: 'search',
    description: 'Search the web for real-time information, news, current events, and documentation.',
    parameters: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'The search query to look up.'
        }
      },
      required: ['query']
    }
  },

  async execute({ query }) {
    logger.info(`Executing web search for: "${query}"`);
    try {
      const url = `https://html.duckduckgo.com/html/?q=${encodeURIComponent(query)}`;
      const response = await fetch(url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const html = await response.text();
      
      // Parse results using regex to keep it dependency-free
      const results = [];
      const resultBlocks = html.match(/<div class="[^"]*result__body[^"]*">([\s\S]*?)<\/div>/g);

      if (resultBlocks) {
        for (const block of resultBlocks.slice(0, 5)) {
          // Extract link and title
          const titleMatch = block.match(/<a class="[^"]*result__url[^"]*" href="([^"]*)"[^>]*>([\s\S]*?)<\/a>/);
          // Extract snippet
          const snippetMatch = block.match(/<a class="[^"]*result__snippet[^"]*"[^>]*>([\s\S]*?)<\/a>/);

          if (titleMatch) {
            let url = titleMatch[1];
            // DuckDuckGo redirects urls, parse the real url if needed, e.g. /l/?kh=-1&uddg=HTTPS_URL
            if (url.includes('uddg=')) {
              const parts = url.split('uddg=');
              if (parts[1]) {
                url = decodeURIComponent(parts[1].split('&')[0]);
              }
            }

            const title = titleMatch[2].replace(/<[^>]*>/g, '').trim();
            const snippet = snippetMatch ? snippetMatch[1].replace(/<[^>]*>/g, '').trim() : '';

            results.push({ title, url, snippet });
          }
        }
      }

      if (results.length === 0) {
        // Fallback simple regex just in case page structure slightly differs
        const genericLinkRegex = /<a href="([^"]+)" class="result__snippet">([^<]+)<\/a>/g;
        let match;
        let count = 0;
        while ((match = genericLinkRegex.exec(html)) !== null && count < 5) {
          results.push({
            title: 'Search Result',
            url: match[1],
            snippet: match[2].trim()
          });
          count++;
        }
      }

      if (results.length === 0) {
        logger.warn(`Search returned zero results for: "${query}" (might be rate-limited/blocked)`);
        return JSON.stringify({
          query,
          error: 'No results found. The search engine might be temporarily rate-limiting requests.',
          results: []
        });
      }

      logger.success(`Search successful. Found ${results.length} results.`);
      return JSON.stringify({ query, results });
    } catch (error) {
      logger.error(`Search execution failed for query: "${query}"`, error);
      return JSON.stringify({
        query,
        error: `Failed to perform search: ${error.message}`,
        results: []
      });
    }
  }
};
