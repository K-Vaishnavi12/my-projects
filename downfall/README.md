# Spatial DSA Tutor - Immersive Learning Lab

An interactive, holographic 3D learning lab built to visualize Data Structures and Algorithms (DSA) in a zero-gravity space environment. Learners can interact with nodes dynamically using real-time webcam hand gesture tracking, physical mouse, keyboard controls, or simulated fallbacks.

---

## 🚀 Technologies Used

- **Core Render Engine:** [Three.js](https://threejs.org/) (WebGL) for rendering the interactive 3D classroom grids, drifting starfields, particle glows, and node meshes.
- **Holographic Labels:** `CSS2DRenderer` for mounting responsive HTML text label badges directly above 3D meshes.
- **Webcam Hand Tracking:** [MediaPipe Hands API](https://developers.google.com/mediapipe/solutions/vision/hand_landmarker) utilizing lightweight, real-time tracking (`modelComplexity: 0`) for jitter-free, low-latency performance.
- **Frontend & Styling:** HTML5, CSS Variables, glassmorphic UI overlay panels, premium typography (Outfit, Inter, JetBrains Mono), and CSS animations.
- **Bundler & Dev Server:** [Vite](https://vitejs.dev/) for extremely fast module replacement and builds.

---

## 🎮 Interaction & Control Schemes

The Spatial DSA Tutor features fully coexisting control systems. You can seamlessly switch between hand gestures, mouse drags, and keyboard hotkeys.

### 1. Webcam Hand Gestures
Webcam gestures project absolute coordinates to the screen using your hand skeleton.

- **Pinch (Thumb + Index Fingertip closer than 0.38x hand scale):**
  - Hover over a node (outlines in gold) and pinch to **grab and drag** the block.
  - Pinch over floating UI panels to click buttons or drag range sliders.
- **Release (Thumb + Index Fingertip spread wider than 0.60x hand scale):**
  - Releases grabbed nodes, triggering zero-gravity momentum glide and snapping them to layout slots.
  - *Debounce Buffer:* Features a 10-frame grace period to prevent node drops if tracking flickers.
- **Left-Hand Pinch Zoom (Dolly):**
  - Pinch your left thumb and index fingers together (without holding a node) and move your hand closer to or further from the camera to zoom.
- **Dual-Hand Transform:**
  - Pinch both hands in empty space:
    - **Scale:** Move hands closer or further apart to scale the data structure.
    - **Rotate:** Rotate your hands relative to each other to spin the structure.
- **3D Button Poking:**
  - Move either index fingertip inside the expanded bounding box of 3D buttons (such as the `▼ NEXT STEP` arrow) to trigger them.

### 2. Physical Mouse Controls
- **Rotate Camera:** Left-Click and drag on empty space.
- **Pan Camera:** Right-Click and drag.
- **Zoom Camera:** Use the scroll wheel.
- **Direct Block Drag-and-Drop:** Left-Click directly on any 3D node and drag to move it. Releasing the mouse clicks snaps the node in place and updates the underlying algorithm engine. Camera rotation is locked automatically while dragging blocks.

### 3. Keyboard Shortcuts
- **Space (Tap):** Play / Pause the step-by-step algorithms simulation.
- **ArrowRight:** Step forward (Next Step).
- **ArrowLeft:** Step backward (Previous Step).
- **Escape:** Exit the active lab and return to the main dashboard.
- **Space (Hold) + Mouse Drag:** Fallback simulated right hand (wireframe cyber-glove). Left-Click to grab.
- **Shift + Space (Hold) + Mouse Drag:** Fallback simulated left hand (activates dual-hand scale and rotation controls).
- **Scroll Wheel (when Space is held):** Push or pull the simulated hand's depth in 3D space.
- *Focus Safeguard:* Keyboard shortcuts are disabled automatically when typing inside text inputs or using the virtual keyboard.

---

## 🛠️ Local Setup & Commands

### Prerequisites
Ensure you have [Node.js](https://nodejs.org/) installed.

### Installation
Clone the project and install dependencies:
```bash
npm install
```

### Start Development Server
Runs the dev server locally (default on `http://localhost:5173/`):
```bash
npm run dev
```

### Build for Production
Compiles and minifies assets into the `dist` directory:
```bash
npm run build
```
