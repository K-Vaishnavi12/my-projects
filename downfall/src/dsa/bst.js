export class BstEngine {
  constructor() {
    this.root = null; // Root node reference
    this.counter = 0;
  }

  // Helper to flat map the tree to an array for easy visualization
  getNodesList(treeNode = this.root, depth = 0, posIndex = 0, parentId = null) {
    if (!treeNode) return [];
    
    const list = [{
      id: treeNode.id,
      value: treeNode.value,
      leftId: treeNode.left ? treeNode.left.id : null,
      rightId: treeNode.right ? treeNode.right.id : null,
      parentId,
      depth,
      posIndex
    }];

    const leftList = this.getNodesList(treeNode.left, depth + 1, posIndex * 2, treeNode.id);
    const rightList = this.getNodesList(treeNode.right, depth + 1, posIndex * 2 + 1, treeNode.id);

    return [...list, ...leftList, ...rightList];
  }

  insert(value) {
    const steps = [];
    const val = parseInt(value);
    if (isNaN(val)) return steps;

    const newId = `bst_${this.counter++}`;
    const newTreeNode = { id: newId, value: val, left: null, right: null };

    // Step 0: Spawn node
    steps.push({
      type: 'bst_spawn',
      nodes: this.getNodesList().map(n => ({ ...n, state: 'normal' })),
      newNode: { id: newId, value: val, state: 'spawn' },
      highlightedLines: [1, 2],
      explanation: `Creating new BST node with value: ${val}.`,
      complexity: 'O(1) Space',
      pseudocode: this.getPseudocode('insert')
    });

    if (!this.root) {
      this.root = newTreeNode;
      steps.push({
        type: 'bst_settled',
        nodes: this.getNodesList().map(n => ({ ...n, state: 'normal' })),
        newNode: null,
        highlightedLines: [3, 4],
        explanation: `Tree is empty. Setting node ${val} as the Root.`,
        complexity: 'O(1) Time',
        pseudocode: this.getPseudocode('insert')
      });
      return steps;
    }

    // Traverse and search for insertion point
    let curr = this.root;
    let parent = null;
    let path = [];

    while (curr) {
      parent = curr;
      path.push(curr.id);
      
      const currentNodesState = this.getNodesList().map(n => ({
        ...n,
        state: n.id === curr.id ? 'active' : (path.includes(n.id) ? 'highlighted' : 'normal')
      }));

      if (val < curr.value) {
        steps.push({
          type: 'bst_traverse',
          nodes: currentNodesState,
          newNode: { id: newId, value: val, state: 'spawn' },
          highlightedLines: [5, 6, 7],
          explanation: `Comparing: ${val} < ${curr.value}. Traversing Left child.`,
          complexity: 'O(log N) Avg / O(N) Worst',
          pseudocode: this.getPseudocode('insert')
        });
        
        if (!curr.left) {
          curr.left = newTreeNode;
          break;
        }
        curr = curr.left;
      } else {
        steps.push({
          type: 'bst_traverse',
          nodes: currentNodesState,
          newNode: { id: newId, value: val, state: 'spawn' },
          highlightedLines: [8, 9, 10],
          explanation: `Comparing: ${val} >= ${curr.value}. Traversing Right child.`,
          complexity: 'O(log N) Avg / O(N) Worst',
          pseudocode: this.getPseudocode('insert')
        });

        if (!curr.right) {
          curr.right = newTreeNode;
          break;
        }
        curr = curr.right;
      }
    }

    // Finalize placement
    steps.push({
      type: 'bst_settled',
      nodes: this.getNodesList().map(n => ({
        ...n,
        state: n.id === newId ? 'active' : 'normal'
      })),
      newNode: null,
      highlightedLines: [11],
      explanation: `Inserted node ${val} into position.`,
      complexity: 'O(log N) Avg / O(N) Worst',
      pseudocode: this.getPseudocode('insert')
    });

    return steps;
  }

  search(value) {
    const steps = [];
    const val = parseInt(value);
    if (isNaN(val)) return steps;

    if (!this.root) {
      steps.push({
        type: 'bst_search_fail',
        nodes: [],
        highlightedLines: [1],
        explanation: 'BST is empty. Search terminated.',
        complexity: 'O(1) Time',
        pseudocode: this.getPseudocode('search')
      });
      return steps;
    }

    let curr = this.root;
    let path = [];
    let found = false;

    while (curr) {
      path.push(curr.id);
      
      const currentNodesState = this.getNodesList().map(n => ({
        ...n,
        state: n.id === curr.id ? 'active' : (path.includes(n.id) ? 'highlighted' : 'normal')
      }));

      if (val === curr.value) {
        steps.push({
          type: 'bst_search_success',
          nodes: currentNodesState.map(n => n.id === curr.id ? { ...n, state: 'success' } : n),
          highlightedLines: [3, 4],
          explanation: `Found node value ${val} in tree!`,
          complexity: 'O(log N) Avg',
          pseudocode: this.getPseudocode('search')
        });
        found = true;
        break;
      } else if (val < curr.value) {
        steps.push({
          type: 'bst_search_traverse',
          nodes: currentNodesState,
          highlightedLines: [5, 6],
          explanation: `Checking: ${val} < ${curr.value}. Searching Left branch.`,
          complexity: 'O(log N) Avg',
          pseudocode: this.getPseudocode('search')
        });
        curr = curr.left;
      } else {
        steps.push({
          type: 'bst_search_traverse',
          nodes: currentNodesState,
          highlightedLines: [7, 8],
          explanation: `Checking: ${val} > ${curr.value}. Searching Right branch.`,
          complexity: 'O(log N) Avg',
          pseudocode: this.getPseudocode('search')
        });
        curr = curr.right;
      }
    }

    if (!found) {
      steps.push({
        type: 'bst_search_fail',
        nodes: this.getNodesList().map(n => ({
          ...n,
          state: path.includes(n.id) ? 'highlighted' : 'normal'
        })),
        highlightedLines: [9],
        explanation: `Node value ${val} not found in the BST.`,
        complexity: 'O(log N) Avg',
        pseudocode: this.getPseudocode('search')
      });
    }

    return steps;
  }

  // Traversal animations
  runTraversal(type) {
    const steps = [];
    const traversalOrder = [];
    
    // Recursive helpers to build steps
    const traverse = (node) => {
      if (!node) return;
      
      if (type === 'preorder') {
        visit(node);
        traverse(node.left);
        traverse(node.right);
      } else if (type === 'inorder') {
        traverse(node.left);
        visit(node);
        traverse(node.right);
      } else {
        traverse(node.left);
        traverse(node.right);
        visit(node);
      }
    };

    const visit = (node) => {
      traversalOrder.push(node);
      
      // Copy list and highlight currently visited node
      const nodesState = this.getNodesList().map(n => {
        const alreadyVisited = traversalOrder.some(visited => visited.id === n.id);
        return {
          ...n,
          state: n.id === node.id ? 'active' : (alreadyVisited ? 'highlighted' : 'normal')
        };
      });

      const orderString = traversalOrder.map(n => n.value).join(', ');

      steps.push({
        type: 'bst_traversal_step',
        nodes: nodesState,
        highlightedLines: [1],
        explanation: `Visited node ${node.value}. Current order: [ ${orderString} ]`,
        complexity: 'O(N) Time / O(H) Space',
        pseudocode: this.getPseudocode(type)
      });
    };

    traverse(this.root);
    
    if (steps.length === 0) {
      steps.push({
        type: 'bst_traversal_empty',
        nodes: [],
        highlightedLines: [0],
        explanation: 'Tree is empty. Nothing to traverse.',
        complexity: 'O(1) Time',
        pseudocode: this.getPseudocode('inorder')
      });
    } else {
      // Completed step
      steps.push({
        type: 'bst_traversal_complete',
        nodes: this.getNodesList().map(n => ({ ...n, state: 'normal' })),
        highlightedLines: [0],
        explanation: `Traversal completed. Total elements visited: ${traversalOrder.length}. Final output: [ ${traversalOrder.map(n => n.value).join(', ')} ]`,
        complexity: 'O(N) Time',
        pseudocode: this.getPseudocode(type)
      });
    }

    return steps;
  }

  clear() {
    this.root = null;
    return [{
      type: 'clear',
      nodes: [],
      highlightedLines: [0],
      explanation: 'BST cleared.',
      complexity: 'O(1) Time',
      pseudocode: this.getPseudocode('insert')
    }];
  }

  getPseudocode(op) {
    switch (op) {
      case 'insert':
        return [
          "function insert(node, value):",
          "  if node is null:",
          "    return new BSTNode(value)",
          "  if value < node.value:",
          "    node.left = insert(node.left, value)",
          "  else:",
          "    node.right = insert(node.right, value)",
          "  return node"
        ];
      case 'search':
        return [
          "function search(node, target):",
          "  if node is null: return NOT_FOUND",
          "  if target == node.value: return FOUND",
          "  if target < node.value:",
          "    return search(node.left, target)",
          "  else:",
          "    return search(node.right, target)"
        ];
      case 'inorder':
        return [
          "function inorder(node):",
          "  if node is not null:",
          "    inorder(node.left)",
          "    visit(node)",
          "    inorder(node.right)"
        ];
      case 'preorder':
        return [
          "function preorder(node):",
          "  if node is not null:",
          "    visit(node)",
          "    preorder(node.left)",
          "    preorder(node.right)"
        ];
      case 'postorder':
        return [
          "function postorder(node):",
          "  if node is not null:",
          "    postorder(node.left)",
          "    postorder(node.right)",
          "    visit(node)"
        ];
    }
  }
}
