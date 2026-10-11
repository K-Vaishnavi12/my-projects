import * as THREE from 'three';

export class DesktopHandSimulator {
  constructor(scene, camera, renderer, animEngine) {
    this.scene = scene;
    this.camera = camera;
    this.renderer = renderer;
    this.animEngine = animEngine; // SceneAnimator reference
    
    // Mouse simulator variables
    this.mouse = new THREE.Vector2();
    this.prevMouse = new THREE.Vector2();
    this.handDepth = 8.0; // default distance from camera
    this.isSpaceActive = false;
    this.isShiftActive = false;
    // Grabbing and pinch variables per hand
    this.grabbedNodeRight = null;
    this.grabOffsetRight = new THREE.Vector3();
    this.isPinchingRight = false;

    this.grabbedNodeLeft = null;
    this.grabOffsetLeft = new THREE.Vector3();
    this.isPinchingLeft = false;

    // Backward compatibility aliases
    Object.defineProperty(this, 'grabbedNode', {
      get() { return this.grabbedNodeRight; },
      set(val) { this.grabbedNodeRight = val; }
    });
    Object.defineProperty(this, 'grabOffset', {
      get() { return this.grabOffsetRight; },
      set(val) { this.grabOffsetRight.copy(val); }
    });
    Object.defineProperty(this, 'isPinching', {
      get() { return this.isPinchingRight; },
      set(val) { this.isPinchingRight = val; }
    });

    // Hover variables per hand
    this.lastHovered3DNodeRight = null;
    this.lastHovered3DNodeLeft = null;

    // Backward compatibility alias for hover
    Object.defineProperty(this, 'lastHovered3DNode', {
      get() { return this.lastHovered3DNodeRight; },
      set(val) { this.lastHovered3DNodeRight = val; }
    });
    
    // Physics parameters
    this.handVelocity = new THREE.Vector3(); // right hand velocity
    this.prevHandPos = new THREE.Vector3(); // right hand prev position
    this.leftHandVelocity = new THREE.Vector3(); // left hand velocity
    this.prevLeftHandPos = new THREE.Vector3(); // left hand prev position
    
    this.springConstant = 0.08;
    this.dampingConstant = 0.88;

    // Left hand zoom tracking
    this.prevLeftZoomScale = undefined;

    // Webcam-mode tracking variables
    this.usingWebcam = false;
    this.latestWebcamLandmarks = [];
    this.latestWebcamHandedness = [];
    this.cursorPos = new THREE.Vector2(0, 0);
    this.active2DElement = null;
    this.isPinching2D = false;
    
    // Gesture state variables
    this.prevHandDistance = 0;
    this.prevHandAngle = undefined;

    // Hysteresis, debounce and smoothing states
    this.wasRightHandVisible = false;
    this.wasLeftHandVisible = false;
    this.unpinchBufferRight = 0;
    this.unpinchBufferLeft = 0;
    this.isPinchingRightState = false;
    this.isPinchingLeftState = false;

    // Direct mouse drag variables
    this.grabbedNodeMouse = null;
    this.grabOffsetMouse = new THREE.Vector3();
    this.mouseDragDepth = 8.0;

    // Create 2D Virtual Cursor for UI interactions
    this.createVirtualCursor();
    
    // Build 21-joint glove models
    this.createHandModels();
    
    // Bind fallback desktop event listeners
    this.setupEventListeners();
  }

  createVirtualCursor() {
    this.cursorEl = document.createElement('div');
    this.cursorEl.id = 'spatial-cursor';
    
    // Style the futuristic cursor
    Object.assign(this.cursorEl.style, {
      position: 'fixed',
      width: '20px',
      height: '20px',
      borderRadius: '50%',
      border: '2px solid #00f2fe',
      boxShadow: '0 0 10px #00f2fe',
      backgroundColor: 'rgba(0, 242, 254, 0.35)',
      pointerEvents: 'none',
      zIndex: '9999',
      transform: 'translate(-50%, -50%)',
      display: 'none',
      transition: 'border-color 0.1s ease, background-color 0.1s ease, transform 0.1s ease'
    });

    document.body.appendChild(this.cursorEl);

    // Inject hover CSS rules dynamically
    const style = document.createElement('style');
    style.id = 'spatial-hover-styles';
    style.innerHTML = `
      .spatial-hover {
        background: rgba(0, 242, 254, 0.2) !important;
        border-color: #00f2fe !important;
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.4) !important;
        transform: translateY(-2px) scale(1.02) !important;
      }
      .spatial-hover-card {
        transform: translateY(-8px) !important;
        border-color: var(--accent-cyan) !important;
        box-shadow: 0 15px 35px rgba(0, 242, 254, 0.25) !important;
      }
    `;
    document.head.appendChild(style);
  }

  createHandModels() {
    // 1. Create Right Hand (Active Controller)
    this.handGroup = this.buildHandMesh(0x00f2fe, 0xa855f7);
    this.handGroup.name = 'cyberGlove_Right';
    this.scene.add(this.handGroup);

    // 2. Create Left Hand (Mirrored Controller for 2-Hand Gestures)
    this.leftHandGroup = this.buildHandMesh(0x00f2fe, 0xff2e7e);
    this.leftHandGroup.name = 'cyberGlove_Left';
    this.scene.add(this.leftHandGroup);
  }

