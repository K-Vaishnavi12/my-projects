export class StackEngine {
  constructor() {
    this.items = []; // array of { id, value }
    this.counter = 0;
  }

  push(value) {
    const steps = [];
    const newId = `stack_${this.counter++}`;
    const newNode = { id: newId, value };
    const prevItems = [...this.items];

    // Step 0: Spawn node above
    steps.push({
      type: 'push_spawn',
      items: [...prevItems, { ...newNode, state: 'spawn' }],
      highlightedLines: [1],
      explanation: `Instantiating a new stack node in space with value: ${value}.`,
      complexity: 'O(1) Time / O(1) Space',
      pseudocode: this.getPseudocode('push')
    });

    // Step 1: Slide into stack
    steps.push({
      type: 'push_slide',
      items: [...prevItems, { ...newNode, state: 'active' }],
      highlightedLines: [2, 3],
      explanation: `Linking new node to previous top. Adjusting Stack pointer.`,
      complexity: 'O(1) Time / O(1) Space',
      pseudocode: this.getPseudocode('push')
    });

    // Finalize internal state
    this.items.push(newNode);

    // Step 2: Settled
    steps.push({
      type: 'push_settled',
      items: this.items.map(item => ({ ...item, state: 'normal' })),
      highlightedLines: [4],
      explanation: `Node ${value} is now pushed at the top of the stack.`,
      complexity: 'O(1) Time',
      pseudocode: this.getPseudocode('push')
    });

    return steps;
  }

  pop() {
    const steps = [];
    if (this.items.length === 0) {
      steps.push({
        type: 'pop_empty',
        items: [],
        highlightedLines: [1],
        explanation: 'Stack Underflow: The stack is empty. Cannot pop.',
        complexity: 'O(1) Time',
        pseudocode: this.getPseudocode('pop')
      });
      return steps;
    }

    const poppedNode = this.items[this.items.length - 1];
    const prevItems = [...this.items];

    // Step 0: Highlight top node
    steps.push({
      type: 'pop_highlight',
      items: prevItems.map((item, idx) => ({
        ...item,
        state: idx === prevItems.length - 1 ? 'highlighted' : 'normal'
      })),
      highlightedLines: [2],
      explanation: `Identifying the top node with value: ${poppedNode.value}.`,
      complexity: 'O(1) Time',
      pseudocode: this.getPseudocode('pop')
    });

    // Step 1: Lift node out
    steps.push({
      type: 'pop_lift',
      items: prevItems.map((item, idx) => ({
        ...item,
        state: idx === prevItems.length - 1 ? 'pop_lift' : 'normal'
      })),
      highlightedLines: [3, 4],
      explanation: `Redirecting top pointer to top.next and removing node ${poppedNode.value}.`,
      complexity: 'O(1) Time',
      pseudocode: this.getPseudocode('pop')
    });

    // Finalize internal state
    this.items.pop();

    // Step 2: Node removed
    steps.push({
      type: 'pop_settled',
      items: this.items.map(item => ({ ...item, state: 'normal' })),
      highlightedLines: [5],
      explanation: `Value ${poppedNode.value} popped successfully.`,
      complexity: 'O(1) Time',
      pseudocode: this.getPseudocode('pop')
    });

    return steps;
  }

  clear() {
    this.items = [];
    return [{
      type: 'clear',
      items: [],
      highlightedLines: [0],
      explanation: 'Stack cleared and reset.',
      complexity: 'O(1) Time',
      pseudocode: this.getPseudocode('push')
    }];
  }

  getPseudocode(op) {
    if (op === 'push') {
      return [
        "function push(value):",
        "  node = new StackNode(value)",
        "  node.next = top",
        "  top = node",
        "  size++"
      ];
    } else {
      return [
        "function pop():",
        "  if top is null: return UNDERFLOW",
        "  temp = top",
        "  top = top.next",
        "  free temp",
        "  return temp.value"
      ];
    }
  }
}
