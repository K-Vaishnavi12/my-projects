export const MODULES = [
    {
        id: 'arrays',
        slug: 'arrays',
        title: 'Arrays & Searching',
        icon: '🔢',
        color: '#38bdf8',
        gradient: 'linear-gradient(135deg, #0ea5e9, #38bdf8)',
        glowColor: 'rgba(56,189,248,0.4)',
        difficulty: 'Beginner',
        xpReward: 100,
        badgeId: 'array_master',
        description: 'Master array indexing, linear and binary search, and the two-pointer technique.',
        concepts: ['Array Indexing O(1)', 'Linear Search O(n)', 'Binary Search O(log n)', 'Two Pointers'],
        quiz: [
            {
                q: 'What is the time complexity of Binary Search?',
                options: ['O(n)', 'O(n²)', 'O(log n)', 'O(1)'],
                answer: 2,
                explanation: 'Binary Search halves the search space each iteration, giving O(log n).'
            },
            {
                q: 'Binary Search requires the array to be ___.',
                options: ['Random', 'Sorted', 'Reversed', 'Any order'],
                answer: 1,
                explanation: 'Binary Search only works on sorted arrays to correctly determine which half to search.'
            },
            {
                q: 'What is the time complexity of accessing arr[5] in a Python list?',
                options: ['O(n)', 'O(log n)', 'O(1)', 'O(n log n)'],
                answer: 2,
                explanation: 'Array/list index access is O(1) — constant time, regardless of list size.'
            },
            {
                q: 'In Binary Search, if arr[mid] < target, we move the ___ pointer.',
                options: ['right', 'left', 'both', 'none'],
                answer: 1,
                explanation: 'If the mid element is less than target, we search the right half by moving left = mid + 1.'
            },
        ]
    },
    {
        id: 'linked-lists',
        slug: 'linked_lists',
        title: 'Linked Lists',
        icon: '🔗',
        color: '#a855f7',
        gradient: 'linear-gradient(135deg, #7c3aed, #a855f7)',
        glowColor: 'rgba(168,85,247,0.4)',
        difficulty: 'Beginner',
        xpReward: 150,
        badgeId: 'chain_builder',
        description: 'Understand nodes, pointers, and dynamic memory with linked lists.',
        concepts: ['Node & Pointer', 'Insertion O(1)/O(n)', 'Deletion O(n)', 'Reversal O(n)'],
        quiz: [
            {
                q: 'What is the time complexity of inserting at the HEAD of a linked list?',
                options: ['O(n)', 'O(log n)', 'O(n²)', 'O(1)'],
                answer: 3,
                explanation: 'Inserting at the head just updates the head pointer — O(1).'
            },
            {
                q: 'What does each node in a singly linked list contain?',
                options: ['Only data', 'Data and two pointers', 'Data and one pointer (next)', 'Only a pointer'],
                answer: 2,
                explanation: 'Each singly linked list node has data and a .next pointer to the next node.'
            },
            {
                q: 'What is the time complexity of searching for a value in a linked list?',
                options: ['O(1)', 'O(log n)', 'O(n)', 'O(n²)'],
                answer: 2,
                explanation: 'You must traverse from head to find a value — O(n) in the worst case.'
            },
            {
                q: 'When is a linked list preferred over an array?',
                options: ['When random access is needed', 'When frequent insertions/deletions at head are needed', 'When memory is limited', 'When sorting is required'],
                answer: 1,
                explanation: 'Linked lists excel at O(1) head insertions/deletions without shifting elements.'
            },
        ]
    },
    {
        id: 'stacks',
        slug: 'stacks',
        title: 'Stacks & Queues',
        icon: '📚',
        color: '#22d3a0',
        gradient: 'linear-gradient(135deg, #059669, #22d3a0)',
        glowColor: 'rgba(34,211,160,0.4)',
        difficulty: 'Intermediate',
        xpReward: 150,
        badgeId: 'stack_lord',
        description: 'Work with LIFO stacks and FIFO queues through real-world problems.',
        concepts: ['Stack LIFO', 'Queue FIFO', 'Push/Pop O(1)', 'Bracket Matching'],
        quiz: [
            {
                q: 'A Stack follows which principle?',
                options: ['FIFO', 'LIFO', 'FILO', 'Random'],
                answer: 1,
                explanation: 'Stack is Last In, First Out (LIFO) — the last element pushed is the first popped.'
            },
            {
                q: 'Which Python data structure is best for implementing a Queue efficiently?',
                options: ['list', 'set', 'deque', 'dict'],
                answer: 2,
                explanation: 'collections.deque provides O(1) appendleft/popleft, making it ideal for queues.'
            },
            {
                q: 'Balanced bracket checking uses which data structure?',
                options: ['Queue', 'Array', 'Stack', 'Tree'],
                answer: 2,
                explanation: 'A Stack is used — push opening brackets, pop when a closing bracket is found.'
            },
            {
                q: 'What operation does .popleft() on a deque simulate?',
                options: ['Stack pop', 'Queue dequeue', 'Array shift', 'Tree deletion'],
                answer: 1,
                explanation: 'popleft() removes from the front, which is the dequeue operation in a Queue.'
            },
        ]
    },
    {
        id: 'trees',
        slug: 'trees',
        title: 'Trees & BST',
        icon: '🌳',
        color: '#fb923c',
        gradient: 'linear-gradient(135deg, #ea580c, #fb923c)',
        glowColor: 'rgba(251,146,60,0.4)',
        difficulty: 'Intermediate',
        xpReward: 200,
        badgeId: 'tree_climber',
        description: 'Explore binary trees, BST insertion, search, and tree traversals.',
        concepts: ['BST Property', 'Insert O(log n)', 'In/Pre/Post-Order', 'Height & Balance'],
        quiz: [
            {
                q: 'In a BST, where are values smaller than the root stored?',
                options: ['Right subtree', 'Left subtree', 'Both sides', 'Root level'],
                answer: 1,
                explanation: 'BST property: left child < parent < right child.'
            },
            {
                q: 'Which traversal visits nodes in SORTED order in a BST?',
                options: ['Pre-order', 'Post-order', 'In-order', 'Level-order'],
                answer: 2,
                explanation: 'In-order traversal (left → root → right) visits BST nodes in ascending sorted order.'
            },
            {
                q: 'Average time complexity of searching in a BST?',
                options: ['O(n)', 'O(1)', 'O(n log n)', 'O(log n)'],
                answer: 3,
                explanation: 'In a balanced BST, search eliminates half the tree at each step — O(log n).'
            },
            {
                q: 'What is the worst-case height of a BST with n nodes?',
                options: ['O(log n)', 'O(√n)', 'O(n)', 'O(1)'],
                answer: 2,
                explanation: 'In the worst case (e.g., sorted insertions), BST degenerates into a linked list — O(n).'
            },
        ]
    },
    {
        id: 'sorting',
        slug: 'sorting',
        title: 'Sorting Algorithms',
        icon: '⚡',
        color: '#facc15',
        gradient: 'linear-gradient(135deg, #d97706, #facc15)',
        glowColor: 'rgba(250,204,21,0.4)',
        difficulty: 'Intermediate',
        xpReward: 200,
        badgeId: 'sort_racer',
        description: 'Race Bubble, Merge, and Quick Sort and understand time complexity.',
        concepts: ['Bubble Sort O(n²)', 'Merge Sort O(n log n)', 'Quick Sort O(n log n)', 'Stability'],
        quiz: [
            {
                q: 'Which sorting algorithm uses a divide-and-conquer strategy and is O(n log n)?',
                options: ['Bubble Sort', 'Selection Sort', 'Merge Sort', 'Insertion Sort'],
                answer: 2,
                explanation: 'Merge Sort divides the array in half recursively and merges sorted halves — O(n log n).'
            },
            {
                q: 'What is the worst-case complexity of Quick Sort?',
                options: ['O(n log n)', 'O(n)', 'O(n²)', 'O(log n)'],
                answer: 2,
                explanation: 'When the pivot is always the smallest/largest element (sorted/reverse sorted), Quick Sort degrades to O(n²).'
            },
            {
                q: 'Bubble Sort compares adjacent elements and swaps them. Its time complexity is:',
                options: ['O(log n)', 'O(n)', 'O(n log n)', 'O(n²)'],
                answer: 3,
                explanation: 'Bubble Sort has nested loops — O(n²) in the worst case.'
            },
            {
                q: 'Which sort is stable (preserves relative order of equal elements)?',
                options: ['Quick Sort', 'Heap Sort', 'Merge Sort', 'Selection Sort'],
                answer: 2,
                explanation: 'Merge Sort is stable because it maintains relative order when merging equal elements.'
            },
        ]
    },
    {
        id: 'graphs',
        slug: 'graphs',
        title: 'Graphs & BFS/DFS',
        icon: '🗺️',
        color: '#ec4899',
        gradient: 'linear-gradient(135deg, #be185d, #ec4899)',
        glowColor: 'rgba(236,72,153,0.4)',
        difficulty: 'Advanced',
        xpReward: 250,
        badgeId: 'maze_explorer',
        description: 'Navigate graphs with BFS and DFS — find paths through mazes!',
        concepts: ['Adjacency List', 'BFS O(V+E)', 'DFS O(V+E)', 'Shortest Path'],
        quiz: [
            {
                q: 'BFS uses which data structure for traversal?',
                options: ['Stack', 'Queue', 'Heap', 'Tree'],
                answer: 1,
                explanation: 'BFS uses a Queue (FIFO) to explore layer by layer from the source node.'
            },
            {
                q: 'DFS uses which data structure (or mechanism) for traversal?',
                options: ['Queue', 'Heap', 'Stack / Recursion', 'Deque'],
                answer: 2,
                explanation: 'DFS uses a Stack (or call stack via recursion) to go deep before backtracking.'
            },
            {
                q: 'BFS guarantees the ___ path in an unweighted graph.',
                options: ['Longest', 'Shortest', 'Random', 'Heaviest'],
                answer: 1,
                explanation: 'BFS explores nodes level by level, so the first time it reaches a node = shortest path.'
            },
            {
                q: 'Time complexity of BFS/DFS where V = vertices, E = edges:',
                options: ['O(V²)', 'O(V × E)', 'O(V + E)', 'O(log V)'],
                answer: 2,
                explanation: 'Both BFS and DFS visit each vertex and edge once — O(V + E).'
            },
        ]
    },
    {
        id: 'hash-tables',
        slug: 'hash_tables',
        title: 'Hash Tables',
        icon: '🔑',
        color: '#10b981',
        gradient: 'linear-gradient(135deg, #047857, #10b981)',
        glowColor: 'rgba(16,185,129,0.4)',
        difficulty: 'Intermediate',
        xpReward: 150,
        badgeId: 'hash_master',
        description: 'Learn about hash functions, collisions, and O(1) lookups.',
        concepts: ['Hash Functions', 'Collision Resolution', 'O(1) Insertion/Lookup'],
        quiz: [
            {
                q: 'What is the average time complexity for a lookup in a hash table?',
                options: ['O(n)', 'O(n log n)', 'O(1)', 'O(log n)'],
                answer: 2,
                explanation: 'Hash tables provide O(1) average time complexity for lookups using the key.'
            },
            {
                q: 'What occurs when two different keys hash to the same index?',
                options: ['Syntax Error', 'Collision', 'Overflow', 'Deadlock'],
                answer: 1,
                explanation: 'A collision happens when two keys result in the same hash index. This is handled by techniques like chaining or open addressing.'
            },
            {
                q: 'Which data structure is often used to handle collisions via chaining?',
                options: ['Stack', 'Queue', 'Linked List', 'Heap'],
                answer: 2,
                explanation: 'Chaining stores colliding elements in a Linked List at that specific index.'
            },
            {
                q: 'In Python, a hash table is implemented as which built-in type?',
                options: ['list', 'tuple', 'set', 'dict'],
                answer: 3,
                explanation: 'A dictionary (`dict`) in Python uses a hash table internally.'
            },
        ]
    },
    {
        id: 'dynamic-programming',
        slug: 'dynamic_programming',
        title: 'Dynamic Programming',
        icon: '🧠',
        color: '#f43f5e',
        gradient: 'linear-gradient(135deg, #be123c, #f43f5e)',
        glowColor: 'rgba(244,63,94,0.4)',
        difficulty: 'Advanced',
        xpReward: 300,
        badgeId: 'dp_genius',
        description: 'Master memoization and tabulation to optimize recursive algorithms.',
        concepts: ['Overlapping Subproblems', 'Optimal Substructure', 'Memoization (Top-Down)', 'Tabulation (Bottom-Up)'],
        quiz: [
            {
                q: 'What is the main purpose of Dynamic Programming?',
                options: ['To avoid recursion entirely', 'To sort an array faster', 'To store results of overlapping subproblems', 'To traverse a graph'],
                answer: 2,
                explanation: 'DP optimizes efficiency by storing the answers to subproblems so they are not re-calculated.'
            },
            {
                q: 'Which approach starts with the base cases and iteratively builds up to the target?',
                options: ['Memoization', 'Tabulation', 'Divide and Conquer', 'Backtracking'],
                answer: 1,
                explanation: 'Tabulation (Bottom-Up DP) starts from the base cases and uses an array/table to build up the solution.'
            },
            {
                q: 'What is the time complexity of a naive recursive Fibonacci (without DP)?',
                options: ['O(n)', 'O(n²)', 'O(n log n)', 'O(2ⁿ)'],
                answer: 3,
                explanation: 'Naive recursive Fibonacci branches into two calls each time, resulting in exponential O(2ⁿ) complexity.'
            },
            {
                q: 'Which two properties must a problem have to be solvable using DP?',
                options: ['Overlapping Subproblems & Optimal Substructure', 'Recursion & Base Case', 'Greedy Choice & Optimal Substructure', 'Overlapping Subproblems & Divide and Conquer'],
                answer: 0,
                explanation: 'A problem must have Overlapping Subproblems and Optimal Substructure to benefit from DP.'
            },
        ]
    },
    {
        id: 'heaps',
        slug: 'heaps',
        title: 'Heaps & Priority Queues',
        icon: '🏔️',
        color: '#8b5cf6',
        gradient: 'linear-gradient(135deg, #6d28d9, #8b5cf6)',
        glowColor: 'rgba(139,92,246,0.4)',
        difficulty: 'Advanced',
        xpReward: 250,
        badgeId: 'heap_hero',
        description: 'Understand Min-Heaps, Max-Heaps, and efficiently getting the largest/smallest elements.',
        concepts: ['Min-Heap', 'Max-Heap', 'Insertion O(log n)', 'Extract-Min O(log n)'],
        quiz: [
            {
                q: 'In a Min-Heap, where is the smallest element located?',
                options: ['At the bottom level', 'At the root', 'At a leaf node', 'It can be anywhere'],
                answer: 1,
                explanation: 'By the Min-Heap property, the root node always contains the smallest element.'
            },
            {
                q: 'Which built-in Python module provides heap queue operations?',
                options: ['queue', 'heap', 'heapq', 'collections'],
                answer: 2,
                explanation: 'The `heapq` module provides an implementation of the heap queue algorithm (a min-heap).'
            },
            {
                q: 'What is the time complexity of extracting the minimum element from a Min-Heap?',
                options: ['O(1)', 'O(log n)', 'O(n)', 'O(n log n)'],
                answer: 1,
                explanation: 'Extracting takes O(1), but restoring the heap property (heapify-down) takes O(log n).'
            },
            {
                q: 'A binary heap is typically implemented using an array because it represents a:',
                options: ['Binary Search Tree', 'Complete Binary Tree', 'Full Binary Tree', 'Spanning Tree'],
                answer: 1,
                explanation: 'A heap is a Complete Binary Tree, meaning all levels are fully filled except possibly the last level, making array representation very space-efficient.'
            },
        ]
    },
    {
        id: 'tries',
        slug: 'tries',
        title: 'Tries (Prefix Trees)',
        icon: '🌲',
        color: '#14b8a6',
        gradient: 'linear-gradient(135deg, #0f766e, #14b8a6)',
        glowColor: 'rgba(20,184,166,0.4)',
        difficulty: 'Advanced',
        xpReward: 250,
        badgeId: 'trie_titan',
        description: 'Build fast autocomplete systems using the Trie data structure.',
        concepts: ['Prefix Tree', 'O(m) Insertion/Search', 'Autocomplete Algorithms'],
        quiz: [
            {
                q: 'What is the primary use case of a Trie?',
                options: ['Sorting numbers', 'Shortest path computation', 'Prefix matching and Autocomplete', 'Balancing binary trees'],
                answer: 2,
                explanation: 'A Trie (prefix tree) naturally stores strings in a way that makes searching for prefixes extremely fast.'
            },
            {
                q: 'What is the time complexity of inserting a word of length \'L\' into a Trie?',
                options: ['O(1)', 'O(L)', 'O(log L)', 'O(n)'],
                answer: 1,
                explanation: 'Inserting a word takes O(L) time, where L is the length of the word, as you add each character one by one.'
            },
            {
                q: 'A standard Trie node contains:',
                options: ['A value and two pointers (left, right)', 'An array/hashmap of children and a boolean flag', 'Just a value', 'A list of related words'],
                answer: 1,
                explanation: 'A Trie node typically contains a hashmap (or array of size 26) pointing to child nodes, and a boolean `is_end_of_word` flag.'
            },
            {
                q: 'Compared to a Hash Table, what is a disadvantage of a Trie?',
                options: ['Slower lookup time', 'Cannot store strings', 'Higher memory consumption', 'Prone to collisions'],
                answer: 2,
                explanation: 'Tries can consume significantly more memory due to the large number of child pointers created at every node.'
            },
        ]
    }
]
