import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        width, height = letter # 612 x 792
        
        # Cover page design (Page 1)
        if self._pageNumber == 1:
            # Dark space background
            self.setFillColor(colors.HexColor("#050811")) # Midnight Blue
            self.rect(0, 0, width, height, fill=True, stroke=False)
            
            # Glowing borders
            self.setStrokeColor(colors.HexColor("#00f2fe")) # Cyan
            self.setLineWidth(3)
            self.line(40, 40, width - 40, 40)
            self.line(40, 40, 40, height - 40)
            
            self.setStrokeColor(colors.HexColor("#a855f7")) # Purple
            self.line(width - 40, 40, width - 40, height - 40)
            self.line(40, height - 40, width - 40, height - 40)
            
            # Draw visual node connector graphic in the background
            self.setStrokeColor(colors.HexColor("#1e293b"))
            self.setLineWidth(1.5)
            self.line(120, height - 150, 240, height - 150)
            self.line(240, height - 150, 360, height - 250)
            self.line(240, height - 150, 180, height - 280)
            
            self.setFillColor(colors.HexColor("#0f172a"))
            self.circle(120, height - 150, 16, fill=True, stroke=True)
            self.circle(240, height - 150, 20, fill=True, stroke=True)
            self.circle(360, height - 250, 16, fill=True, stroke=True)
            self.circle(180, height - 280, 16, fill=True, stroke=True)
            
            self.setFillColor(colors.HexColor("#00f2fe"))
            self.circle(120, height - 150, 5, fill=True, stroke=False)
            self.circle(360, height - 250, 5, fill=True, stroke=False)
            
            self.setFillColor(colors.HexColor("#a855f7"))
            self.circle(240, height - 150, 7, fill=True, stroke=False)
            self.circle(180, height - 280, 5, fill=True, stroke=False)
            
            self.restoreState()
            return
            
        # Standard Page Decorations
        # Header
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#0ea5e9")) # Cyan accent
        self.drawString(54, height - 45, "SPATIAL DSA TUTOR")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b")) # Slate
        self.drawRightString(width - 54, height - 45, "TECHNICAL ARCHITECTURE & DOCUMENTATION")
        
        # Header separator line
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, height - 52, width - 54, height - 52)
        
        # Footer text
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(54, 35, "Confidential - Spatial Learning Lab")
        
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(width - 54, 35, page_text)
        
        # Footer separator line
        self.line(54, 45, width - 54, 45)
        self.restoreState()

