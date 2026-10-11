export class GraphEngine {
  constructor() {
    this.nodes = [];
    this.edges = [];
    this.generateDefaultGraph();
  }

  generateDefaultGraph() {
    this.nodes = [
      { id: 'A', label: 'A' },
      { id: 'B', label: 'B' },
      { id: 'C', label: 'C' },
      { id: 'D', label: 'D' },
      { id: 'E', label: 'E' },
      { id: 'F', label: 'F' }
    ];

    this.edges = [
      { from: 'A', to: 'B' },
      { from: 'A', to: 'C' },
      { from: 'B', to: 'D' },
      { from: 'B', to: 'E' },
      { from: 'C', to: 'E' },
      { from: 'C', to: 'F' },
      { from: 'D', to: 'F' },
      { from: 'E', to: 'F' }
    ];
  }

  generateRandomGraph() {
    this.nodes = [
      { id: 'A', label: 'A' },
      { id: 'B', label: 'B' },
      { id: 'C', label: 'C' },
      { id: 'D', label: 'D' },
      { id: 'E', label: 'E' },
      { id: 'F', label: 'F' }
    ];

    this.edges = [];
    // Randomly link nodes with some connectivity assurance
    for (let i = 0; i < this.nodes.length; i++) {
      const from = this.nodes[i].id;
      // force at least one link to prevent isolated nodes
      const targetIdx = (i + 1) % this.nodes.length;
      this.edges.push({ from, to: this.nodes[targetIdx].id });
      
      // Add a random secondary edge
      const randomTarget = Math.floor(Math.random() * this.nodes.length);
      const to = this.nodes[randomTarget].id;
      if (from !== to && !this.edges.some(e => (e.from === from && e.to === to) || (e.from === to && e.to === from))) {
        this.edges.push({ from, to });
      }
    }
  }

  bfs(startId = 'A') {
    const steps = [];
    const visited = new Set();
    const queue = [];
    
    // Initial state
    queue.push(startId);
    visited.add(startId);

    steps.push({
      type: 'bfs_start',
      nodes: this.nodes.map(n => ({
        ...n,
        state: n.id === startId ? 'active' : 'normal'
      })),
      edges: this.edges.map(e => ({ ...e, state: 'normal' })),
      queue: [...queue],
      visited: Array.from(visited),
      highlightedLines: [1, 2, 3],
      explanation: `Initializing BFS at Node ${startId}. Adding to Queue and marking Visited.`,
      complexity: 'O(V + E) Time / O(V) Space',
      pseudocode: this.getPseudocode('bfs')
    });

    while (queue.length > 0) {
      const curr = queue.shift();
      
      // Dequeue step
      steps.push({
        type: 'bfs_dequeue',
        nodes: this.nodes.map(n => ({
          ...n,
          state: n.id === curr ? 'active' : (visited.has(n.id) ? 'highlighted' : 'normal')
        })),
        edges: this.edges.map(e => {
          // Highlight edges already traversed
          const wasTraversed = visited.has(e.from) && visited.has(e.to);
          return { ...e, state: wasTraversed ? 'highlighted' : 'normal' };
        }),
        queue: [...queue],
        visited: Array.from(visited),
        highlightedLines: [4, 5],
        explanation: `Dequeued Node ${curr} from the front of the queue. Processing its neighbors.`,
        complexity: 'O(V + E) Time',
        pseudocode: this.getPseudocode('bfs')
      });

      // Find neighbors
      const neighbors = [];
      for (const edge of this.edges) {
        if (edge.from === curr && !visited.has(edge.to)) neighbors.push({ node: edge.to, edge });
        if (edge.to === curr && !visited.has(edge.from)) neighbors.push({ node: edge.from, edge });
      }

      for (const nbr of neighbors) {
        visited.add(nbr.node);
        queue.push(nbr.node);

        steps.push({
          type: 'bfs_neighbor',
          nodes: this.nodes.map(n => ({
            ...n,
            state: n.id === nbr.node ? 'active' : (n.id === curr ? 'active' : (visited.has(n.id) ? 'highlighted' : 'normal'))
          })),
          edges: this.edges.map(e => {
            if (e === nbr.edge) return { ...e, state: 'active' }; // highlight edge being traversed right now
            const wasTraversed = visited.has(e.from) && visited.has(e.to);
            return { ...e, state: wasTraversed ? 'highlighted' : 'normal' };
          }),
          queue: [...queue],
          visited: Array.from(visited),
          highlightedLines: [6, 7, 8],
          explanation: `Discovered unvisited neighbor Node ${nbr.node}. Traversing edge, adding ${nbr.node} to queue, and marking visited.`,
          complexity: 'O(V + E) Time',
          pseudocode: this.getPseudocode('bfs')
        });
      }
    }

    // Complete state
    steps.push({
      type: 'bfs_complete',
      nodes: this.nodes.map(n => ({ ...n, state: 'highlighted' })),
      edges: this.edges.map(e => ({ ...e, state: 'highlighted' })),
      queue: [],
      visited: Array.from(visited),
      highlightedLines: [9],
      explanation: `BFS complete. Visited nodes in order: [ ${Array.from(visited).join(', ')} ]`,
      complexity: 'O(V + E) Time',
      pseudocode: this.getPseudocode('bfs')
    });

    return steps;
  }

  dfs(startId = 'A') {
    const steps = [];
    const visited = new Set();
    const stack = [];

    // Helper to generate snapshots inside recursive function
    const dfsVisit = (currId, parentId = null, connectingEdge = null) => {
      visited.add(currId);
      stack.push(currId);

      steps.push({
        type: 'dfs_visit',
        nodes: this.nodes.map(n => ({
          ...n,
          state: n.id === currId ? 'active' : (visited.has(n.id) ? 'highlighted' : 'normal')
        })),
        edges: this.edges.map(e => {
          if (e === connectingEdge) return { ...e, state: 'active' };
          const wasTraversed = visited.has(e.from) && visited.has(e.to);
          return { ...e, state: wasTraversed ? 'highlighted' : 'normal' };
        }),
        stack: [...stack],
        visited: Array.from(visited),
        highlightedLines: [1, 2, 3],
        explanation: `Visiting Node ${currId}${parentId ? ` from parent Node ${parentId}` : ''}. Pushing to Recursion Stack.`,
        complexity: 'O(V + E) Time',
        pseudocode: this.getPseudocode('dfs')
      });

      // Find neighbors
      const neighbors = [];
      for (const edge of this.edges) {
        if (edge.from === currId && !visited.has(edge.to)) neighbors.push({ node: edge.to, edge });
        if (edge.to === currId && !visited.has(edge.from)) neighbors.push({ node: edge.from, edge });
      }

      for (const nbr of neighbors) {
        if (!visited.has(nbr.node)) {
          dfsVisit(nbr.node, currId, nbr.edge);
        }
      }

      stack.pop();
      steps.push({
        type: 'dfs_backtrack',
        nodes: this.nodes.map(n => ({
          ...n,
          state: visited.has(n.id) ? 'highlighted' : 'normal'
        })),
        edges: this.edges.map(e => {
          const wasTraversed = visited.has(e.from) && visited.has(e.to);
          return { ...e, state: wasTraversed ? 'highlighted' : 'normal' };
        }),
        stack: [...stack],
        visited: Array.from(visited),
        highlightedLines: [4],
        explanation: `Finished exploring all paths from Node ${currId}. Backtracking...`,
        complexity: 'O(V + E) Time',
        pseudocode: this.getPseudocode('dfs')
      });
    };

    dfsVisit(startId);

    // Complete
    steps.push({
      type: 'dfs_complete',
      nodes: this.nodes.map(n => ({ ...n, state: 'highlighted' })),
      edges: this.edges.map(e => ({ ...e, state: 'highlighted' })),
      stack: [],
      visited: Array.from(visited),
      highlightedLines: [5],
      explanation: `DFS complete. Visited nodes in order: [ ${Array.from(visited).join(', ')} ]`,
      complexity: 'O(V + E) Time',
      pseudocode: this.getPseudocode('dfs')
    });

    return steps;
  }

  getPseudocode(op) {
    if (op === 'bfs') {
      return [
        "function BFS(graph, start):",
        "  queue = [start]",
        "  visited = {start}",
        "  while queue is not empty:",
        "    curr = queue.dequeue()",
        "    for neighbor in graph.neighbors(curr):",
        "      if neighbor not in visited:",
        "        visited.add(neighbor)",
        "        queue.enqueue(neighbor)"
      ];
    } else {
      return [
        "function DFS(graph, node):",
        "  visited.add(node)",
        "  stack.push(node)",
        "  for neighbor in graph.neighbors(node):",
        "    if neighbor not in visited:",
        "      DFS(graph, neighbor)",
        "  stack.pop()"
      ];
    }
  }
}