  buildHandMesh(jointHex, tipHex) {
    const group = new THREE.Group();
    group.visible = false;

    const jointMat = new THREE.MeshBasicMaterial({ color: jointHex, transparent: true, opacity: 0.8 });
    const tipMat = new THREE.MeshBasicMaterial({ color: tipHex, transparent: true, opacity: 0.9 });
    const sphereGeo = new THREE.SphereGeometry(0.06, 8, 8); // smaller joint spheres

    // Create 21 joint spheres
    const joints = [];
    for (let i = 0; i < 21; i++) {
      const isTip = [4, 8, 12, 16, 20].includes(i);
      const mesh = new THREE.Mesh(sphereGeo, isTip ? tipMat : jointMat);
      mesh.position.set(0, 0, 0);
      mesh.name = `joint_${i}`;
      group.add(mesh);
      joints.push(mesh);
    }
    group.userData.joints = joints;

    // MediaPipe joint connections (skeletal bones)
    const connections = [
      [0, 1], [1, 2], [2, 3], [3, 4], // Thumb
      [0, 5], [5, 6], [6, 7], [7, 8], // Index
      [5, 9], [9, 10], [10, 11], [11, 12], // Middle
      [9, 13], [13, 14], [14, 15], [15, 16], // Ring
      [13, 17], [17, 18], [18, 19], [19, 20], // Pinky
      [0, 17] // Palm wrap
    ];
    group.userData.connections = connections;

    const lineMat = new THREE.LineBasicMaterial({ color: jointHex, transparent: true, opacity: 0.4 });
    connections.forEach(conn => {
      const points = [new THREE.Vector3(), new THREE.Vector3()];
      const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
      const line = new THREE.Line(lineGeo, lineMat);
      line.name = `line_${conn[0]}_${conn[1]}`;
      group.add(line);
    });

    return group;
  }

  setupEventListeners() {
    window.addEventListener('mousemove', this.onMouseMove.bind(this));
    window.addEventListener('keydown', this.onKeyDown.bind(this));
    window.addEventListener('keyup', this.onKeyUp.bind(this));
    window.addEventListener('mousedown', this.onMouseDown.bind(this));
    window.addEventListener('mouseup', this.onMouseUp.bind(this));
    window.addEventListener('wheel', this.onWheel.bind(this), { passive: false });
  }

  onMouseMove(event) {
    this.prevMouse.copy(this.mouse);
    this.mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    this.mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

    if (this.isSpaceActive) {
      const dist = this.mouse.distanceTo(this.prevMouse);
      if (dist > 0.005) {
        this.handSimMovedOrGrabbed = true;
      }
    }

    // Handle direct mouse drag positioning
    if (this.grabbedNodeMouse) {
      const mouseWorld = new THREE.Vector3(this.mouse.x, this.mouse.y, 0.5);
      mouseWorld.unproject(this.camera);
      const dir = mouseWorld.sub(this.camera.position).normalize();
      const targetPos = this.camera.position.clone().add(dir.multiplyScalar(this.mouseDragDepth)).add(this.grabOffsetMouse);
      
      this.grabbedNodeMouse.position.lerp(targetPos, 0.85);
      this.grabbedNodeMouse.userData.currentPos.copy(this.grabbedNodeMouse.position);
    }
  }

  onKeyDown(event) {
    // Ignore keyboard hand controls if typing in input fields
    if (document.activeElement && ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
      return;
    }

    if (event.code === 'Space') {
      event.preventDefault();
      this.isSpaceActive = true;
      this.handSimMovedOrGrabbed = false;
      this.handGroup.visible = true;
      
      if (event.shiftKey) {
        this.isShiftActive = true;
        this.leftHandGroup.visible = true;
      }
      this.animEngine.controls.enabled = false;
    }
    if (event.code === 'ShiftLeft' || event.code === 'ShiftRight') {
      if (this.isSpaceActive) {
        this.isShiftActive = true;
        this.leftHandGroup.visible = true;
        this.handSimMovedOrGrabbed = true;
      }
    }
  }

  onKeyUp(event) {
    if (event.code === 'Space') {
      this.isSpaceActive = false;
      this.isShiftActive = false;
      this.handGroup.visible = false;
      this.leftHandGroup.visible = false;
      this.isPinchingRight = false;
      this.releaseNode();
      this.animEngine.controls.enabled = true;
      this.prevHandDistance = 0;
      
      if (!this.handSimMovedOrGrabbed) {
        if (this.hud) {
          this.hud.togglePlay();
        }
      }
    }
    if (event.code === 'ShiftLeft' || event.code === 'ShiftRight') {
      this.isShiftActive = false;
      this.leftHandGroup.visible = false;
      this.prevHandDistance = 0;
    }
  }

  onMouseDown(event) {
    if (this.isSpaceActive && event.button === 0 && !this.isShiftActive) {
      this.isPinchingRight = true;
      this.handSimMovedOrGrabbed = true;
      this.attemptGrab();
      return;
    }

    // Direct mouse drag-and-drop on blocks (without Space key)
    if (event.button === 0) {
      const raycaster = new THREE.Raycaster();
      raycaster.setFromCamera(this.mouse, this.camera);

      const meshesToCheck = [];
      this.animEngine.nodesMap.forEach(group => {
        const core = group.getObjectByName('core');
        if (core) meshesToCheck.push(core);
      });

      const intersects = raycaster.intersectObjects(meshesToCheck);

      if (intersects.length > 0) {
        // We clicked on a block!
        event.preventDefault();
        
        const coreMesh = intersects[0].object;
        const node = coreMesh.parent;
        
        // Grab it
        this.grabbedNodeMouse = node;
        node.userData.isGrabbed = true;
        
        const nodePos = new THREE.Vector3();
        node.getWorldPosition(nodePos);
        
        // Project mouse depth
        const depth = nodePos.distanceTo(this.camera.position);
        this.mouseDragDepth = depth;
        
        // Compute offset
        const mouseWorld = new THREE.Vector3(this.mouse.x, this.mouse.y, 0.5);
        mouseWorld.unproject(this.camera);
        const dir = mouseWorld.sub(this.camera.position).normalize();
        const clickPoint = this.camera.position.clone().add(dir.multiplyScalar(depth));
        
        this.grabOffsetMouse = new THREE.Vector3().subVectors(nodePos, clickPoint);
        node.userData.targetColor.setHex(0xf59e0b); // gold grab outline
        
        this.animEngine.controls.enabled = false; // Disable camera rotation while dragging
      }
    }
  }