def build_pdf(filename="Spatial_DSA_Tutor_Documentation.pdf"):
    # Target letter size with 0.75-inch (54 points) left/right margins
    # top/bottom margins at 72 points to clear header and footer lines
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )

    styles = getSampleStyleSheet()

    # Define color scheme palette
    color_primary = colors.HexColor("#0ea5e9") # Cyan
    color_secondary = colors.HexColor("#a855f7") # Purple
    color_dark = colors.HexColor("#0f172a") # Slate-900
    color_text = colors.HexColor("#1e293b") # Slate-800
    color_muted = colors.HexColor("#64748b") # Slate-500
    color_bg_code = colors.HexColor("#f8fafc") # Slate-50

    # Modify existing styles to match palette
    styles['Normal'].textColor = color_text
    styles['Normal'].fontSize = 10
    styles['Normal'].leading = 14.5

    # Define custom styles
    cover_title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=34,
        textColor=colors.white,
        spaceAfter=15,
        alignment=0
    )

    cover_subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#00f2fe"), # Neon Cyan
        spaceAfter=40,
        alignment=0
    )

    cover_meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14.5,
        textColor=colors.HexColor("#94a3b8"), # Slate gray
        alignment=0
    )

    h1_style = ParagraphStyle(
        'DocH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=17,
        leading=21,
        textColor=color_dark,
        spaceBefore=16,
        spaceAfter=10,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12.5,
        leading=16,
        textColor=color_primary,
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        spaceAfter=8
    )

    body_bold_style = ParagraphStyle(
        'DocBodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    code_style = ParagraphStyle(
        'DocCode',
        parent=styles['Code'],
        fontName='Courier',
        fontSize=8,
        leading=10.5,
        textColor=color_dark,
        backColor=color_bg_code,
        borderColor=colors.HexColor("#e2e8f0"),
        borderWidth=0.5,
        borderPadding=6,
        spaceAfter=10
    )

    story = []

    # ================= PAGE 1: COVER PAGE =================
    story.append(Spacer(1, 140))
    story.append(Paragraph("SPATIAL DSA TUTOR", cover_title_style))
    story.append(Paragraph("An Immersive 3D Learning Lab with Real-Time Webcam Hand Gesture Tracking", cover_subtitle_style))
    
    # Custom colored divider line table
    divider_table = Table([[""]], colWidths=[504])
    divider_table.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 2, color_secondary),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(divider_table)
    story.append(Spacer(1, 25))

    meta_text = """
    <b>SYSTEM LEVEL DOCUMENTATION & PROJECT ANALYSIS</b><br/>
    <b>Author:</b> Antigravity Coding Assistant<br/>
    <b>Date:</b> June 11, 2026<br/>
    <b>Workspace Path:</b> <code>downfall/</code><br/>
    <b>Stack:</b> Three.js (WebGL), MediaPipe Hands API, WebXR, Vanilla CSS, Vite<br/>
    <b>Version:</b> 1.0.0
    """
    story.append(Paragraph(meta_text, cover_meta_style))
    story.append(PageBreak())

    # ================= PAGE 2: INTRODUCTION & OVERVIEW =================
    story.append(Paragraph("1. Executive Summary & Overview", h1_style))
    
    intro_p1 = """
    The <b>Spatial DSA Tutor (Immersive Learning Lab)</b> is an interactive WebGL-based educational tool designed to visualize 
    Data Structures and Algorithms (DSA) within a zero-gravity space simulation environment. By combining modern 3D graphics (Three.js), 
    computer vision hand tracking (MediaPipe Hands API), virtual reality capabilities (WebXR), and standard web technologies, 
    the project offers an engaging and highly tactile method for exploring abstract programming concepts.
    """
    story.append(Paragraph(intro_p1, body_style))

    intro_p2 = """
    Unlike traditional static text representations or 2D canvas visualizers, the Spatial DSA Tutor treats data elements 
    as physical objects. Nodes can drift, levitate, bounce, and glide based on simulated gravity and spring physics. 
    Users can interact with these components using three coexisting control systems:
    """
    story.append(Paragraph(intro_p2, body_style))

    control_text = """
    • <b>Webcam Hand Gestures:</b> Real-time hand tracking maps the user's hand coordinates to 3D space, allowing users to pinch and drag nodes, zoom using left-hand dollying, and perform dual-hand transformations (scaling and rotation).<br/><br/>
    • <b>Desktop Cyber-Glove Simulator:</b> A physics-based mouse and keyboard fallback system that simulates a 3D hand in the classroom, rendering a virtual glove to maintain the zero-gravity interaction experience even without a webcam.<br/><br/>
    • <b>Physical Controls & Shortcuts:</b> Standard keyboard hotkeys (Space for Play/Pause, ArrowRight/Left for steps) and physical mouse clicks/drags to directly control orbit camera systems and drag blocks.
    """
    story.append(Paragraph(control_text, body_style))

    story.append(Spacer(1, 10))
    story.append(Paragraph("2. Technical Stack & Dependencies", h1_style))
    
    tech_p = """
    The project leverages lightweight, high-performance, and client-side dependencies to achieve real-time, low-latency, and interactive WebGL experiences without needing a heavyweight backend server. The key stack components are summarized below:
    """
    story.append(Paragraph(tech_p, body_style))

    # Tech Stack Table
    table_data = [
        [Paragraph("<b>Component</b>", body_bold_style), Paragraph("<b>Technology / Spec</b>", body_bold_style), Paragraph("<b>Description / Role</b>", body_bold_style)],
        [Paragraph("Core Render Engine", body_style), Paragraph("Three.js (^0.184.0)", body_style), Paragraph("Handles WebGL rendering, geometries, neon lighting, fog, and particle layers.", body_style)],
        [Paragraph("Overlay Badges", body_style), Paragraph("CSS2DRenderer", body_style), Paragraph("Mounts standard HTML text label badges directly above 3D node coordinates.", body_style)],
        [Paragraph("Computer Vision", body_style), Paragraph("MediaPipe Hands API", body_style), Paragraph("Extracts 21 hand skeleton joints from webcam video feed in real-time.", body_style)],
        [Paragraph("Immersive VR", body_style), Paragraph("WebXR Device API", body_style), Paragraph("Binds virtual reality rendering and controller/hand tracking sessions.", body_style)],
        [Paragraph("Frontend Styling", body_style), Paragraph("Vanilla CSS Variables", body_style), Paragraph("Renders glassmorphic control overlays and sidebar text panels.", body_style)],
        [Paragraph("Bundler / Server", body_style), Paragraph("Vite (^8.0.12)", body_style), Paragraph("High-speed build bundler and hot-module reloading dev server.", body_style)]
    ]

    t = Table(table_data, colWidths=[120, 110, 274])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('TEXTCOLOR', (0,0), (-1,0), color_dark),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('LINEABOVE', (0,0), (-1,0), 0.5, colors.HexColor("#94a3b8")),
        ('LINEBELOW', (0,0), (-1,0), 1, colors.HexColor("#475569")),
    ]))
    story.append(t)
    story.append(PageBreak())

    # ================= PAGE 3: ARCHITECTURE & DIRECTORY STRUCTURE =================
    story.append(Paragraph("3. System Architecture & Modular Layout", h1_style))
    
    arch_p = """
    The application follows a modular, decoupled architecture where the algorithm engines, the 3D visualizers, the user interfaces, and the gesture controllers interact through structured events and APIs. Below is an overview of the directory hierarchy:
    """
    story.append(Paragraph(arch_p, body_style))

    dir_code = """
downfall/
├── index.html                   # Main entry document containing overlay layouts
├── package.json                 # Dependency manager specifying Vite and Three.js
├── src/
│   ├── main.js                  # Entry script initializing engine modules
│   ├── style.css                # Glassmorphic and typographic CSS stylesheets
│   ├── dsa/                     # CORE ALGORITHM ENGINES
│   │   ├── index.js             # Exports and combines all engines
│   │   ├── bst.js               # Binary Search Tree traversal and insertion
│   │   ├── graph.js             # BFS/DFS traversals and node structures
│   │   ├── linkedList.js        # Chain nodes, insert/delete at head/index
│   │   ├── queue.js             # FIFO Queue insertion and deletion
│   │   ├── stack.js             # LIFO Stack push/pop operations
│   │   └── sorting.js           # Bubble, Quick, Merge Sort and manual sorting
│   ├── interaction/             # USER CONTROL SYSTEMS
│   │   ├── handSim.js           # Keyboard/Mouse fallback glove simulator
│   │   ├── webcamHands.js       # MediaPipe webcam keypoint tracker
│   │   └── webxr.js             # Immersive WebXR VR headset connector
│   ├── ui/                      # HUD OVERLAYS & CONTROLS
│   │   ├── hud.js               # Binds HUD buttons, command inputs, and timelines
│   │   └── keyboard.js          # On-screen keyboard for gesture text inputs
│   └── visualization/           # THREE.JS WEBGL SYSTEMS
│       ├── animator.js          # Node animations, levitations, and transitions
│       ├── engine.js            # WebGL renderer, OrbitControls, and lights
│       └── environment.js       # Starfields, holographic floor, and drift particles
    """
    story.append(Paragraph(dir_code.strip().replace(" ", "&nbsp;").replace("\n", "<br/>"), code_style))

    story.append(Paragraph("Component Relationships", h2_style))
    comp_p = """
    1. <b>Main Loop (<code>main.js</code>):</b> Initializes the <code>VisualEngine</code>, <code>ClassroomEnvironment</code>, and <code>SceneAnimator</code>. Instantiates both the <code>DesktopHandSimulator</code> (physical controls) and <code>WebcamHandsManager</code> (gesture controls). It establishes the animation loop using <code>renderer.setAnimationLoop()</code> to ensure WebXR compatibility.<br/><br/>
    2. <b>Visual Engine (<code>engine.js</code>):</b> Manages canvas containers, ambient and spotlight systems, fog levels, and orbit camera lerps. It runs both the WebGL canvas renderer and the <code>CSS2DRenderer</code> simultaneously.<br/><br/>
    3. <b>Scene Animator (<code>animator.js</code>):</b> Acts as a bridge between the abstract state of data structures and their visual representation in 3D. It manages position lerping, object levitation, dynamic node colors, and the instantiation of 3D lines/arrows representing pointers or graph edges.<br/><br/>
    4. <b>HUD Controller (<code>hud.js</code>):</b> Captures clicks on sidebar elements, handles scrubbers, command-line inputs, and speed sliders. On state change, it asks the active <code>dsa</code> engine to generate animation steps, which are then passed to the <code>SceneAnimator</code> to render.
    """
    story.append(Paragraph(comp_p, body_style))
    story.append(PageBreak())

    # ================= PAGE 4: DSA ENGINE MECHANICS =================
    story.append(Paragraph("4. DSA Engine Mechanics & Step Simulation", h1_style))
    
    eng_p = """
    Each data structure engine (located in <code>src/dsa/</code>) operates by receiving an action command (e.g. <i>push</i>, <i>insert</i>, <i>sort</i>) and generating an array of <b>animation step states</b>. Instead of executing the entire algorithm instantly, the engine returns a chronological sequence of steps, where each step defines:
    """
    story.append(Paragraph(eng_p, body_style))

    step_info = """
    • <b>Nodes/Items:</b> The current state (value, coordinates, color code) of all nodes in the scene.<br/>
    • <b>State Markers:</b> Specific labels marking nodes as <i>spawn</i>, <i>active</i>, <i>highlighted</i>, or <i>delete_lift</i>.<br/>
    • <b>Pseudocode Highlights:</b> Indices of lines in the algorithm's pseudocode that correspond to the active execution step.<br/>
    • <b>Text Explanation:</b> Context-rich explanations displayed on the HUD describing the current operation.
    """
    story.append(Paragraph(step_info, body_style))

    story.append(Paragraph("Stack & Queue Engines", h2_style))
    stack_p = """
    The <b>Stack Engine</b> (<code>stack.js</code>) manages a Last-In, First-Out (LIFO) stack. It generates steps for Push (spawning an element and moving it to the top of the tower) and Pop (lifting the top element, fading it out, and deleting it). The <b>Queue Engine</b> (<code>queue.js</code>) operates a First-In, First-Out (FIFO) queue, lining nodes up horizontally, where elements enter from the right (rear) and exit from the left (front).
    """
    story.append(Paragraph(stack_p, body_style))

    story.append(Paragraph("LinkedList Engine", h2_style))
    ll_p = """
    The <b>LinkedList Engine</b> (<code>linkedList.js</code>) allows index-based insertion and deletion. For middle-of-chain operations, it generates traversal steps that highlight each node sequentially (highlight state: <i>active</i>/<i>highlighted</i>), links the new node's next pointer to the successor, and then breaks and re-links the predecessor node to point to the new node in 3D.
    """
    story.append(Paragraph(ll_p, body_style))

    story.append(Paragraph("Binary Search Tree (BST) Engine", h2_style))
    bst_p = """
    The <b>BST Engine</b> (<code>bst.js</code>) maps integer keys to a recursive parent-child tree hierarchy. Operations include Insertion (animating traversal from the root, branching left/right based on value comparisons) and Tree Traversals (In-order, Pre-order, Post-order), where a "scanning light" animates through nodes following recursive visit orders.
    """
    story.append(Paragraph(bst_p, body_style))

    story.append(Paragraph("Graph & Sorting Engines", h2_style))
    graph_sort_p = """
    The <b>Graph Engine</b> (<code>graph.js</code>) manages nodes in 3D spaces with connecting edge vectors. It simulates Breadth-First Search (BFS) and Depth-First Search (DFS) traversals by pushing queue/stack updates and coloring visited nodes.
    The <b>Sorting Engine</b> (<code>sorting.js</code>) represents arrays as vertical columns. It supports Bubble, Quick, and Merge Sorts. In addition, it allows users to manually grab columns using webcam hand gestures or simulated hands, sorting them manually. If successfully sorted, a victory condition triggers, flashing columns in celebration green.
    """
    story.append(Paragraph(graph_sort_p, body_style))
    story.append(PageBreak())

    # ================= PAGE 5: EXECUTION GUIDE =================
    story.append(Paragraph("5. Step-by-Step Local Setup & Execution Guide", h1_style))
    
    setup_p = """
    Follow these steps to set up, run, configure, and compile the Spatial DSA Tutor on a local machine.
    """
    story.append(Paragraph(setup_p, body_style))

    story.append(Paragraph("Prerequisites", h2_style))
    prereq_p = """
    Before starting, ensure that <b>Node.js</b> (v18.0.0 or higher recommended) is installed on your operating system.
    """
    story.append(Paragraph(prereq_p, body_style))

    story.append(Paragraph("Step 1: Install Dependencies", h2_style))
    step1_p = """
    Open a terminal window in the project's root folder (containing <code>package.json</code>) and run the following command to download Vite, Three.js, and other necessary assets:
    """
    story.append(Paragraph(step1_p, body_style))
    story.append(Paragraph("npm install", code_style))

    story.append(Paragraph("Step 2: Start Development Server", h2_style))
    step2_p = """
    To start the local hot-reloading development server, run the following npm script. This spins up the server, typically bound to <code>http://localhost:5173/</code>:
    """
    story.append(Paragraph(step2_p, body_style))
    story.append(Paragraph("npm run dev", code_style))
    
    step2_note = """
    Open the output URL in a web browser. Ensure you grant camera permissions if prompted to enable real-time webcam hand tracking.
    """
    story.append(Paragraph(step2_note, body_style))

    story.append(Paragraph("Step 3: Compile for Production", h2_style))
    step3_p = """
    To bundle and compile all JavaScript, CSS, and HTML assets into a highly optimized, minified production build, run:
    """
    story.append(Paragraph(step3_p, body_style))
    story.append(Paragraph("npm run build", code_style))

    step3_note = """
    This command outputs all compiled assets to the <code>dist/</code> directory, which can be deployed to static web hosts such as Netlify, Vercel, or GitHub Pages.
    """
    story.append(Paragraph(step3_note, body_style))

    story.append(Paragraph("Step 4: Local Preview of Build", h2_style))
    step4_p = """
    To preview the compiled assets locally using a lightweight server, run the following command:
    """
    story.append(Paragraph(step4_p, body_style))
    story.append(Paragraph("npm run preview", code_style))

    story.append(PageBreak())

    # ================= PAGE 6: INTERACTIVE USER USER GUIDE =================
    story.append(Paragraph("6. Interactive Interface Guide & Control Commands", h1_style))
    
    gui_p = """
    Once the application is running, users can interact with the system using three different command methods:
    """
    story.append(Paragraph(gui_p, body_style))

    story.append(Paragraph("A. Command-Line Console Command Guide", h2_style))
    cmd_p = """
    A command bar interface (visible on the overlay HUD) allows power users to type textual operations to interact with active labs. The list of supported commands includes:
    """
    story.append(Paragraph(cmd_p, body_style))

    cmd_table_data = [
        [Paragraph("<b>Topic</b>", body_bold_style), Paragraph("<b>Command Example</b>", body_bold_style), Paragraph("<b>Execution Effect</b>", body_bold_style)],
        [Paragraph("Stack", body_style), Paragraph("<code>push 42</code>", body_style), Paragraph("Spawns a new node labeled 42 and pushes it to the stack top.", body_style)],
        [Paragraph("Stack", body_style), Paragraph("<code>pop</code>", body_style), Paragraph("Pops and animates deletion of the top node.", body_style)],
        [Paragraph("Queue", body_style), Paragraph("<code>enqueue hello</code>", body_style), Paragraph("Enqueues a node labeled 'hello' into the queue rear.", body_style)],
        [Paragraph("Queue", body_style), Paragraph("<code>dequeue</code>", body_style), Paragraph("Dequeues the front element of the queue line.", body_style)],
        [Paragraph("LinkedList", body_style), Paragraph("<code>insert a 2</code>", body_style), Paragraph("Inserts a node labeled 'a' at index 2 of the list chain.", body_style)],
        [Paragraph("LinkedList", body_style), Paragraph("<code>delete 1</code>", body_style), Paragraph("Deletes the node located at index 1.", body_style)],
        [Paragraph("BST", body_style), Paragraph("<code>create tree with 10 5 15</code>", body_style), Paragraph("Wipes current BST and inserts 10 (root), 5, and 15.", body_style)],
        [Paragraph("BST", body_style), Paragraph("<code>show inorder</code>", body_style), Paragraph("Starts inorder tree traversal, lighting nodes in order.", body_style)],
        [Paragraph("Graph", body_style), Paragraph("<code>show bfs</code>", body_style), Paragraph("Runs Breadth-First Search traversal from starting node 'A'.", body_style)],
        [Paragraph("Sorting", body_style), Paragraph("<code>sort bubble</code>", body_style), Paragraph("Triggers step-by-step Bubble Sort algorithm visualization.", body_style)],
        [Paragraph("General", body_style), Paragraph("<code>clear</code>", body_style), Paragraph("Wipes all active data structure meshes from the 3D scene.", body_style)]
    ]

    ct = Table(cmd_table_data, colWidths=[80, 150, 274])
    ct.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('TEXTCOLOR', (0,0), (-1,0), color_dark),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('LINEABOVE', (0,0), (-1,0), 0.5, colors.HexColor("#94a3b8")),
        ('LINEBELOW', (0,0), (-1,0), 1, colors.HexColor("#475569")),
    ]))
    story.append(ct)
    story.append(Spacer(1, 10))

    story.append(Paragraph("B. Keyboard Shortcuts", h2_style))
    kbd_text = """
    • <b>Space (Tap):</b> Play or pause step-by-step playback of simulation timelines.<br/>
    • <b>ArrowRight:</b> Advance one step forward in the simulation timeline.<br/>
    • <b>ArrowLeft:</b> Move one step backward in the simulation timeline.<br/>
    • <b>Escape:</b> Exit the active laboratory view and return to the main dashboard.<br/>
    • <b>Space (Hold) + Mouse Drag:</b> Move a simulated right hand (wireframe cyber-glove). Left-click to pinch/grab nodes.<br/>
    • <b>Shift + Space (Hold) + Mouse Drag:</b> Move a simulated left hand to enable dual-hand gesture operations.
    """
    story.append(Paragraph(kbd_text, body_style))

    story.append(Paragraph("C. Webcam Hand Gesture Specifications", h2_style))
    gst_text = """
    • <b>Single-Hand Pinch:</b> Brings thumb and index fingertips closer than 0.38x hand scale. Grabs a node if hovered, allowing drag-and-drop. Pinching over UI controls clicks buttons or drags sliders.<br/>
    • <b>Single-Hand Release:</b> Spreads thumb and index wider than 0.60x. Releases grabbed items, initiating inertial glide and layout snapping.<br/>
    • <b>Left-Hand Dolly Zoom:</b> Pinch left thumb/index in empty space. Move hand closer to webcam to zoom in, and pull back to zoom out.<br/>
    • <b>Dual-Hand Scale/Rotate:</b> Pinch both hands in empty space. Move hands apart or closer together to scale the data structure mesh; rotate hands relative to each other to rotate the data structure.
    """
    story.append(Paragraph(gst_text, body_style))

    # Build the document using the custom NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated {filename}")

if __name__ == '__main__':
    filename = "Spatial_DSA_Tutor_Documentation.pdf"
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    build_pdf(filename)
