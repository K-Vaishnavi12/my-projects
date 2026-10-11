export const PYTHON_CODE = {
    arrays: `# Arrays & Searching in Python
# ─────────────────────────────

# Creating & accessing arrays (lists)
arr = [10, 23, 5, 17, 42, 8, 31]
print(arr[0])          # 10  → O(1) access
print(len(arr))        # 7

# Linear Search  →  O(n)
def linear_search(arr, target):
    for i, val in enumerate(arr):
        if val == target:
            return i   # found at index i
    return -1

# Binary Search  →  O(log n)  (requires sorted array)
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1   # search right half
        else:
            right = mid - 1  # search left half
    return -1

sorted_arr = [5, 8, 10, 17, 23, 31, 42]
print(binary_search(sorted_arr, 17))   # → 3

# Two Pointer Technique  →  O(n)
def two_sum(arr, target):
    left, right = 0, len(arr) - 1
    while left < right:
        s = arr[left] + arr[right]
        if s == target:   return (left, right)
        elif s < target:  left += 1
        else:             right -= 1
    return None
`,
    linked_lists: `# Linked Lists in Python
# ─────────────────────────

class Node:
    def __init__(self, data):
        self.data = data
        self.next = None   # pointer to next node

class LinkedList:
    def __init__(self):
        self.head = None

    # Insert at the end  →  O(n)
    def append(self, data):
        new_node = Node(data)
        if not self.head:
            self.head = new_node; return
        curr = self.head
        while curr.next:          # traverse to end
            curr = curr.next
        curr.next = new_node

    # Insert at front  →  O(1)
    def prepend(self, data):
        new_node = Node(data)
        new_node.next = self.head
        self.head = new_node

    # Delete a node  →  O(n)
    def delete(self, data):
        if not self.head: return
        if self.head.data == data:
            self.head = self.head.next; return
        curr = self.head
        while curr.next:
            if curr.next.data == data:
                curr.next = curr.next.next; return
            curr = curr.next

    # Reverse the list  →  O(n)
    def reverse(self):
        prev, curr = None, self.head
        while curr:
            nxt = curr.next
            curr.next = prev
            prev, curr = curr, nxt
        self.head = prev

    def display(self):
        vals, curr = [], self.head
        while curr:
            vals.append(str(curr.data)); curr = curr.next
        print(" → ".join(vals))

ll = LinkedList()
ll.append(1); ll.append(2); ll.append(3)
ll.prepend(0)
ll.display()    # 0 → 1 → 2 → 3
ll.reverse()
ll.display()    # 3 → 2 → 1 → 0
`,
    stacks: `# Stacks & Queues in Python
# ──────────────────────────

# ─── STACK (LIFO: Last In, First Out) ───
class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):      # O(1)
        self.items.append(item)

    def pop(self):             # O(1)
        if self.is_empty(): raise IndexError("Stack underflow")
        return self.items.pop()

    def peek(self):            # O(1)
        return self.items[-1] if self.items else None

    def is_empty(self):
        return len(self.items) == 0

    def size(self):
        return len(self.items)

# Classic: Balanced Brackets
def is_balanced(expression):
    stack = Stack()
    pairs = {')': '(', ']': '[', '}': '{'}
    for ch in expression:
        if ch in '([{':
            stack.push(ch)
        elif ch in ')]}':
            if stack.is_empty() or stack.pop() != pairs[ch]:
                return False
    return stack.is_empty()

print(is_balanced("({[]})"))   # True
print(is_balanced("({[})"))    # False

# ─── QUEUE (FIFO: First In, First Out) ───
from collections import deque

class Queue:
    def __init__(self):
        self.items = deque()

    def enqueue(self, item):   # O(1)
        self.items.append(item)

    def dequeue(self):         # O(1)
        if self.is_empty(): raise IndexError("Queue underflow")
        return self.items.popleft()

    def front(self):
        return self.items[0] if self.items else None

    def is_empty(self):
        return len(self.items) == 0

q = Queue()
q.enqueue("A"); q.enqueue("B"); q.enqueue("C")
print(q.dequeue())   # A
print(q.front())     # B
`,
    trees: `# Trees & Binary Search Tree (BST)
# ────────────────────────────────

class TreeNode:
    def __init__(self, val):
        self.val   = val
        self.left  = None   # left child
        self.right = None   # right child

class BST:
    def __init__(self):
        self.root = None

    # Insert  →  O(log n) avg, O(n) worst
    def insert(self, val):
        self.root = self._insert(self.root, val)

    def _insert(self, node, val):
        if not node: return TreeNode(val)
        if val < node.val:
            node.left  = self._insert(node.left,  val)
        elif val > node.val:
            node.right = self._insert(node.right, val)
        return node

    # Search  →  O(log n) avg
    def search(self, val):
        return self._search(self.root, val)

    def _search(self, node, val):
        if not node: return False
        if node.val == val: return True
        if val < node.val:  return self._search(node.left,  val)
        return self._search(node.right, val)

    # In-order traversal (sorted output)  →  O(n)
    def inorder(self, node=None, result=None):
        if result is None: result, node = [], self.root
        if node:
            self.inorder(node.left,  result)
            result.append(node.val)
            self.inorder(node.right, result)
        return result

bst = BST()
for v in [50, 30, 70, 20, 40, 60, 80]:
    bst.insert(v)

print(bst.inorder())        # [20, 30, 40, 50, 60, 70, 80]
print(bst.search(40))       # True
print(bst.search(99))       # False
`,
    sorting: `# Sorting Algorithms in Python
# ──────────────────────────────

# ─── Bubble Sort  →  O(n²) ───
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

# ─── Selection Sort  →  O(n²) ───
def selection_sort(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr

# ─── Merge Sort  →  O(n log n) ───
def merge_sort(arr):
    if len(arr) <= 1: return arr
    mid   = len(arr) // 2
    left  = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    return result + left[i:] + right[j:]

# ─── Quick Sort  →  O(n log n) avg ───
def quick_sort(arr):
    if len(arr) <= 1: return arr
    pivot  = arr[len(arr) // 2]
    left   = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right  = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)

arr = [64, 25, 12, 22, 11]
print(bubble_sort(arr[:]))    # [11, 12, 22, 25, 64]
print(merge_sort(arr[:]))     # [11, 12, 22, 25, 64]
print(quick_sort(arr[:]))     # [11, 12, 22, 25, 64]
`,
    graphs: `# Graphs, BFS & DFS in Python
# ─────────────────────────────

# Graph represented as adjacency list
graph = {
    'A': ['B', 'C'],
    'B': ['A', 'D', 'E'],
    'C': ['A', 'F'],
    'D': ['B'],
    'E': ['B', 'F'],
    'F': ['C', 'E'],
}

# ─── BFS (Breadth-First Search)  →  O(V + E) ───
from collections import deque

def bfs(graph, start):
    visited, queue = set([start]), deque([start])
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return order

print(bfs(graph, 'A'))
# ['A', 'B', 'C', 'D', 'E', 'F']

# ─── DFS (Depth-First Search)  →  O(V + E) ───
def dfs(graph, start, visited=None):
    if visited is None: visited = set()
    visited.add(start)
    order = [start]
    for neighbor in graph[start]:
        if neighbor not in visited:
            order += dfs(graph, neighbor, visited)
    return order

print(dfs(graph, 'A'))
# ['A', 'B', 'D', 'E', 'F', 'C']

# ─── Shortest Path (BFS)  →  O(V + E) ───
def shortest_path(graph, start, end):
    queue = deque([[start]])
    visited = {start}
    while queue:
        path = queue.popleft()
        node = path[-1]
        if node == end: return path
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(path + [neighbor])
    return None

print(shortest_path(graph, 'A', 'F'))
# ['A', 'C', 'F']
`,
}
