import { StackEngine, QueueEngine, LinkedListEngine, BstEngine, GraphEngine, SortingEngine } from '../dsa';
import { VirtualKeyboard } from './keyboard';

export class HUDController {
  constructor(animator, visualEngine) {
    this.animator = animator;
    this.visualEngine = visualEngine;
    
    // Initialize engines
    this.engines = {
      stack: new StackEngine(),
      queue: new QueueEngine(),
      linkedlist: new LinkedListEngine(),
      bst: new BstEngine(),
      graph: new GraphEngine(),
      sorting: new SortingEngine()
    };

    this.currentTopic = 'stack';
    this.steps = [];
    this.currentStepIndex = 0;
    this.isPlaying = false;
    this.playSpeed = 1.0; // speed multiplier
    this.lastStepTime = 0;

    // Cache DOM Elements
    this.cacheDOMElements();
    this.setupEventListeners();

    // Initialize virtual keyboard for gesture text typing
    this.virtualKeyboard = new VirtualKeyboard();
  }

  cacheDOMElements() {
    this.lessonItems = document.querySelectorAll('.lesson-item');
    this.ctrlGroups = document.querySelectorAll('.ctrl-group');
    this.topicTitle = document.getElementById('hud-topic-title');
    this.complexityLabel = document.getElementById('hud-complexity');
    this.explanationText = document.getElementById('hud-explanation-text');
    this.pseudocodeBox = document.getElementById('pseudocode-box');
    
    // Playback controls
    this.btnPrev = document.getElementById('btn-prev');
    this.btnPlay = document.getElementById('btn-play');
    this.btnNext = document.getElementById('btn-next');
    this.iconPlay = document.getElementById('icon-play');
    this.iconPause = document.getElementById('icon-pause');
    
    // Scrubber & Speed
    this.sliderTimeline = document.getElementById('timeline-slider');
    this.lblCurrentStep = document.getElementById('current-step-label');
    this.lblTotalSteps = document.getElementById('total-steps-label');
    this.sliderSpeed = document.getElementById('speed-slider');
    this.lblSpeed = document.getElementById('speed-label');

    // Dashboard & Home UI overlays
    this.btnHome = document.getElementById('btn-home');
    this.dashboardOverlay = document.getElementById('dashboard-overlay');
    this.hudOverlay = document.getElementById('hud-overlay');
    this.lessonDeck = document.getElementById('lesson-deck');
    this.gestureGuide = document.getElementById('gesture-guide');
    this.topicCards = document.querySelectorAll('.topic-card');

    // Command Bar & Focus mode elements
    this.btnFocus = document.getElementById('btn-focus');
    this.commandBar = document.getElementById('command-bar');
    this.btnCmdEnter = document.getElementById('btn-cmd-enter');
  }

