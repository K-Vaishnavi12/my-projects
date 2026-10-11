export class SortingEngine {
  constructor() {
    this.items = []; // array of { id, value }
    this.counter = 0;
    this.generateRandomArray();
  }

  generateRandomArray() {
    this.items = [];
    const size = 6;
    for (let i = 0; i < size; i++) {
      const val = Math.floor(Math.random() * 80) + 15; // 15 to 95
      this.items.push({ id: `sort_${this.counter++}`, value: val });
    }
  }

  shuffle() {
    this.generateRandomArray();
    return [{
      type: 'shuffle',
      items: this.items.map(item => ({ ...item, state: 'normal' })),
      highlightedLines: [0],
      explanation: `Array shuffled: [ ${this.items.map(item => item.value).join(', ')} ]`,
      complexity: 'O(N) Time',
      pseudocode: this.getPseudocode('bubble')
    }];
  }

  bubbleSort() {
    const steps = [];
    const arr = this.items.map(item => ({ ...item }));
    const n = arr.length;
    const pseudocode = this.getPseudocode('bubble');

    // Initial state
    steps.push({
      type: 'sort_init',
      items: arr.map(item => ({ ...item, state: 'normal' })),
      highlightedLines: [1],
      explanation: `Starting Bubble Sort on array.`,
      complexity: 'O(N^2) Time / O(1) Space',
      pseudocode
    });

    let swapped;
    for (let i = 0; i < n; i++) {
      swapped = false;
      for (let j = 0; j < n - i - 1; j++) {
        // Step: Highlight j and j+1 as comparing
        steps.push({
          type: 'sort_compare',
          items: arr.map((item, idx) => ({
            ...item,
            state: idx === j || idx === j + 1 ? 'comparing' : (idx >= n - i ? 'sorted' : 'normal')
          })),
          highlightedLines: [2, 3],
          explanation: `Comparing elements at index ${j} (${arr[j].value}) and ${j + 1} (${arr[j + 1].value}).`,
          complexity: 'O(N^2) Time',
          pseudocode
        });

        if (arr[j].value > arr[j + 1].value) {
          // Swap
          const temp = arr[j];
          arr[j] = arr[j + 1];
          arr[j + 1] = temp;
          swapped = true;

          steps.push({
            type: 'sort_swap',
            items: arr.map((item, idx) => ({
              ...item,
              state: idx === j || idx === j + 1 ? 'swapping' : (idx >= n - i ? 'sorted' : 'normal')
            })),
            highlightedLines: [4],
            explanation: `Since ${arr[j + 1].value} > ${arr[j].value}, swap them.`,
            complexity: 'O(N^2) Time',
            pseudocode
          });
        }
      }
      
      // End of pass: last element is sorted
      arr[n - i - 1].state = 'sorted';
      steps.push({
        type: 'sort_pass_end',
        items: arr.map((item, idx) => ({
          ...item,
          state: idx >= n - i - 1 ? 'sorted' : 'normal'
        })),
        highlightedLines: [1],
        explanation: `End of Pass ${i + 1}. Node ${arr[n - i - 1].value} is settled at its final sorted position.`,
        complexity: 'O(N^2) Time',
        pseudocode
      });

      if (!swapped) break; // Optimized break
    }

    // Fully sorted
    steps.push({
      type: 'sort_complete',
      items: arr.map(item => ({ ...item, state: 'sorted' })),
      highlightedLines: [5],
      explanation: `Bubble Sort complete! Entire array is sorted.`,
      complexity: 'O(N^2) Worst / O(N) Best',
      pseudocode
    });

    this.items = arr;
    return steps;
  }

  quickSort() {
    const steps = [];
    const arr = this.items.map(item => ({ ...item }));
    const pseudocode = this.getPseudocode('quick');

    steps.push({
      type: 'sort_init',
      items: arr.map(item => ({ ...item, state: 'normal' })),
      highlightedLines: [1],
      explanation: `Starting Quick Sort on array.`,
      complexity: 'O(N log N) Avg / O(N^2) Worst',
      pseudocode
    });

    const runQuickSort = (low, high) => {
      if (low < high) {
        const pIdx = partition(low, high);
        runQuickSort(low, pIdx - 1);
        runQuickSort(pIdx + 1, high);
      } else if (low >= 0 && low < arr.length) {
        // single element is sorted
        arr[low].state = 'sorted';
      }
    };

    const partition = (low, high) => {
      const pivotVal = arr[high].value;
      arr[high].state = 'pivot';

      steps.push({
        type: 'quick_pivot',
        items: arr.map((item, idx) => ({
          ...item,
          state: idx === high ? 'pivot' : (item.state === 'sorted' ? 'sorted' : 'normal')
        })),
        highlightedLines: [2, 3],
        explanation: `Chosen pivot value ${pivotVal} at index ${high}.`,
        complexity: 'O(N log N) Time',
        pseudocode
      });

      let i = low - 1;
      for (let j = low; j < high; j++) {
        // Compare
        steps.push({
          type: 'quick_compare',
          items: arr.map((item, idx) => {
            if (idx === high) return { ...item, state: 'pivot' };
            if (idx === j) return { ...item, state: 'comparing' };
            if (idx === i) return { ...item, state: 'active' }; // tracker pointer
            return item;
          }),
          highlightedLines: [4],
          explanation: `Comparing item index ${j} (${arr[j].value}) with pivot (${pivotVal}).`,
          complexity: 'O(N log N) Time',
          pseudocode
        });

        if (arr[j].value < pivotVal) {
          i++;
          const temp = arr[i];
          arr[i] = arr[j];
          arr[j] = temp;

          steps.push({
            type: 'quick_swap',
            items: arr.map((item, idx) => {
              if (idx === high) return { ...item, state: 'pivot' };
              if (idx === i || idx === j) return { ...item, state: 'swapping' };
              return item;
            }),
            highlightedLines: [5, 6],
            explanation: `Since ${arr[i].value} < ${pivotVal}, increment pointer to index ${i} and swap values.`,
            complexity: 'O(N log N) Time',
            pseudocode
          });
        }
      }

      // Swap pivot into place
      const tempVal = arr[i + 1];
      arr[i + 1] = arr[high];
      arr[high] = tempVal;
      arr[i + 1].state = 'sorted';

      steps.push({
        type: 'quick_partition_end',
        items: arr.map((item, idx) => {
          if (idx === i + 1) return { ...item, state: 'sorted' };
          return item;
        }),
        highlightedLines: [7, 8],
        explanation: `Placed pivot ${pivotVal} into its final sorted position at index ${i + 1}. Left partition < ${pivotVal}, Right partition >= ${pivotVal}.`,
        complexity: 'O(N log N) Time',
        pseudocode
      });

      return i + 1;
    };

    runQuickSort(0, arr.length - 1);

    // Finalize
    steps.push({
      type: 'sort_complete',
      items: arr.map(item => ({ ...item, state: 'sorted' })),
      highlightedLines: [9],
      explanation: `Quick Sort complete! Array fully sorted.`,
      complexity: 'O(N log N) Average',
      pseudocode
    });

    this.items = arr;
    return steps;
  }

  mergeSort() {
    const steps = [];
    const arr = this.items.map(item => ({ ...item }));
    const pseudocode = this.getPseudocode('merge');

    steps.push({
      type: 'sort_init',
      items: arr.map(item => ({ ...item, state: 'normal' })),
      highlightedLines: [1],
      explanation: `Starting Merge Sort. Divide and Conquer approach.`,
      complexity: 'O(N log N) Time / O(N) Space',
      pseudocode
    });

    const runMergeSort = (l, r) => {
      if (l < r) {
        const m = Math.floor((l + r) / 2);
        
        steps.push({
          type: 'merge_split',
          items: arr.map((item, idx) => ({
            ...item,
            state: idx >= l && idx <= m ? 'comparing' : (idx > m && idx <= r ? 'active' : 'normal')
          })),
          highlightedLines: [2, 3, 4],
          explanation: `Splitting subarray [${l}...${r}] at midpoint ${m}.`,
          complexity: 'O(N log N) Time',
          pseudocode
        });

        runMergeSort(l, m);
        runMergeSort(m + 1, r);
        merge(l, m, r);
      }
    };

    const merge = (l, m, r) => {
      const leftSize = m - l + 1;
      const rightSize = r - m;

      const L = [];
      const R = [];

      for (let i = 0; i < leftSize; i++) L.push(arr[l + i]);
      for (let j = 0; j < rightSize; j++) R.push(arr[m + 1 + j]);

      let i = 0, j = 0, k = l;

      while (i < leftSize && j < rightSize) {
        steps.push({
          type: 'merge_compare',
          items: arr.map((item, idx) => ({
            ...item,
            state: idx === l + i || idx === m + 1 + j ? 'comparing' : 'normal'
          })),
          highlightedLines: [5],
          explanation: `Merging: Comparing left element ${L[i].value} and right element ${R[j].value}.`,
          complexity: 'O(N) Merge Time',
          pseudocode
        });

        if (L[i].value <= R[j].value) {
          arr[k] = L[i];
          i++;
        } else {
          arr[k] = R[j];
          j++;
        }
        k++;
      }

      while (i < leftSize) {
        arr[k] = L[i];
        i++;
        k++;
      }

      while (j < rightSize) {
        arr[k] = R[j];
        j++;
        k++;
      }

      // Mark this segment as temporarily sorted
      steps.push({
        type: 'merge_merged',
        items: arr.map((item, idx) => ({
          ...item,
          state: idx >= l && idx <= r ? 'sorted' : 'normal'
        })),
        highlightedLines: [6],
        explanation: `Merged segment [${l}...${r}] in sorted order.`,
        complexity: 'O(N) Merge Time',
        pseudocode
      });
    };

    runMergeSort(0, arr.length - 1);

    steps.push({
      type: 'sort_complete',
      items: arr.map(item => ({ ...item, state: 'sorted' })),
      highlightedLines: [7],
      explanation: `Merge Sort complete! Array fully sorted.`,
      complexity: 'O(N log N) Time',
      pseudocode
    });

    this.items = arr;
    return steps;
  }

  getPseudocode(op) {
    if (op === 'bubble') {
      return [
        "function bubbleSort(array):",
        "  for i = 0 to array.length - 1:",
        "    for j = 0 to array.length - i - 2:",
        "      if array[j] > array[j+1]:",
        "        swap(array[j], array[j+1])",
        "  return array"
      ];
    } else if (op === 'quick') {
      return [
        "function quickSort(arr, low, high):",
        "  if low < high:",
        "    pivot = choosePivot(arr, high)",
        "    pIdx = partition(arr, low, high, pivot)",
        "    quickSort(arr, low, pIdx - 1)",
        "    quickSort(arr, pIdx + 1, high)",
        "function partition(arr, low, high, pivot):",
        "  // rearranges array around pivot",
        "  return pivotFinalIndex"
      ];
    } else {
      return [
        "function mergeSort(arr, l, r):",
        "  if l < r:",
        "    m = (l + r) / 2",
        "    mergeSort(arr, l, m)",
        "    mergeSort(arr, m + 1, r)",
        "    merge(arr, l, m, r) // sorts and merges halves"
      ];
    }
  }
}