  onMouseUp(event) {
    if (event.button === 0) {
      if (this.isSpaceActive) {
        this.isPinchingRight = false;
        this.releaseNode();
      }

      // Handle direct mouse release
      if (this.grabbedNodeMouse) {
        const node = this.grabbedNodeMouse;
        const ud = node.userData;
        ud.isGrabbed = false;
        
        // Velocity from mouse movement
        const mouseWorld = new THREE.Vector3(this.mouse.x, this.mouse.y, 0.5);
        mouseWorld.unproject(this.camera);
        const prevMouseWorld = new THREE.Vector3(this.prevMouse.x, this.prevMouse.y, 0.5);
        prevMouseWorld.unproject(this.camera);
        
        const velocity = new THREE.Vector3().subVectors(mouseWorld, prevMouseWorld).multiplyScalar(10);
        ud.velocity = velocity;

        if (ud.baseColor) {
          ud.targetColor.copy(ud.baseColor);
        } else {
          ud.targetColor.setHex(0x00f2fe);
        }

        this.grabbedNodeMouse = null;

        if (this.hud) {
          this.hud.rearrangeNodes();
        }

        this.animEngine.controls.enabled = true; // Re-enable camera rotation
      }
    }
  }

  onWheel(event) {
    if (this.isSpaceActive) {
      event.preventDefault();
      this.handDepth -= event.deltaY * 0.005;
      this.handDepth = Math.max(3, Math.min(this.handDepth, 25));
      this.handSimMovedOrGrabbed = true;
    }
  }

  updateKnuckleLines(hand) {
    const joints = hand.userData.joints;
    const connections = hand.userData.connections;
    
    connections.forEach(conn => {
      const line = hand.getObjectByName(`line_${conn[0]}_${conn[1]}`);
      if (line) {
        const p1 = joints[conn[0]].position;
        const p2 = joints[conn[1]].position;
        const points = [p1, p2];
        line.geometry.setFromPoints(points);
        line.geometry.attributes.position.needsUpdate = true;
      }
    });
  }

  positionRelaxedHand(hand, isPinching = false) {
    const joints = hand.userData.joints;
    
    // Wrist at local origin
    joints[0].position.set(0, 0, 0);
    
    // Thumb: joints 1-4
    joints[1].position.set(-0.15, 0.15, 0.05);
    joints[2].position.set(-0.25, 0.3, 0.08);
    joints[3].position.set(-0.32, 0.42, 0.1);
    joints[4].position.set(-0.38, 0.5, 0.12);
    
    // Index: joints 5-8
    joints[5].position.set(-0.1, 0.25, 0.0);
    joints[6].position.set(-0.12, 0.45, -0.02);
    joints[7].position.set(-0.14, 0.6, -0.03);
    joints[8].position.set(-0.15, 0.7, -0.04);
    
    // Middle: joints 9-12
    joints[9].position.set(0.0, 0.26, 0.0);
    joints[10].position.set(0.02, 0.48, -0.02);
    joints[11].position.set(0.03, 0.64, -0.03);
    joints[12].position.set(0.04, 0.75, -0.04);
    
    // Ring: joints 13-16
    joints[13].position.set(0.1, 0.24, 0.0);
    joints[14].position.set(0.14, 0.45, -0.02);
    joints[15].position.set(0.17, 0.6, -0.03);
    joints[16].position.set(0.19, 0.7, -0.04);
    
    // Pinky: joints 17-20
    joints[17].position.set(0.2, 0.2, 0.05);
    joints[18].position.set(0.26, 0.38, 0.02);
    joints[19].position.set(0.31, 0.5, 0.0);
    joints[20].position.set(0.35, 0.6, -0.02);
    
    if (isPinching) {
      // Squeeze Index & Thumb tips together
      const pinchPoint = new THREE.Vector3().addVectors(joints[4].position, joints[8].position).multiplyScalar(0.5);
      joints[4].position.lerp(pinchPoint, 0.85);
      joints[8].position.lerp(pinchPoint, 0.85);
      
      joints[3].position.lerp(pinchPoint, 0.4);
      joints[7].position.lerp(pinchPoint, 0.4);
    }
  }

  // Receives raw landmarks from WebcamHandsManager
  updateFromWebcam(multiHandLandmarks, multiHandedness) {
    this.latestWebcamLandmarks = multiHandLandmarks || [];
    this.latestWebcamHandedness = multiHandedness || [];
    this.usingWebcam = this.latestWebcamLandmarks.length > 0;
  }

  // Projects normalized MediaPipe landmarks into Three.js camera space
  getJointWorldPos(lm) {
    const ndcX = (1 - lm.x) * 2 - 1; // Mirrored camera coordinates
    const ndcY = -(lm.y * 2 - 1);
    
    // Feed depth using relative landmark z-displacement
    const depth = this.handDepth + (lm.z || 0) * 8.0;
    
    const tempV = new THREE.Vector3(ndcX, ndcY, 0.5);
    tempV.unproject(this.camera);
    const dir = tempV.sub(this.camera.position).normalize();
    return this.camera.position.clone().add(dir.multiplyScalar(depth));
  }