  setupEventListeners() {
    // Topic Navigation
    this.lessonItems.forEach(item => {
      item.addEventListener('click', () => {
        this.selectTopic(item.dataset.topic);
      });
    });

    // Dashboard Card selection clicks
    this.topicCards.forEach(card => {
      card.addEventListener('click', () => {
        this.openLab(card.dataset.topic);
      });
    });

    // Home / Dashboard button click
    this.btnHome.addEventListener('click', () => {
      this.closeLab();
    });

    // Playback control clicks
    if (this.btnPlay) this.btnPlay.addEventListener('click', this.togglePlay.bind(this));
    if (this.btnPrev) this.btnPrev.addEventListener('click', this.stepBackward.bind(this));
    if (this.btnNext) this.btnNext.addEventListener('click', this.stepForward.bind(this));
    
    // Timeline scrubber scrubbing
    this.sliderTimeline.addEventListener('input', (e) => {
      this.pause();
      this.goToStep(parseInt(e.target.value));
    });

    // Speed adjustment
    this.sliderSpeed.addEventListener('input', (e) => {
      this.playSpeed = parseFloat(e.target.value);
      this.lblSpeed.textContent = this.playSpeed.toFixed(1);
    });

    // Wire Interactive Engine Buttons
    // 1. Stack
    document.getElementById('stack-push').addEventListener('click', () => {
      const val = document.getElementById('stack-input').value.trim() || Math.floor(Math.random() * 90 + 9);
      document.getElementById('stack-input').value = '';
      this.loadSteps(this.engines.stack.push(val));
    });
    document.getElementById('stack-pop').addEventListener('click', () => {
      this.loadSteps(this.engines.stack.pop());
    });
    document.getElementById('stack-clear').addEventListener('click', () => {
      this.loadSteps(this.engines.stack.clear());
    });

    // 2. Queue
    document.getElementById('queue-enqueue').addEventListener('click', () => {
      const val = document.getElementById('queue-input').value.trim() || Math.floor(Math.random() * 90 + 9);
      document.getElementById('queue-input').value = '';
      this.loadSteps(this.engines.queue.enqueue(val));
    });
    document.getElementById('queue-dequeue').addEventListener('click', () => {
      this.loadSteps(this.engines.queue.dequeue());
    });
    document.getElementById('queue-clear').addEventListener('click', () => {
      this.loadSteps(this.engines.queue.clear());
    });

    // 3. LinkedList
    document.getElementById('ll-insert').addEventListener('click', () => {
      const val = document.getElementById('ll-input').value.trim() || Math.floor(Math.random() * 90 + 9);
      const idxInput = document.getElementById('ll-index').value;
      const idx = idxInput !== '' ? parseInt(idxInput) : null;
      document.getElementById('ll-input').value = '';
      document.getElementById('ll-index').value = '';
      this.loadSteps(this.engines.linkedlist.insert(val, idx));
    });
    document.getElementById('ll-delete').addEventListener('click', () => {
      const idxInput = document.getElementById('ll-index').value;
      const idx = idxInput !== '' ? parseInt(idxInput) : 0;
      document.getElementById('ll-index').value = '';
      this.loadSteps(this.engines.linkedlist.delete(idx));
    });
    document.getElementById('ll-clear').addEventListener('click', () => {
      this.loadSteps(this.engines.linkedlist.clear());
    });

    // 4. BST
    document.getElementById('bst-insert').addEventListener('click', () => {
      const valInput = document.getElementById('bst-input').value;
      const val = valInput !== '' ? parseInt(valInput) : Math.floor(Math.random() * 90 + 9);
      document.getElementById('bst-input').value = '';
      this.loadSteps(this.engines.bst.insert(val));
    });
    document.getElementById('bst-search').addEventListener('click', () => {
      const valInput = document.getElementById('bst-input').value;
      if (valInput === '') return;
      document.getElementById('bst-input').value = '';
      this.loadSteps(this.engines.bst.search(parseInt(valInput)));
    });
    document.getElementById('bst-inorder').addEventListener('click', () => {
      this.loadSteps(this.engines.bst.runTraversal('inorder'));
    });
    document.getElementById('bst-preorder').addEventListener('click', () => {
      this.loadSteps(this.engines.bst.runTraversal('preorder'));
    });
    document.getElementById('bst-postorder').addEventListener('click', () => {
      this.loadSteps(this.engines.bst.runTraversal('postorder'));
    });
    document.getElementById('bst-clear').addEventListener('click', () => {
      this.loadSteps(this.engines.bst.clear());
    });

    // 5. Graph
    document.getElementById('graph-bfs').addEventListener('click', () => {
      this.loadSteps(this.engines.graph.bfs('A'));
    });
    document.getElementById('graph-dfs').addEventListener('click', () => {
      this.loadSteps(this.engines.graph.dfs('A'));
    });
    document.getElementById('graph-random').addEventListener('click', () => {
      this.engines.graph.generateRandomGraph();
      // Trigger a default display
      this.loadSteps([{
        type: 'reset',
        nodes: this.engines.graph.nodes.map(n => ({ ...n, state: 'normal' })),
        edges: this.engines.graph.edges.map(e => ({ ...e, state: 'normal' })),
        queue: [],
        visited: [],
        highlightedLines: [0],
        explanation: 'Random Graph generated. Click BFS or DFS to traverse.',
        complexity: 'O(V + E) Traversals',
        pseudocode: this.engines.graph.getPseudocode('bfs')
      }]);
    });

    // 6. Sorting
    document.getElementById('sort-run').addEventListener('click', () => {
      const alg = document.getElementById('sort-algorithm').value;
      if (alg === 'bubble') {
        this.loadSteps(this.engines.sorting.bubbleSort());
      } else if (alg === 'quick') {
        this.loadSteps(this.engines.sorting.quickSort());
      } else if (alg === 'merge') {
        this.loadSteps(this.engines.sorting.mergeSort());
      }
    });
    document.getElementById('sort-shuffle').addEventListener('click', () => {
      this.loadSteps(this.engines.sorting.shuffle());
    });

    // Command input entry triggers
    this.btnCmdEnter.addEventListener('click', this.executeCommand.bind(this));
    this.commandBar.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        this.executeCommand();
      }
    });

    // Focus Mode click trigger
    this.btnFocus.addEventListener('click', this.toggleFocusMode.bind(this));

    // Global keyboard shortcuts for playback controls (working alongside gestures)
    window.addEventListener('keydown', (e) => {
      // Ignore if user is actively typing in any input field
      if (document.activeElement && ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
        return;
      }

      if (e.code === 'Space') {
        // Skip toggle play if space is being used to simulate hands
        if (this.handSimulator && this.handSimulator.isSpaceActive) {
          return;
        }
        e.preventDefault();
        this.togglePlay();
      } else if (e.code === 'ArrowRight') {
        e.preventDefault();
        this.stepForward();
      } else if (e.code === 'ArrowLeft') {
        e.preventDefault();
        this.stepBackward();
      } else if (e.code === 'Escape') {
        e.preventDefault();
        this.closeLab();
      }
    });
  }

  selectTopic(topic) {
    this.currentTopic = topic;
    this.pause();

    // Toggle active sidebar items
    this.lessonItems.forEach(item => {
      if (item.dataset.topic === topic) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });

    // Toggle interactive input forms
    this.ctrlGroups.forEach(group => {
      if (group.dataset.topic === topic) {
        group.classList.add('active');
      } else {
        group.classList.remove('remove'); // Reset classes
        group.classList.remove('active');
      }
    });

    // Setup Topic HUD Header, Descriptions and Complexities
    this.topicTitle.textContent = topic.toUpperCase().replace('LINKEDLIST', 'LINKED LIST');
    this.animator.clearAll();

    // Spawn initial layout configurations on topic switch
    let initialSteps = [];
    if (topic === 'stack') {
      this.complexityLabel.textContent = 'O(1) PUSH / POP';
      initialSteps = [{
        type: 'init',
        items: [],
        explanation: 'Empty stack initialized. Enter a value and click Push to append items floating on top.',
        highlightedLines: [0],
        pseudocode: this.engines.stack.getPseudocode('push')
      }];
    } 
    else if (topic === 'queue') {
      this.complexityLabel.textContent = 'O(1) ENQUEUE / DEQUEUE';
      initialSteps = [{
        type: 'init',
        items: [],
        explanation: 'Empty Queue initialized. Enqueued items enter from the right (rear) and exit from the left (front).',
        highlightedLines: [0],
        pseudocode: this.engines.queue.getPseudocode('enqueue')
      }];
    } 
    else if (topic === 'linkedlist') {
      this.complexityLabel.textContent = 'O(N) TRAVERSE / O(1) INSERT';
      initialSteps = [{
        type: 'init',
        items: [],
        explanation: 'Empty Linked List initialized. Try inserting a node at index 0 or index 1.',
        highlightedLines: [0],
        pseudocode: this.engines.linkedlist.getPseudocode('insert')
      }];
    } 
    else if (topic === 'bst') {
      this.complexityLabel.textContent = 'O(LOG N) AVG / O(N) WORST';
      initialSteps = [{
        type: 'init',
        nodes: [],
        explanation: 'Empty BST. Inserting nodes will build a spatial balanced parent-child tree hierarchy.',
        highlightedLines: [0],
        pseudocode: this.engines.bst.getPseudocode('insert')
      }];
    } 
    else if (topic === 'graph') {
      this.complexityLabel.textContent = 'O(V + E) TRAVERSALS';
      initialSteps = [{
        type: 'init',
        nodes: this.engines.graph.nodes.map(n => ({ ...n, state: 'normal' })),
        edges: this.engines.graph.edges.map(e => ({ ...e, state: 'normal' })),
        queue: [],
        visited: [],
        explanation: 'Graph layout active. Start BFS or DFS to watch lights traverse through edges.',
        highlightedLines: [0],
        pseudocode: this.engines.graph.getPseudocode('bfs')
      }];
    } 
    else if (topic === 'sorting') {
      this.complexityLabel.textContent = 'O(N LOG N) EFFICIENT';
      initialSteps = [{
        type: 'init',
        items: this.engines.sorting.items.map(item => ({ ...item, state: 'normal' })),
        explanation: 'Array of unsorted columns active. Shuffle values or click Sort to see sorting algorithms.',
        highlightedLines: [0],
        pseudocode: this.engines.sorting.getPseudocode('bubble')
      }];
    }

    this.loadSteps(initialSteps);
  }

  openLab(topic) {
    this.selectTopic(topic);
    this.dashboardOverlay.classList.add('hidden');
    this.hudOverlay.classList.remove('hidden');
    this.hudOverlay.classList.add('sidebar-hidden');
    if (this.lessonDeck) this.lessonDeck.classList.add('hidden');
    if (this.gestureGuide) this.gestureGuide.classList.remove('hidden');
    
    // Show 3D control buttons
    if (this.animator.uiButtonsGroup) {
      this.animator.uiButtonsGroup.visible = true;
    }
  }

  closeLab() {
    this.pause();
    this.dashboardOverlay.classList.remove('hidden');
    this.hudOverlay.classList.add('hidden');
    this.hudOverlay.classList.remove('sidebar-hidden');
    if (this.lessonDeck) this.lessonDeck.classList.remove('hidden');
    if (this.gestureGuide) this.gestureGuide.classList.add('hidden');
    
    // Hide virtual keyboard if visible
    if (this.virtualKeyboard) {
      this.virtualKeyboard.hide();
    }
    
    // Disable focus mode when leaving lab
    if (this.btnFocus.classList.contains('active')) {
      this.toggleFocusMode();
    }
    
    // Hide 3D control buttons
    if (this.animator.uiButtonsGroup) {
      this.animator.uiButtonsGroup.visible = false;
    }
    
    this.animator.clearAll();
  }

  toggleFocusMode() {
    const active = this.btnFocus.classList.toggle('active');
    this.btnFocus.querySelector('span').textContent = active ? 'FOCUS MODE: ON' : 'FOCUS MODE: OFF';
    if (this.visualEngine) {
      this.visualEngine.setFocusMode(active);
    }
  }

  executeCommand() {
    const rawInput = this.commandBar.value.trim();
    if (!rawInput) return;
    this.commandBar.value = '';

    const text = rawInput.toLowerCase();
    
    // 1. Stack Commands
    if (this.currentTopic === 'stack') {
      const pushMatch = text.match(/^push\s+(\w+)$/);
      if (pushMatch) {
        this.loadSteps(this.engines.stack.push(pushMatch[1]));
        return;
      }
      if (text === 'pop') {
        this.loadSteps(this.engines.stack.pop());
        return;
      }
    }

    // 2. Queue Commands
    if (this.currentTopic === 'queue') {
      const enqueueMatch = text.match(/^enqueue\s+(\w+)$/);
      if (enqueueMatch) {
        this.loadSteps(this.engines.queue.enqueue(enqueueMatch[1]));
        return;
      }
      if (text === 'dequeue') {
        this.loadSteps(this.engines.queue.dequeue());
        return;
      }
    }

    // 3. LinkedList Commands
    if (this.currentTopic === 'linkedlist') {
      const insertMatch = text.match(/^insert\s+(\w+)(?:\s+(\d+))?$/);
      if (insertMatch) {
        const val = insertMatch[1];
        const idx = insertMatch[2] !== undefined ? parseInt(insertMatch[2]) : null;
        this.loadSteps(this.engines.linkedlist.insert(val, idx));
        return;
      }
      const deleteMatch = text.match(/^delete\s+(\d+)$/);
      if (deleteMatch) {
        this.loadSteps(this.engines.linkedlist.delete(parseInt(deleteMatch[1])));
        return;
      }
    }

    // 4. BST Commands
    if (this.currentTopic === 'bst') {
      // Create BST with list of numbers
      const createMatch = text.match(/^create\s+(?:tree|bst)\s+with\s+(.+)$/);
      if (createMatch) {
        const nums = createMatch[1].trim().split(/\s+/).map(Number).filter(n => !isNaN(n));
        this.engines.bst.clear();
        let allSteps = [];
        nums.forEach(num => {
          allSteps = allSteps.concat(this.engines.bst.insert(num));
        });
        this.loadSteps(allSteps);
        return;
      }
      const insertMatch = text.match(/^insert\s+(\d+)$/);
      if (insertMatch) {
        this.loadSteps(this.engines.bst.insert(parseInt(insertMatch[1])));
        return;
      }
      const searchMatch = text.match(/^search\s+(\d+)$/);
      if (searchMatch) {
        this.loadSteps(this.engines.bst.search(parseInt(searchMatch[1])));
        return;
      }
      const traverseMatch = text.match(/^show\s+(inorder|preorder|postorder)$/);
      if (traverseMatch) {
        this.loadSteps(this.engines.bst.runTraversal(traverseMatch[1]));
        return;
      }
    }

    // 5. Graph Commands
    if (this.currentTopic === 'graph') {
      const traverseMatch = text.match(/^show\s+(bfs|dfs)$/);
      if (traverseMatch) {
        const type = traverseMatch[1];
        if (type === 'bfs') {
          this.loadSteps(this.engines.graph.bfs('A'));
        } else {
          this.loadSteps(this.engines.graph.dfs('A'));
        }
        return;
      }
      if (text === 'random' || text === 'create graph') {
        this.engines.graph.generateRandomGraph();
        this.loadSteps([{
          type: 'reset',
          nodes: this.engines.graph.nodes.map(n => ({ ...n, state: 'normal' })),
          edges: this.engines.graph.edges.map(e => ({ ...e, state: 'normal' })),
          queue: [],
          visited: [],
          highlightedLines: [0],
          explanation: 'Random Graph generated.',
          complexity: 'O(V + E)',
          pseudocode: this.engines.graph.getPseudocode('bfs')
        }]);
        return;
      }
    }

    // 6. Sorting Commands
    if (this.currentTopic === 'sorting') {
      const sortMatch = text.match(/^sort\s+(bubble|quick|merge)$/);
      if (sortMatch) {
        const alg = sortMatch[1];
        if (alg === 'bubble') this.loadSteps(this.engines.sorting.bubbleSort());
        else if (alg === 'quick') this.loadSteps(this.engines.sorting.quickSort());
        else if (alg === 'merge') this.loadSteps(this.engines.sorting.mergeSort());
        return;
      }
      if (text === 'shuffle') {
        this.loadSteps(this.engines.sorting.shuffle());
        return;
      }
    }

    // 7. General Commands
    if (text === 'clear' || text === 'reset') {
      this.loadSteps(this.engines[this.currentTopic].clear());
      return;
    }

    // Command fallback error
    this.explanationText.textContent = `Command not recognized. Try examples like: 'push 10', 'enqueue 15', 'insert 25 1', 'create tree with 12 8 20', 'show inorder', 'show bfs', or 'sort bubble'.`;
  }

  loadSteps(steps) {
    if (!steps || steps.length === 0) return;
    this.steps = steps;
    this.currentStepIndex = 0;
    
    // Update timeline DOM constraints
    this.sliderTimeline.max = steps.length - 1;
    this.sliderTimeline.value = 0;
    this.lblTotalSteps.textContent = steps.length - 1;

    this.goToStep(0);
  }

  goToStep(index) {
    if (index < 0 || index >= this.steps.length) return;
    this.currentStepIndex = index;
    this.sliderTimeline.value = index;
    this.lblCurrentStep.textContent = index;

    const step = this.steps[index];

    // Trigger visualizer update
    this.animator.syncState(step, this.currentTopic);

    // Update Text panel
    if (step.explanation) {
      this.explanationText.textContent = step.explanation;
    }
    if (step.complexity) {
      this.complexityLabel.textContent = step.complexity.toUpperCase();
    }

    // Render pseudocode list with highlighted lines
    if (step.pseudocode) {
      this.renderPseudocode(step.pseudocode, step.highlightedLines || []);
    }
  }

  renderPseudocode(lines, highlights) {
    this.pseudocodeBox.innerHTML = '';
    lines.forEach((line, idx) => {
      const span = document.createElement('span');
      span.className = 'pseudocode-line';
      span.textContent = line;
      if (highlights.includes(idx)) {
        span.classList.add('highlight');
      }
      this.pseudocodeBox.appendChild(span);
    });
  }

  // Playback control functions
  togglePlay() {
    if (this.isPlaying) {
      this.pause();
    } else {
      this.play();
    }
  }

  play() {
    if (this.steps.length <= 1) return;
    this.isPlaying = true;
    if (this.iconPlay) this.iconPlay.classList.add('hidden');
    if (this.iconPause) this.iconPause.classList.remove('hidden');
  }

  pause() {
    this.isPlaying = false;
    if (this.iconPlay) this.iconPlay.classList.remove('hidden');
    if (this.iconPause) this.iconPause.classList.add('hidden');
  }

  stepForward() {
    this.pause();
    if (this.currentStepIndex < this.steps.length - 1) {
      this.goToStep(this.currentStepIndex + 1);
    }
  }

  stepBackward() {
    this.pause();
    if (this.currentStepIndex > 0) {
      this.goToStep(this.currentStepIndex - 1);
    }
  }

  rearrangeNodes() {
    const topic = this.currentTopic;
    if (!['stack', 'queue', 'linkedlist', 'sorting'].includes(topic)) return;

    // Collect all active node groups from animator
    const activeNodes = [];
    this.animator.nodesMap.forEach((nodeGroup, id) => {
      // Find the value from the label element
      const label = nodeGroup.getObjectByName('label');
      const value = label ? parseInt(label.element.textContent) : 0;
      activeNodes.push({
        id,
        value,
        x: nodeGroup.position.x,
        y: nodeGroup.position.y
      });
    });

    if (activeNodes.length === 0) return;

    // Sort by coordinate depending on topic layout
    if (topic === 'stack') {
      // Stack is vertical: bottom to top
      activeNodes.sort((a, b) => a.y - b.y);
    } else {
      // Others are horizontal: left to right
      activeNodes.sort((a, b) => a.x - b.x);
    }

    // Update the engine's items array
    const engine = this.engines[topic];
    if (engine) {
      engine.items = activeNodes.map(node => ({
        id: node.id,
        value: node.value,
        state: 'normal'
      }));

      // Update target layout positions in animator so they snap into slots
      engine.items.forEach((item, index) => {
        const targetPos = this.animator.calculateLayoutPosition(topic, index, engine.items.length);
        const nodeGroup = this.animator.nodesMap.get(item.id);
        if (nodeGroup && !nodeGroup.userData.isGrabbed) {
          nodeGroup.userData.targetPos.copy(targetPos);
        }
      });

      // Special check for sorting game victory!
      if (topic === 'sorting') {
        const isSorted = engine.items.every((item, i) => i === 0 || item.value >= engine.items[i - 1].value);
        if (isSorted) {
          if (this.explanationText) {
            this.explanationText.innerHTML = "<span style='color: #10b981; font-weight: bold; text-shadow: 0 0 10px rgba(16, 185, 129, 0.4);'>🎉 VICTORY! You have successfully sorted the columns manually using gestures!</span>";
          }
          
          // Flash nodes green to celebrate victory
          engine.items.forEach(item => {
            const group = this.animator.nodesMap.get(item.id);
            if (group) {
              group.userData.targetColor.setHex(0x10b981);
              group.userData.baseColor.setHex(0x10b981);
              const label = group.getObjectByName('label');
              if (label && label.element) {
                label.element.style.borderColor = '#10b981';
              }
            }
          });
        }
      }
    }
  }

  // Hook into animation main loop to automatically play through steps
  update(time) {
    if (this.isPlaying) {
      // Step duration is adjusted dynamically by the speed slider
      const stepDuration = 1200 / this.playSpeed;
      if (time - this.lastStepTime > stepDuration) {
        if (this.currentStepIndex < this.steps.length - 1) {
          this.goToStep(this.currentStepIndex + 1);
          this.lastStepTime = time;
        } else {
          this.pause(); // Stop when reaching the end
        }
      }
    } else {
      // Keep updating clock to prevent instantaneous jumping on play restart
      this.lastStepTime = time;
    }
  }
}
