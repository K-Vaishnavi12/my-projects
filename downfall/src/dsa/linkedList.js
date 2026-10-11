export class LinkedListEngine {
  constructor() {
    this.items = []; // array of { id, value } representing the linked list in order
    this.counter = 0;
  }

  insert(value, index = null) {
    const steps = [];
    const newId = `ll_${this.counter++}`;
    const newNode = { id: newId, value };
    const prevItems = [...this.items];

    // Determine clean index (clamp bounds)
    let idx = index !== null ? parseInt(index) : prevItems.length;
    if (isNaN(idx) || idx < 0) idx = 0;
    if (idx > prevItems.length) idx = prevItems.length;

    // Step 0: Spawn node
    steps.push({
      type: 'insert_spawn',
      items: this.cloneWithStates(prevItems),
      newNode: { ...newNode, state: 'spawn' },
      insertIndex: idx,
      highlightedLines: [1, 2],
      explanation: `Creating new node in memory with value: ${value}.`,
      complexity: 'O(1) Space',
      pseudocode: this.getPseudocode('insert')
    });

    if (idx === 0) {
      // Insertion at Head
      steps.push({
        type: 'insert_link_next',
        items: this.cloneWithStates(prevItems),
        newNode: { ...newNode, state: 'active' },
        insertIndex: idx,
        highlightedLines: [3],
        explanation: `Pointing new node's 'next' pointer to current head node.`,
        complexity: 'O(1) Time',
        pseudocode: this.getPseudocode('insert')
      });

      const nextItems = [newNode, ...prevItems];
      steps.push({
        type: 'insert_settled',
        items: this.cloneWithStates(nextItems),
        newNode: null,
        insertIndex: idx,
        highlightedLines: [4, 5],
        explanation: `Updating Head pointer to point to the new node. Insertion complete.`,
        complexity: 'O(1) Time',
        pseudocode: this.getPseudocode('insert')
      });

      this.items = nextItems;
    } else {
      // Insertion in middle or tail
      // Traverse to find the index-1 node
      for (let i = 0; i < idx; i++) {
        const traverseItems = this.cloneWithStates(prevItems);
        // Highlight all traversed nodes
        for (let j = 0; j <= i; j++) {
          traverseItems[j].state = j === i ? 'active' : 'highlighted';
        }
        steps.push({
          type: 'insert_traverse',
          items: traverseItems,
          newNode: { ...newNode, state: 'spawn' },
          insertIndex: idx,
          highlightedLines: [6, 7, 8],
          explanation: `Traversing: current pointer at node value ${prevItems[i].value} (index ${i}). Searching for index ${idx - 1}.`,
          complexity: 'O(N) Time',
          pseudocode: this.getPseudocode('insert')
        });
      }

      // Link new node to prevNode's next
      steps.push({
        type: 'insert_link_next',
        items: prevItems.map((item, i) => ({
          ...item,
          state: i === idx - 1 ? 'active' : 'normal'
        })),
        newNode: { ...newNode, state: 'active' },
        insertIndex: idx,
        highlightedLines: [9],
        explanation: `Setting new node's next pointer to node ${prevItems[idx] ? prevItems[idx].value : 'null'}.`,
        complexity: 'O(1) Time',
        pseudocode: this.getPseudocode('insert')
      });

      // Point prevNode to new node
      const nextItems = [...prevItems];
      nextItems.splice(idx, 0, newNode);

      steps.push({
        type: 'insert_link_prev',
        items: nextItems.map((item, i) => {
          if (item.id === newId) return { ...item, state: 'active' };
          if (i === idx - 1) return { ...item, state: 'highlighted' };
          return { ...item, state: 'normal' };
        }),
        newNode: null,
        insertIndex: idx,
        highlightedLines: [10],
        explanation: `Breaking old link. Pointing node ${prevItems[idx - 1].value}'s next to new node ${value}.`,
        complexity: 'O(1) Time',
        pseudocode: this.getPseudocode('insert')
      });

      // Complete
      steps.push({
        type: 'insert_settled',
        items: this.cloneWithStates(nextItems),
        newNode: null,
        insertIndex: idx,
        highlightedLines: [11],
        explanation: `Node ${value} inserted successfully at index ${idx}.`,
        complexity: 'O(N) Time (Traverse) + O(1) Time (Insert)',
        pseudocode: this.getPseudocode('insert')
      });

      this.items = nextItems;
    }

    return steps;
  }

  delete(index) {
    const steps = [];
    const prevItems = [...this.items];

    if (prevItems.length === 0) {
      steps.push({
        type: 'delete_empty',
        items: [],
        highlightedLines: [1],
        explanation: 'Linked List is empty. Cannot delete.',
        complexity: 'O(1) Time',
        pseudocode: this.getPseudocode('delete')
      });
      return steps;
    }

    let idx = parseInt(index);
    if (isNaN(idx) || idx < 0 || idx >= prevItems.length) {
      steps.push({
        type: 'delete_invalid',
        items: this.cloneWithStates(prevItems),
        highlightedLines: [1],
        explanation: `Invalid index: ${index}. Cannot delete.`,
        complexity: 'O(1) Time',
        pseudocode: this.getPseudocode('delete')
      });
      return steps;
    }

    const targetNode = prevItems[idx];

    if (idx === 0) {
      // Delete head
      steps.push({
        type: 'delete_highlight',
        items: prevItems.map((item, i) => ({
          ...item,
          state: i === 0 ? 'highlighted' : 'normal'
        })),
        highlightedLines: [2],
        explanation: `Targeting Head node ${targetNode.value} for deletion.`,
        complexity: 'O(1) Time',
        pseudocode: this.getPseudocode('delete')
      });

      steps.push({
        type: 'delete_relink',
        items: prevItems.map((item, i) => ({
          ...item,
          state: i === 0 ? 'delete_lift' : 'normal'
        })),
        highlightedLines: [3],
        explanation: `Updating Head pointer to head.next (node ${prevItems[1] ? prevItems[1].value : 'null'}).`,
        complexity: 'O(1) Time',
        pseudocode: this.getPseudocode('delete')
      });

      const nextItems = prevItems.slice(1);
      steps.push({
        type: 'delete_settled',
        items: this.cloneWithStates(nextItems),
        highlightedLines: [4],
        explanation: `Node ${targetNode.value} deleted successfully.`,
        complexity: 'O(1) Time',
        pseudocode: this.getPseudocode('delete')
      });

      this.items = nextItems;
    } else {
      // Delete middle/tail
      // Traverse to find the index-1 node
      for (let i = 0; i < idx; i++) {
        const traverseItems = this.cloneWithStates(prevItems);
        for (let j = 0; j <= i; j++) {
          traverseItems[j].state = j === i ? 'active' : 'highlighted';
        }
        steps.push({
          type: 'delete_traverse',
          items: traverseItems,
          highlightedLines: [5, 6, 7],
          explanation: `Traversing: current pointer at node value ${prevItems[i].value} (index ${i}). Searching for index ${idx - 1}.`,
          complexity: 'O(N) Time',
          pseudocode: this.getPseudocode('delete')
        });
      }

      // Highlight target to delete
      steps.push({
        type: 'delete_highlight',
        items: prevItems.map((item, i) => {
          if (i === idx) return { ...item, state: 'highlighted' };
          if (i === idx - 1) return { ...item, state: 'active' };
          return { ...item, state: 'normal' };
        }),
        highlightedLines: [8],
        explanation: `Target node ${targetNode.value} identified at index ${idx}. Prev node is ${prevItems[idx - 1].value}.`,
        complexity: 'O(1) Time',
        pseudocode: this.getPseudocode('delete')
      });

      // Break link and relink prevNode to target's next
      steps.push({
        type: 'delete_relink',
        items: prevItems.map((item, i) => {
          if (i === idx) return { ...item, state: 'delete_lift' };
          if (i === idx - 1) return { ...item, state: 'highlighted' };
          return { ...item, state: 'normal' };
        }),
        highlightedLines: [9],
        explanation: `Updating node ${prevItems[idx - 1].value}'s next to point to ${prevItems[idx + 1] ? prevItems[idx + 1].value : 'null'}.`,
        complexity: 'O(1) Time',
        pseudocode: this.getPseudocode('delete')
      });

      const nextItems = prevItems.filter((_, i) => i !== idx);

      // Complete
      steps.push({
        type: 'delete_settled',
        items: this.cloneWithStates(nextItems),
        highlightedLines: [10],
        explanation: `Node ${targetNode.value} removed from memory. Positions adjusted.`,
        complexity: 'O(N) Time (Traverse) + O(1) Time (Delete)',
        pseudocode: this.getPseudocode('delete')
      });

      this.items = nextItems;
    }

    return steps;
  }

  clear() {
    this.items = [];
    return [{
      type: 'clear',
      items: [],
      highlightedLines: [0],
      explanation: 'Linked List cleared.',
      complexity: 'O(1) Time',
      pseudocode: this.getPseudocode('insert')
    }];
  }

  cloneWithStates(arr) {
    return arr.map(item => ({ ...item, state: 'normal' }));
  }

  getPseudocode(op) {
    if (op === 'insert') {
      return [
        "function insert(value, index):",
        "  node = new LinkedListNode(value)",
        "  if index == 0:",
        "    node.next = head",
        "    head = node",
        "    return",
        "  curr = head",
        "  for i = 0 to index - 1:",
        "    curr = curr.next",
        "  node.next = curr.next",
        "  curr.next = node",
        "  size++"
      ];
    } else {
      return [
        "function delete(index):",
        "  if head is null or index out of bounds: error",
        "  if index == 0:",
        "    head = head.next",
        "    return",
        "  curr = head",
        "  for i = 0 to index - 1:",
        "    curr = curr.next",
        "  target = curr.next",
        "  curr.next = target.next",
        "  free target"
      ];
    }
  }
}