  attemptGrabHand(handGroup, isRight) {
    const lastHoveredProp = isRight ? 'lastHovered3DNodeRight' : 'lastHovered3DNodeLeft';
    const grabbedNodeProp = isRight ? 'grabbedNodeRight' : 'grabbedNodeLeft';
    const grabOffsetProp = isRight ? 'grabOffsetRight' : 'grabOffsetLeft';

    const indexTipWorldPos = new THREE.Vector3();
    handGroup.userData.joints[8].getWorldPosition(indexTipWorldPos);

    // Proximity grab (extremely easy to target using hand gestures)
    if (this[lastHoveredProp]) {
      const node = this[lastHoveredProp];
      // Check if it's already grabbed by the other hand
      const otherGrabbedNodeProp = isRight ? 'grabbedNodeLeft' : 'grabbedNodeRight';
      if (this[otherGrabbedNodeProp] === node) {
        return;
      }

      this[grabbedNodeProp] = node;
      node.userData.isGrabbed = true;
      
      const nodePos = new THREE.Vector3();
      node.getWorldPosition(nodePos);
      this[grabOffsetProp].copy(nodePos).sub(indexTipWorldPos);
      node.userData.targetColor.setHex(0xf59e0b); // yellow warning grab
      return;
    }

    // Fallback to raycast grab
    const raycaster = new THREE.Raycaster();
    raycaster.set(this.camera.position, indexTipWorldPos.clone().sub(this.camera.position).normalize());
    
    const meshesToCheck = [];
    this.animEngine.nodesMap.forEach(group => {
      const core = group.getObjectByName('core');
      if (core) meshesToCheck.push(core);
    });

    const intersects = raycaster.intersectObjects(meshesToCheck);

    if (intersects.length > 0) {
      const coreMesh = intersects[0].object;
      const node = coreMesh.parent;

      // Check if it's already grabbed by the other hand
      const otherGrabbedNodeProp = isRight ? 'grabbedNodeLeft' : 'grabbedNodeRight';
      if (this[otherGrabbedNodeProp] === node) {
        return;
      }

      this[grabbedNodeProp] = node;
      node.userData.isGrabbed = true;
      
      const nodePos = new THREE.Vector3();
      node.getWorldPosition(nodePos);
      this[grabOffsetProp].copy(nodePos).sub(indexTipWorldPos);
      node.userData.targetColor.setHex(0xf59e0b); // yellow warning grab
    }
  }

  attemptGrab() {
    this.attemptGrabHand(this.handGroup, true);
  }

  releaseNodeHand(isRight) {
    const grabbedNodeProp = isRight ? 'grabbedNodeRight' : 'grabbedNodeLeft';
    const velocity = isRight ? this.handVelocity : this.leftHandVelocity;
    const node = this[grabbedNodeProp];
    
    if (node) {
      const ud = node.userData;
      ud.isGrabbed = false;
      
      // Let it glide with hand momentum
      ud.velocity = velocity.clone().multiplyScalar(0.4);
      
      // Restore default state color if tracked
      if (ud.baseColor) {
        ud.targetColor.copy(ud.baseColor);
      } else {
        ud.targetColor.setHex(0x00f2fe);
      }
      this[grabbedNodeProp] = null;

      // Trigger manual reordering evaluation
      if (this.hud) {
        this.hud.rearrangeNodes();
      }
    }
  }

  releaseNode() {
    this.releaseNodeHand(true);
  }

  // Measures distance between thumb and index in relative MediaPipe coordinate space
  getPinchDistance(landmarks) {
    const thumb = landmarks[4];
    const index = landmarks[8];
    const dx = thumb.x - index.x;
    const dy = thumb.y - index.y;
    const dz = thumb.z - index.z;
    return Math.sqrt(dx * dx + dy * dy + dz * dz);
  }

  // Measures the overall hand size in image coordinates (wrist to middle finger base)
  getHandScale(landmarks) {
    if (!landmarks || landmarks.length <= 9) return 1.0;
    const wrist = landmarks[0];
    const middleBase = landmarks[9];
    const dx = wrist.x - middleBase.x;
    const dy = wrist.y - middleBase.y;
    const dz = wrist.z - middleBase.z;
    return Math.sqrt(dx * dx + dy * dy + dz * dz);
  }

  // Simulates cursor mouse hover events on DOM elements
  process2DHover(screenX, screenY) {
    const element = document.elementFromPoint(screenX, screenY);
    if (!element) return;

    // Identify interactive elements
    const interactiveCard = element.closest('.topic-card');
    const interactiveBtn = element.closest('.action-btn, .control-btn, .lesson-item, input, select, button, #keyboard-close-btn');

    // Remove old hover classes
    if (this.lastHoveredCard && this.lastHoveredCard !== interactiveCard) {
      this.lastHoveredCard.classList.remove('spatial-hover-card');
    }
    if (this.lastHoveredBtn && this.lastHoveredBtn !== interactiveBtn) {
      this.lastHoveredBtn.classList.remove('spatial-hover');
    }

    // Apply new hover classes
    if (interactiveCard) {
      interactiveCard.classList.add('spatial-hover-card');
      this.lastHoveredCard = interactiveCard;
    }
    if (interactiveBtn) {
      interactiveBtn.classList.add('spatial-hover');
      this.lastHoveredBtn = interactiveBtn;
    }
  }

