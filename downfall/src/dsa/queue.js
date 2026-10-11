export class QueueEngine {
  constructor() {
    this.items = []; // array of { id, value }
    this.counter = 0;
  }

  enqueue(value) {
    const steps = [];
    const newId = `queue_${this.counter++}`;
    const newNode = { id: newId, value };
    const prevItems = [...this.items];

    // Step 0: Spawn node at back
    steps.push({
      type: 'enqueue_spawn',
      items: [...prevItems, { ...newNode, state: 'spawn' }],
      highlightedLines: [1],
      explanation: `Instantiating a new queue node in space with value: ${value}.`,
      complexity: 'O(1) Time / O(1) Space',
      pseudocode: this.getPseudocode('enqueue')
    });

    // Step 1: Slide into queue
    steps.push({
      type: 'enqueue_slide',
      items: [...prevItems, { ...newNode, state: 'active' }],
      highlightedLines: [2, 3],
      explanation: `Linking previous rear node to new node. Moving rear pointer.`,
      complexity: 'O(1) Time / O(1) Space',
      pseudocode: this.getPseudocode('enqueue')
    });

    // Finalize state
    this.items.push(newNode);

    // Step 2: Settled
    steps.push({
      type: 'enqueue_settled',
      items: this.items.map(item => ({ ...item, state: 'normal' })),
      highlightedLines: [4],
      explanation: `Node ${value} is successfully added to the rear of the queue.`,
      complexity: 'O(1) Time',
      pseudocode: this.getPseudocode('enqueue')
    });

    return steps;
  }

  dequeue() {
    const steps = [];
    if (this.items.length === 0) {
      steps.push({
        type: 'dequeue_empty',
        items: [],
        highlightedLines: [1],
        explanation: 'Queue Underflow: The queue is empty. Cannot dequeue.',
        complexity: 'O(1) Time',
        pseudocode: this.getPseudocode('dequeue')
      });
      return steps;
    }

    const dequeuedNode = this.items[0];
    const prevItems = [...this.items];

    // Step 0: Highlight front node
    steps.push({
      type: 'dequeue_highlight',
      items: prevItems.map((item, idx) => ({
        ...item,
        state: idx === 0 ? 'highlighted' : 'normal'
      })),
      highlightedLines: [2],
      explanation: `Locating the front node with value: ${dequeuedNode.value}.`,
      complexity: 'O(1) Time',
      pseudocode: this.getPseudocode('dequeue')
    });

    // Step 1: Slide node out front
    steps.push({
      type: 'dequeue_slide_out',
      items: prevItems.map((item, idx) => ({
        ...item,
        state: idx === 0 ? 'dequeue_slide' : 'normal'
      })),
      highlightedLines: [3, 4],
      explanation: `Redirecting front pointer to front.next. Removing node ${dequeuedNode.value}.`,
      complexity: 'O(1) Time',
      pseudocode: this.getPseudocode('dequeue')
    });

    // Update internal state
    this.items.shift();

    // Step 2: Remaining nodes shift forward
    steps.push({
      type: 'dequeue_settled',
      items: this.items.map(item => ({ ...item, state: 'normal' })),
      highlightedLines: [5],
      explanation: `Queue adjusted. Front node ${dequeuedNode.value} dequeued. Remaining nodes shift forward.`,
      complexity: 'O(1) Time',
      pseudocode: this.getPseudocode('dequeue')
    });

    return steps;
  }

  clear() {
    this.items = [];
    return [{
      type: 'clear',
      items: [],
      highlightedLines: [0],
      explanation: 'Queue cleared.',
      complexity: 'O(1) Time',
      pseudocode: this.getPseudocode('enqueue')
    }];
  }

  getPseudocode(op) {
    if (op === 'enqueue') {
      return [
        "function enqueue(value):",
        "  node = new QueueNode(value)",
        "  if rear is not null: rear.next = node",
        "  rear = node",
        "  if front is null: front = node"
      ];
    } else {
      return [
        "function dequeue():",
        "  if front is null: return UNDERFLOW",
        "  temp = front",
        "  front = front.next",
        "  if front is null: rear = null",
        "  return temp.value"
      ];
    }
  }
}