  process2DClick(screenX, screenY) {
    const element = document.elementFromPoint(screenX, screenY);
    if (element) {
      // Simulate click event
      element.click();
      
      // Focus if it's an input box to load virtual keyboard
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes(element.tagName)) {
        element.focus();
      }
    }
  }

  processSliderDrag(screenX) {
    if (this.active2DElement && this.active2DElement.tagName === 'INPUT' && this.active2DElement.type === 'range') {
      const slider = this.active2DElement;
      const rect = slider.getBoundingClientRect();
      const pct = Math.max(0, Math.min(1, (screenX - rect.left) / rect.width));
      
      const min = parseFloat(slider.min || 0);
      const max = parseFloat(slider.max || 100);
      const step = parseFloat(slider.step || 1);
      
      const val = min + pct * (max - min);
      const roundedVal = Math.round(val / step) * step;
      
      slider.value = roundedVal;
      slider.dispatchEvent(new Event('input', { bubbles: true }));
    }
  }

  checkButtonPokes(time, deltaTime) {
    if (!this.animEngine || !this.animEngine.pokeButtons) return;

    const rightIndexTip = new THREE.Vector3();
    const rightTipMesh = this.handGroup.userData.joints[8];
    if (this.handGroup.visible && rightTipMesh) {
      rightTipMesh.getWorldPosition(rightIndexTip);
      this.testPokeCollision(rightIndexTip);
    }

    const leftIndexTip = new THREE.Vector3();
    const leftTipMesh = this.leftHandGroup.userData.joints[8];
    if (this.leftHandGroup.visible && leftTipMesh) {
      leftTipMesh.getWorldPosition(leftIndexTip);
      this.testPokeCollision(leftIndexTip);
    }
  }

  testPokeCollision(indexTipWorld) {
    this.animEngine.pokeButtons.forEach(btn => {
      const box = new THREE.Box3().setFromObject(btn);
      box.expandByScalar(0.35); // Expanded margin for highly responsive and forgiving pokes

      const isInside = box.containsPoint(indexTipWorld);

      if (isInside) {
        if (!btn.userData.isPressed && btn.userData.cooldown <= 0) {
          btn.userData.isPressed = true;
          btn.userData.cooldown = 0.8; // cooldown timer
          this.triggerButtonAction(btn.userData.id);
        }
      } else {
        // Only release press when fingertip leaves box
        btn.userData.isPressed = false;
      }
    });
  }

  triggerButtonAction(id) {
    if (id === 'next') {
      if (this.hud) {
        this.hud.stepForward();
      } else {
        const btn = document.getElementById('btn-next');
        if (btn) btn.click();
      }
    }
  }

  // 3D Nodes proximity hover labels highlight
  process3DHover(indexTipWorld, isRight = true) {
    let hoveredNode = null;
    let minDistance = 0.8; // hover bounds

    this.animEngine.nodesMap.forEach(group => {
      const nodePos = new THREE.Vector3();
      group.getWorldPosition(nodePos);
      const dist = indexTipWorld.distanceTo(nodePos);
      if (dist < minDistance) {
        hoveredNode = group;
        minDistance = dist;
      }
    });

    const lastHoveredProp = isRight ? 'lastHovered3DNodeRight' : 'lastHovered3DNodeLeft';
    const lastHoveredNode = this[lastHoveredProp];

    if (lastHoveredNode && lastHoveredNode !== hoveredNode) {
      // Restore previous node styling if not hovered by the OTHER hand either
      const otherHandHoveredProp = isRight ? 'lastHovered3DNodeLeft' : 'lastHovered3DNodeRight';
      const otherHoveredNode = this[otherHandHoveredProp];

      if (lastHoveredNode !== otherHoveredNode) {
        const ud = lastHoveredNode.userData;
        ud.targetScale.set(1, 1, 1);
        if (ud.baseColor) {
          ud.targetColor.copy(ud.baseColor);
        }
        const label = lastHoveredNode.getObjectByName('label');
        if (label && label.element) {
          label.element.classList.remove('highlighted');
        }
      }
      this[lastHoveredProp] = null;
    }

    if (hoveredNode) {
      const ud = hoveredNode.userData;
      ud.targetScale.set(1.15, 1.15, 1.15); // pop scale on hover
      ud.targetColor.setHex(0xf59e0b); // gold outline glow

      const label = hoveredNode.getObjectByName('label');
      if (label && label.element) {
        label.element.classList.add('highlighted');
      }
      this[lastHoveredProp] = hoveredNode;
    }
  }

  update(time, deltaTime) {
    if (this.usingWebcam) {
      this.handGroup.visible = false;
      this.leftHandGroup.visible = false;

      let rightHandIdx = -1;
      let leftHandIdx = -1;

      // Identify handedness indexes
      this.latestWebcamHandedness.forEach((handed, index) => {
        if (handed.label === 'Right') rightHandIdx = index;
        else if (handed.label === 'Left') leftHandIdx = index;
      });

      let isAnyPinching = false;

      // Update right hand model meshes (Space key activates desktop simulated hand)
      if (this.isSpaceActive) {
        this.handGroup.visible = true;
        const tempV = new THREE.Vector3(this.mouse.x, this.mouse.y, 0.5);
        tempV.unproject(this.camera);
        const dir = tempV.sub(this.camera.position).normalize();
        const targetHandPos = this.camera.position.clone().add(dir.multiplyScalar(this.handDepth));
        
        this.handGroup.position.lerp(targetHandPos, 0.35);
        this.positionRelaxedHand(this.handGroup, this.isPinchingRight);
        this.updateKnuckleLines(this.handGroup);

        const indexTipWorld = new THREE.Vector3();
        this.handGroup.userData.joints[8].getWorldPosition(indexTipWorld);

        this.process3DHover(indexTipWorld, true);

        if (this.isPinchingRight) {
          isAnyPinching = true;
          if (this.grabbedNodeRight) {
            const grabTargetPos = indexTipWorld.clone().add(this.grabOffsetRight);
            this.grabbedNodeRight.position.lerp(grabTargetPos, 0.85);
            this.grabbedNodeRight.userData.currentPos.copy(this.grabbedNodeRight.position);
          }
        }

        // Calculate hand velocity vector for momentum
        this.handVelocity.subVectors(this.handGroup.position, this.prevHandPos).divideScalar(Math.max(deltaTime, 0.001));
        this.prevHandPos.copy(this.handGroup.position);
      } else if (rightHandIdx !== -1) {
        this.handGroup.visible = true;
        const landmarks = this.latestWebcamLandmarks[rightHandIdx];
        const joints = this.handGroup.userData.joints;

        // Position 21 joint meshes
        landmarks.forEach((lm, i) => {
          const worldPos = this.getJointWorldPos(lm);
          if (!this.wasRightHandVisible) {
            joints[i].position.copy(worldPos);
          } else {
            joints[i].position.lerp(worldPos, 0.65); // Smooth high-frequency jitter
          }
        });
        this.wasRightHandVisible = true;
        
        this.updateKnuckleLines(this.handGroup);

        const indexTipWorld = new THREE.Vector3();
        joints[8].getWorldPosition(indexTipWorld);

        // 3D Nodes proximity hover checks
        this.process3DHover(indexTipWorld, true);

        // Update 2D cursor coordinates (projected from Right Index tip)
        const targetX = (1 - landmarks[8].x) * window.innerWidth;
        const targetY = landmarks[8].y * window.innerHeight;

        // Apply low-pass cursor damping
        if (this.cursorPos.x === 0 && this.cursorPos.y === 0) {
          this.cursorPos.set(targetX, targetY);
        } else {
          this.cursorPos.x += (targetX - this.cursorPos.x) * 0.28;
          this.cursorPos.y += (targetY - this.cursorPos.y) * 0.28;
        }

        this.cursorEl.style.left = `${this.cursorPos.x}px`;
        this.cursorEl.style.top = `${this.cursorPos.y}px`;
        this.cursorEl.style.display = 'block';

        this.process2DHover(this.cursorPos.x, this.cursorPos.y);

        // Check right hand pinch (using scale-invariant ratio & hysteresis)
        const scale = this.getHandScale(landmarks);
        const rightPinchDist = this.getPinchDistance(landmarks);
        const pinchRatio = scale > 0 ? rightPinchDist / scale : 999;
        
        let isCurrentlyPinching = false;
        if (this.isPinchingRightState) {
          if (pinchRatio < 0.60) {
            isCurrentlyPinching = true;
          }
        } else {
          if (pinchRatio < 0.38) {
            isCurrentlyPinching = true;
          }
        }

        // Apply unpinch debounce buffer
        if (isCurrentlyPinching) {
          this.unpinchBufferRight = 0;
          this.isPinchingRightState = true;
        } else {
          this.unpinchBufferRight++;
          if (this.unpinchBufferRight < 10) { // 10 frames grace period
            isCurrentlyPinching = true;
          } else {
            this.isPinchingRightState = false;
          }
        }

        if (isCurrentlyPinching) {
          isAnyPinching = true;

          // Visual finger pinch deformation
          const pinchPoint = new THREE.Vector3().addVectors(joints[4].position, joints[8].position).multiplyScalar(0.5);
          joints[4].position.lerp(pinchPoint, 0.8);
          joints[8].position.lerp(pinchPoint, 0.8);
          this.updateKnuckleLines(this.handGroup);

          // Change cursor color to show click
          this.cursorEl.style.borderColor = '#a855f7';
          this.cursorEl.style.backgroundColor = 'rgba(168, 85, 247, 0.6)';
          this.cursorEl.style.transform = 'translate(-50%, -50%) scale(0.8)';

          if (!this.isPinchingRight) {
            this.isPinchingRight = true;

            // Determine if clicking HTML or grabbing a 3D Node
            const clickedElement = document.elementFromPoint(this.cursorPos.x, this.cursorPos.y);
            
            // Check if pointer is hovering over an overlay panel
            const overlayPanel = clickedElement ? clickedElement.closest('.glass-panel, #dashboard-overlay, #virtual-keyboard') : null;

            if (overlayPanel) {
              this.isPinching2D = true;
              this.active2DElement = clickedElement;
              this.process2DClick(this.cursorPos.x, this.cursorPos.y);
            } else {
              this.attemptGrabHand(this.handGroup, true);
            }
          }

          // Handle active actions
          if (this.isPinching2D) {
            // Drag range sliders
            this.processSliderDrag(this.cursorPos.x);
          } else if (this.grabbedNodeRight) {
            // Drag 3D node (high speed catching up)
            const grabTargetPos = indexTipWorld.clone().add(this.grabOffsetRight);
            this.grabbedNodeRight.position.lerp(grabTargetPos, 0.85);
            this.grabbedNodeRight.userData.currentPos.copy(this.grabbedNodeRight.position);
          }
        } else {
          // Unpinch
          this.cursorEl.style.borderColor = '#00f2fe';
          this.cursorEl.style.backgroundColor = 'rgba(0, 242, 254, 0.35)';
          this.cursorEl.style.transform = 'translate(-50%, -50%) scale(1.0)';

          if (this.isPinchingRight) {
            this.isPinchingRight = false;
            this.isPinching2D = false;
            this.active2DElement = null;
            this.releaseNodeHand(true);
          }
        }

        // Calculate hand velocity vector for momentum
        this.handVelocity.subVectors(this.handGroup.position, this.prevHandPos).divideScalar(Math.max(deltaTime, 0.001));
        this.prevHandPos.copy(this.handGroup.position);
      } else {
        this.cursorEl.style.display = 'none';
        this.wasRightHandVisible = false;
        if (this.grabbedNodeRight) {
          this.releaseNodeHand(true);
        }
      }

      // Update left hand model meshes
      if (this.isSpaceActive && this.isShiftActive) {
        this.leftHandGroup.visible = true;
        const mirrorX = -this.mouse.x;
        const tempLeftV = new THREE.Vector3(mirrorX, this.mouse.y, 0.5);
        tempLeftV.unproject(this.camera);
        const leftDir = tempLeftV.sub(this.camera.position).normalize();
        const targetLeftHandPos = this.camera.position.clone().add(leftDir.multiplyScalar(this.handDepth));
        
        this.leftHandGroup.position.lerp(targetLeftHandPos, 0.35);
        this.positionRelaxedHand(this.leftHandGroup, false);
        this.updateKnuckleLines(this.leftHandGroup);

        const leftIndexTipWorld = new THREE.Vector3();
        this.leftHandGroup.userData.joints[8].getWorldPosition(leftIndexTipWorld);

        this.process3DHover(leftIndexTipWorld, false);

        // Simulated scaling
        const dist = this.handGroup.position.distanceTo(this.leftHandGroup.position);
        if (this.prevHandDistance > 0) {
          const ratio = dist / this.prevHandDistance;
          const currentScale = this.animEngine.structureGroup.scale.x;
          const targetScale = Math.max(0.3, Math.min(currentScale * ratio, 2.8));
          this.animEngine.structureGroup.scale.set(targetScale, targetScale, targetScale);
        }
        this.prevHandDistance = dist;

        // Simulated rotation
        const mouseDeltaX = this.mouse.x - this.prevMouse.x;
        this.animEngine.structureGroup.rotation.y += mouseDeltaX * 1.5;

        // Calculate left hand velocity vector for momentum
        this.leftHandVelocity.subVectors(this.leftHandGroup.position, this.prevLeftHandPos).divideScalar(Math.max(deltaTime, 0.001));
        this.prevLeftHandPos.copy(this.leftHandGroup.position);
      } else if (leftHandIdx !== -1) {
        this.leftHandGroup.visible = true;
        const landmarks = this.latestWebcamLandmarks[leftHandIdx];
        const joints = this.leftHandGroup.userData.joints;

        landmarks.forEach((lm, i) => {
          const worldPos = this.getJointWorldPos(lm);
          if (!this.wasLeftHandVisible) {
            joints[i].position.copy(worldPos);
          } else {
            joints[i].position.lerp(worldPos, 0.65);
          }
        });
        this.wasLeftHandVisible = true;

        this.updateKnuckleLines(this.leftHandGroup);

        // Check left hand pinch (using scale-invariant ratio & hysteresis)
        const scale = this.getHandScale(landmarks);
        const leftPinchDist = this.getPinchDistance(landmarks);
        const pinchRatio = scale > 0 ? leftPinchDist / scale : 999;

        let isCurrentlyPinchingLeft = false;
        if (this.isPinchingLeftState) {
          if (pinchRatio < 0.60) {
            isCurrentlyPinchingLeft = true;
          }
        } else {
          if (pinchRatio < 0.38) {
            isCurrentlyPinchingLeft = true;
          }
        }

        // Apply unpinch debounce buffer
        if (isCurrentlyPinchingLeft) {
          this.unpinchBufferLeft = 0;
          this.isPinchingLeftState = true;
        } else {
          this.unpinchBufferLeft++;
          if (this.unpinchBufferLeft < 10) {
            isCurrentlyPinchingLeft = true;
          } else {
            this.isPinchingLeftState = false;
          }
        }

        const leftIndexTipWorld = new THREE.Vector3();
        joints[8].getWorldPosition(leftIndexTipWorld);

        // 3D Nodes proximity hover checks
        this.process3DHover(leftIndexTipWorld, false);

        if (isCurrentlyPinchingLeft) {
          isAnyPinching = true;

          const pinchPoint = new THREE.Vector3().addVectors(joints[4].position, joints[8].position).multiplyScalar(0.5);
          joints[4].position.lerp(pinchPoint, 0.8);
          joints[8].position.lerp(pinchPoint, 0.8);
          this.updateKnuckleLines(this.leftHandGroup);

          if (!this.isPinchingLeft) {
            this.isPinchingLeft = true;
            this.attemptGrabHand(this.leftHandGroup, false);
          }

          if (this.grabbedNodeLeft) {
            // Drag 3D node (high speed catching up)
            const grabTargetPos = leftIndexTipWorld.clone().add(this.grabOffsetLeft);
            this.grabbedNodeLeft.position.lerp(grabTargetPos, 0.85);
            this.grabbedNodeLeft.userData.currentPos.copy(this.grabbedNodeLeft.position);
          } else {
            // Pinch Zoom (Left Hand) when NOT grabbing a node
            // Controlled by hand scale (moving hand closer/further from camera)
            if (this.prevLeftZoomScale !== undefined) {
              const scaleRatio = scale / this.prevLeftZoomScale;
              if (scaleRatio > 1.03) {
                // Hand moving closer: Zoom in
                this.animEngine.controls.dollyIn(0.95);
                this.prevLeftZoomScale = scale;
              } else if (scaleRatio < 0.97) {
                // Hand moving further: Zoom out
                this.animEngine.controls.dollyOut(1.05);
                this.prevLeftZoomScale = scale;
              }
            } else {
              this.prevLeftZoomScale = scale;
            }
          }
        } else {
          if (this.isPinchingLeft) {
            this.isPinchingLeft = false;
            this.releaseNodeHand(false);
          }
          this.prevLeftZoomScale = undefined;
        }

        // Calculate left hand velocity vector for momentum
        this.leftHandVelocity.subVectors(this.leftHandGroup.position, this.prevLeftHandPos).divideScalar(Math.max(deltaTime, 0.001));
        this.prevLeftHandPos.copy(this.leftHandGroup.position);
      } else {
        this.prevLeftZoomScale = undefined;
        this.wasLeftHandVisible = false;
        if (this.grabbedNodeLeft) {
          this.releaseNodeHand(false);
        }
      }

      // Disable orbit controls when pinching/grabbing, simulating hands, or dragging via mouse to prevent screen movement
      const isDragging = isAnyPinching || !!this.grabbedNodeMouse || this.isSpaceActive;
      this.animEngine.controls.enabled = !isDragging;

      // Check dual hand rotate/scale gestures (only if not grabbing nodes)
      if (rightHandIdx !== -1 && leftHandIdx !== -1) {
        const rightLM = this.latestWebcamLandmarks[rightHandIdx];
        const leftLM = this.latestWebcamLandmarks[leftHandIdx];
        
        const rightPinchDist = this.getPinchDistance(rightLM);
        const leftPinchDist = this.getPinchDistance(leftLM);

        // Both hands must pinch to trigger transform adjustments (and not grabbing nodes)
        if (rightPinchDist < 0.12 && leftPinchDist < 0.12 && !this.grabbedNodeRight && !this.grabbedNodeLeft) {
          const rightIndexPos = new THREE.Vector3();
          const leftIndexPos = new THREE.Vector3();
          
          this.handGroup.userData.joints[8].getWorldPosition(rightIndexPos);
          this.leftHandGroup.userData.joints[8].getWorldPosition(leftIndexPos);

          // 1. Dual Hand scaling structure
          const currentDist = rightIndexPos.distanceTo(leftIndexPos);
          if (this.prevHandDistance > 0) {
            const ratio = currentDist / this.prevHandDistance;
            const currentScale = this.animEngine.structureGroup.scale.x;
            const targetScale = Math.max(0.3, Math.min(currentScale * ratio, 2.8));
            this.animEngine.structureGroup.scale.set(targetScale, targetScale, targetScale);
          }
          this.prevHandDistance = currentDist;

          // 2. Dual Hand rotating structure (Tilt yaw angle)
          const dx = rightIndexPos.x - leftIndexPos.x;
          const dz = rightIndexPos.z - leftIndexPos.z;
          const currentAngle = Math.atan2(dz, dx);

          if (this.prevHandAngle !== undefined) {
            const angleDelta = currentAngle - this.prevHandAngle;
            // Mirror rotation factor
            this.animEngine.structureGroup.rotation.y -= angleDelta * 1.5;
          }
          this.prevHandAngle = currentAngle;
        } else {
          this.prevHandDistance = 0;
          this.prevHandAngle = undefined;
        }
      } else {
        this.prevHandDistance = 0;
        this.prevHandAngle = undefined;
      }

      // Proximity pokes checks
      this.checkButtonPokes(time, deltaTime);

    } else {
      // FALLBACK: Desktop mouse and keyboard simulator
      this.cursorEl.style.display = 'none';

      if (this.isSpaceActive) {
        const tempV = new THREE.Vector3(this.mouse.x, this.mouse.y, 0.5);
        tempV.unproject(this.camera);
        const dir = tempV.sub(this.camera.position).normalize();
        const targetHandPos = this.camera.position.clone().add(dir.multiplyScalar(this.handDepth));
        
        this.handGroup.position.lerp(targetHandPos, 0.35);
        
        // Procedural hand mesh deformation
        this.positionRelaxedHand(this.handGroup, this.isPinching);
        this.updateKnuckleLines(this.handGroup);

        this.handVelocity.subVectors(this.handGroup.position, this.prevHandPos).divideScalar(Math.max(deltaTime, 0.001));
        this.prevHandPos.copy(this.handGroup.position);

        if (this.isShiftActive) {
          const mirrorX = -this.mouse.x;
          const tempLeftV = new THREE.Vector3(mirrorX, this.mouse.y, 0.5);
          tempLeftV.unproject(this.camera);
          const leftDir = tempLeftV.sub(this.camera.position).normalize();
          const targetLeftHandPos = this.camera.position.clone().add(leftDir.multiplyScalar(this.handDepth));
          
          this.leftHandGroup.position.lerp(targetLeftHandPos, 0.35);
          this.positionRelaxedHand(this.leftHandGroup, false);
          this.updateKnuckleLines(this.leftHandGroup);

          // Simulated scaling
          const dist = this.handGroup.position.distanceTo(this.leftHandGroup.position);
          if (this.prevHandDistance > 0) {
            const ratio = dist / this.prevHandDistance;
            const currentScale = this.animEngine.structureGroup.scale.x;
            const targetScale = Math.max(0.3, Math.min(currentScale * ratio, 2.8));
            this.animEngine.structureGroup.scale.set(targetScale, targetScale, targetScale);
          }
          this.prevHandDistance = dist;

          // Simulated rotation
          const mouseDeltaX = this.mouse.x - this.prevMouse.x;
          this.animEngine.structureGroup.rotation.y += mouseDeltaX * 1.5;
        } else {
          this.prevHandDistance = 0;
          
          if (this.grabbedNode) {
            const indexTipWorldPos = new THREE.Vector3();
            this.handGroup.userData.joints[8].getWorldPosition(indexTipWorldPos);
            const targetNodePos = indexTipWorldPos.clone().add(this.grabOffset);
            this.grabbedNode.position.lerp(targetNodePos, 0.45);
            this.grabbedNode.userData.currentPos.copy(this.grabbedNode.position);
          }
        }
      }
    }

    // Apply inertia and bounce-backs physics for all nodes
    this.animEngine.nodesMap.forEach(group => {
      const ud = group.userData;
      if (ud.isGrabbed) return;

      if (!ud.velocity) ud.velocity = new THREE.Vector3();

      if (ud.velocity.lengthSq() > 0.0001) {
        ud.currentPos.addScaledVector(ud.velocity, deltaTime);
        ud.velocity.multiplyScalar(this.dampingConstant);
      }

      // Spring returns
      const displacement = new THREE.Vector3().subVectors(ud.targetPos, ud.currentPos);
      const springAcceleration = displacement.multiplyScalar(this.springConstant);
      ud.velocity.addScaledVector(springAcceleration, deltaTime * 60);
    });
    
    this.prevMouse.copy(this.mouse);
  }
}
