import * as THREE from 'three';
import { CSS2DObject } from 'three/examples/jsm/renderers/CSS2DRenderer.js';

export class SceneAnimator {
  constructor(scene) {
    this.scene = scene;
    
    // Root container group for the entire active data structure
    this.structureGroup = new THREE.Group();
    this.scene.add(this.structureGroup);

    this.nodesMap = new Map(); // id -> THREE.Group
    this.linksList = [];       // array of link meshes
    this.spawningNodes = new Map(); // id -> THREE.Group
    
    // Geometry templates
    this.sphereGeo = new THREE.SphereGeometry(0.5, 32, 32);
    this.cylinderGeo = new THREE.CylinderGeometry(0.4, 0.4, 1.2, 32);
    
    // Default coordinates for graph nodes
    this.graphCoordinates = {
      'A': new THREE.Vector3(0, 2.5, -2),
      'B': new THREE.Vector3(-3.5, 1.5, -0.5),
      'C': new THREE.Vector3(3.5, 1.5, -0.5),
      'D': new THREE.Vector3(-3.5, -1.0, 1.5),
      'E': new THREE.Vector3(0, -0.5, 0.5),
      'F': new THREE.Vector3(3.5, -1.0, 1.5)
    };

    // Holographic Step Badge (floats above active/comparing nodes)
    this.holoStepDiv = document.createElement('div');
    this.holoStepDiv.className = 'holo-step-badge hidden';
    this.holoStepBadge = new CSS2DObject(this.holoStepDiv);
    this.holoStepBadge.name = 'holoStepBadge';

    // 3D UI Buttons Group
    this.uiButtonsGroup = new THREE.Group();
    this.uiButtonsGroup.name = 'uiButtonsGroup';
    this.uiButtonsGroup.visible = false; // Hidden on dashboard by default
    this.scene.add(this.uiButtonsGroup);
    
    this.pokeButtons = [];
    this.create3DButtons();
  }

  create3DButtons() {
    this.uiButtonsGroup.clear();
    this.pokeButtons = [];

    // Single large Down Arrow button centered horizontally (x = 0)
    const btn = { id: 'next', text: '▼ NEXT STEP', x: 0, color: 0x00f2fe };

    // Extra large geometry for extremely easy and comfortable fingertip pokes
    const geo = new THREE.BoxGeometry(1.6, 0.5, 0.35);
    const mat = new THREE.MeshPhysicalMaterial({
      color: btn.color,
      transparent: true,
      opacity: 0.75,
      roughness: 0.15,
      metalness: 0.1,
      transmission: 0.65,
      thickness: 0.35,
      emissive: btn.color,
      emissiveIntensity: 0.35
    });

    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(btn.x, -2.2, 0.5); // Float below node structures
    mesh.name = `btn3d_${btn.id}`;
    mesh.userData = {
      id: btn.id,
      isPressed: false,
      cooldown: 0,
      originalY: -2.2,
      originalScaleY: 1.0
    };

    // Create a clean HTML label overlay floating on the button
    const labelDiv = document.createElement('div');
    Object.assign(labelDiv.style, {
      color: '#ffffff',
      fontFamily: 'Outfit, sans-serif',
      fontSize: '12px',
      fontWeight: 'bold',
      letterSpacing: '1.5px',
      padding: '4px 10px',
      background: 'rgba(10, 15, 30, 0.85)',
      border: `2px solid ${new THREE.Color(btn.color).getStyle()}`,
      borderRadius: '6px',
      boxShadow: `0 0 15px ${new THREE.Color(btn.color).getStyle()}`,
      textShadow: '0 0 5px rgba(255, 255, 255, 0.5)',
      whiteSpace: 'nowrap'
    });
    labelDiv.textContent = btn.text;
    
    const labelObj = new CSS2DObject(labelDiv);
    labelObj.position.set(0, 0, 0.2); // Float in front of the box
    mesh.add(labelObj);

    this.uiButtonsGroup.add(mesh);
    this.pokeButtons.push(mesh);
  }

  // Clear all meshes from the scene
  clearAll() {
    this.nodesMap.forEach(node => {
      this.structureGroup.remove(node);
      // Remove HTML label
      const label = node.getObjectByName('label');
      if (label && label.element && label.element.parentNode) {
        label.element.parentNode.removeChild(label.element);
      }
    });
    this.nodesMap.clear();

    this.spawningNodes.forEach(node => {
      this.structureGroup.remove(node);
      const label = node.getObjectByName('label');
      if (label && label.element && label.element.parentNode) {
        label.element.parentNode.removeChild(label.element);
      }
    });
    this.spawningNodes.clear();

    // Reset structure transforms (for scaling/rotation gestures)
    this.structureGroup.scale.set(1, 1, 1);
    this.structureGroup.rotation.set(0, 0, 0);

    this.clearLinks();

    // Detach holographic step badge
    if (this.holoStepBadge.parent) {
      this.holoStepBadge.parent.remove(this.holoStepBadge);
    }
    this.holoStepDiv.classList.add('hidden');
  }

  clearLinks() {
    this.linksList.forEach(link => this.structureGroup.remove(link));
    this.linksList = [];
  }

  // Map logic state into 3D objects and target layouts
  syncState(state, topic) {
    if (!state) return;

    this.clearLinks();

    // 1. Process Nodes
    const currentActiveIds = new Set();

    if (topic === 'stack' || topic === 'queue') {
      const items = state.items || [];
      items.forEach((item, idx) => {
        currentActiveIds.add(item.id);
        const targetPos = this.calculateLayoutPosition(topic, idx, items.length);
        this.updateOrCreateNode(item.id, item.value, targetPos, item.state, topic);
      });
      // Queue connected blocks
      if (topic === 'queue') {
        for (let i = 0; i < items.length - 1; i++) {
          this.createLink(items[i].id, items[i + 1].id, 'normal', false);
        }
      }
    } 
    else if (topic === 'linkedlist') {
      const items = state.items || [];
      items.forEach((item, idx) => {
        currentActiveIds.add(item.id);
        const targetPos = this.calculateLayoutPosition(topic, idx, items.length);
        this.updateOrCreateNode(item.id, item.value, targetPos, item.state, topic);
      });

      // Handle standalone spawning node during insertion
      if (state.newNode) {
        const item = state.newNode;
        currentActiveIds.add(item.id);
        const targetPos = new THREE.Vector3(0, 3, 0); // Spawn in air
        this.updateOrCreateNode(item.id, item.value, targetPos, item.state, topic);
      }

      // Draw LinkedList link lines (arrows)
      for (let i = 0; i < items.length - 1; i++) {
        this.createLink(items[i].id, items[i + 1].id, 'normal', true);
      }
      // If we are linking the new node to its target neighbor
      if (state.newNode && state.insertIndex !== null) {
        const idx = state.insertIndex;
        // link new node to next
        if (state.type === 'insert_link_next') {
          if (items[idx]) {
            this.createLink(state.newNode.id, items[idx].id, 'active', true);
          }
        }
        // link previous to new node
        if (state.type === 'insert_link_prev') {
          if (items[idx - 1]) {
            this.createLink(items[idx - 1].id, state.newNode.id, 'active', true);
          }
        }
      }
    } 
    else if (topic === 'bst') {
      const treeNodes = state.nodes || [];
      treeNodes.forEach(node => {
        currentActiveIds.add(node.id);
        const targetPos = this.calculateLayoutPosition('bst', 0, 0, node.depth, node.posIndex);
        this.updateOrCreateNode(node.id, node.value, targetPos, node.state, topic);
      });

      // Handle spawning node
      if (state.newNode) {
        const item = state.newNode;
        currentActiveIds.add(item.id);
        const targetPos = new THREE.Vector3(4, 4, 0);
        this.updateOrCreateNode(item.id, item.value, targetPos, item.state, topic);
      }

      // Draw BST parent-child link lines
      treeNodes.forEach(node => {
        if (node.leftId) this.createLink(node.id, node.leftId, 'normal', false);
        if (node.rightId) this.createLink(node.id, node.rightId, 'normal', false);
      });
    } 
    else if (topic === 'graph') {
      const graphNodes = state.nodes || [];
      graphNodes.forEach(node => {
        currentActiveIds.add(node.id);
        const targetPos = this.graphCoordinates[node.id] || new THREE.Vector3();
        this.updateOrCreateNode(node.id, node.label, targetPos, node.state, topic);
      });

      // Draw Edges
      const graphEdges = state.edges || [];
      graphEdges.forEach(edge => {
        this.createLink(edge.from, edge.to, edge.state, false);
      });
    } 
    else if (topic === 'sorting') {
      const items = state.items || [];
      items.forEach((item, idx) => {
        currentActiveIds.add(item.id);
        const targetPos = this.calculateLayoutPosition('sorting', idx, items.length);
        this.updateOrCreateNode(item.id, item.value, targetPos, item.state, topic);
      });
    }

    // 2. Remove obsolete nodes
    this.nodesMap.forEach((node, id) => {
      if (!currentActiveIds.has(id)) {
        // Shrink node and remove
        this.structureGroup.remove(node);
        // Remove label
        const label = node.getObjectByName('label');
        if (label && label.element && label.element.parentNode) {
          label.element.parentNode.removeChild(label.element);
        }
        this.nodesMap.delete(id);
      }
    });

    // 3. Attach Holographic Step Badge to the active or highlighted node
    let activeNodeId = null;

    if (state.items) {
      const activeItem = state.items.find(item => ['active', 'highlighted', 'comparing', 'swapping'].includes(item.state));
      if (activeItem) activeNodeId = activeItem.id;
    }
    if (!activeNodeId && state.nodes) {
      const activeNode = state.nodes.find(node => ['active', 'highlighted', 'comparing', 'swapping'].includes(node.state));
      if (activeNode) activeNodeId = activeNode.id;
    }
    if (!activeNodeId && state.nodes && topic === 'graph') {
      const activeNode = state.nodes.find(node => node.state === 'active');
      if (activeNode) activeNodeId = activeNode.id;
    }

    if (activeNodeId && this.nodesMap.has(activeNodeId) && state.explanation) {
      const activeGroup = this.nodesMap.get(activeNodeId);
      this.holoStepDiv.textContent = state.explanation;
      this.holoStepDiv.classList.remove('hidden');

      if (this.holoStepBadge.parent) {
        this.holoStepBadge.parent.remove(this.holoStepBadge);
      }
      activeGroup.add(this.holoStepBadge);
    } else {
      if (this.holoStepBadge.parent) {
        this.holoStepBadge.parent.remove(this.holoStepBadge);
      }
      this.holoStepDiv.classList.add('hidden');
    }
  }

  // Calculate coordinates based on structured layouts
  calculateLayoutPosition(topic, index, total, depth = 0, posIndex = 0) {
    const pos = new THREE.Vector3();
    if (topic === 'stack') {
      // Stack Layout: float vertically
      pos.set(0, -2 + index * 1.3, 0);
    } 
    else if (topic === 'queue') {
      // Queue Layout: horizontal queue tunnel
      const spacing = 1.6;
      const startX = -((total - 1) * spacing) / 2;
      pos.set(startX + index * spacing, 0, 0);
    } 
    else if (topic === 'linkedlist') {
      // Linked List: horizontal list with pointers
      const spacing = 2.4;
      const startX = -((total - 1) * spacing) / 2;
      pos.set(startX + index * spacing, 1.5, 0);
    } 
    else if (topic === 'bst') {
      // Binary Search Tree: Root at top center, subtrees extend downwards
      const startY = 4.0;
      const levelHeight = 2.0;
      
      // Spacing scales down exponentially with depth to avoid node overlap
      const spacingX = 8.0 / Math.pow(2, depth);
      const levelX = (posIndex - (Math.pow(2, depth) - 1) / 2) * spacingX;
      
      pos.set(levelX, startY - depth * levelHeight, 0);
    } 
    else if (topic === 'sorting') {
      // Sorting columns arranged in a row
      const spacing = 1.8;
      const startX = -((total - 1) * spacing) / 2;
      pos.set(startX + index * spacing, -1.0, 0);
    }
    return pos;
  }

  updateOrCreateNode(id, value, targetPos, state, topic) {
    let nodeGroup = this.nodesMap.get(id);

    if (!nodeGroup) {
      // Create new node
      nodeGroup = new THREE.Group();
      nodeGroup.userData = {
        id,
        targetPos: targetPos.clone(),
        currentPos: targetPos.clone().add(new THREE.Vector3(0, 3, 0)), // slide down spawn
        targetScale: new THREE.Vector3(1, 1, 1),
        currentScale: new THREE.Vector3(0.01, 0.01, 0.01),
        targetColor: new THREE.Color(),
        currentColor: new THREE.Color(0x00f2fe),
        baseColor: new THREE.Color(0x00f2fe),
        phaseX: Math.random() * Math.PI * 2,
        phaseY: Math.random() * Math.PI * 2,
        isGrabbed: false
      };

      nodeGroup.position.copy(nodeGroup.userData.currentPos);
      nodeGroup.scale.copy(nodeGroup.userData.currentScale);

      // Create core geometry mesh
      let mesh;
      if (topic === 'sorting') {
        // Sorting items are cylinders whose height is proportional to the value
        const height = (value / 100) * 4.0 + 0.5; // Scale height to fit scene
        const columnGeo = new THREE.CylinderGeometry(0.4, 0.4, height, 32);
        const columnMat = new THREE.MeshPhongMaterial({
          color: 0x00f2fe,
          transparent: true,
          opacity: 0.85,
          shininess: 80,
          emissive: 0x003344
        });
        mesh = new THREE.Mesh(columnGeo, columnMat);
        mesh.position.y = height / 2; // Offset center so the base sits on coordinate
        mesh.name = 'core';
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        nodeGroup.add(mesh);
        
        // Update user data position offsets so columns align nicely
        nodeGroup.userData.heightOffset = height / 2;
      } else if (topic === 'stack') {
        // Stack as vertical floating block
        const blockGeo = new THREE.BoxGeometry(1.4, 0.6, 1.4);
        const mat = new THREE.MeshPhysicalMaterial({
          color: 0x00f2fe,
          transparent: true,
          opacity: 0.65,
          roughness: 0.1,
          metalness: 0.1,
          transmission: 0.6,
          thickness: 0.5,
          ior: 1.5,
          clearcoat: 1.0,
          emissive: 0x002233
        });
        mesh = new THREE.Mesh(blockGeo, mat);
        mesh.name = 'core';
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        nodeGroup.add(mesh);
      } else if (topic === 'queue') {
        // Queue as horizontal connected block
        const blockGeo = new THREE.BoxGeometry(1.2, 1.2, 1.2);
        const mat = new THREE.MeshPhysicalMaterial({
          color: 0x00f2fe,
          transparent: true,
          opacity: 0.65,
          roughness: 0.1,
          metalness: 0.1,
          transmission: 0.6,
          thickness: 0.5,
          ior: 1.5,
          clearcoat: 1.0,
          emissive: 0x002233
        });
        mesh = new THREE.Mesh(blockGeo, mat);
        mesh.name = 'core';
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        nodeGroup.add(mesh);
      } else {
        // Normal data structure node: Glowing Sphere
        const mat = new THREE.MeshPhysicalMaterial({
          color: 0x00f2fe,
          transparent: true,
          opacity: 0.65,
          roughness: 0.1,
          metalness: 0.1,
          transmission: 0.6, // Glassmorphic look
          thickness: 0.5,
          ior: 1.5,
          clearcoat: 1.0,
          emissive: 0x002233
        });
        mesh = new THREE.Mesh(this.sphereGeo, mat);
        mesh.name = 'core';
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        nodeGroup.add(mesh);

        // Surrounding orbital wireframe halo ring
        const ringGeo = new THREE.TorusGeometry(0.7, 0.02, 8, 48);
        const ringMat = new THREE.MeshBasicMaterial({
          color: 0x00f2fe,
          transparent: true,
          opacity: 0.3
        });
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.name = 'halo';
        ring.rotation.x = Math.PI / 4;
        ring.rotation.y = Math.PI / 4;
        nodeGroup.add(ring);
      }

      // Add CSS 2D Label overlay
      const labelDiv = document.createElement('div');
      labelDiv.className = 'node-label-badge';
      labelDiv.textContent = value;
      labelDiv.dataset.nodeId = id;
      
      const labelObj = new CSS2DObject(labelDiv);
      labelObj.name = 'label';
      // Adjust height offset for label based on structure
      if (topic === 'sorting') {
        const height = (value / 100) * 4.0 + 0.5;
        labelObj.position.set(0, height + 0.4, 0);
      } else {
        labelObj.position.set(0, 0, 0);
      }
      nodeGroup.add(labelObj);

      this.structureGroup.add(nodeGroup);
      this.nodesMap.set(id, nodeGroup);
    }

    // Update state indicators (target color & animations)
    nodeGroup.userData.targetPos.copy(targetPos);
    nodeGroup.userData.targetScale.set(1, 1, 1);

    const labelObj = nodeGroup.getObjectByName('label');
    const labelDiv = labelObj ? labelObj.element : null;
    if (labelDiv) {
      labelDiv.className = 'node-label-badge';
      labelDiv.textContent = value;
    }

    const coreMesh = nodeGroup.getObjectByName('core');
    const haloMesh = nodeGroup.getObjectByName('halo');

    // Color mapper based on state
    let stateColor = new THREE.Color(0x00f2fe); // default cyan
    if (state === 'highlighted' || state === 'comparing') {
      stateColor.setHex(0xff2e7e); // glowing pink (alert)
      if (labelDiv) labelDiv.classList.add('highlighted');
    } else if (state === 'active' || state === 'swapping') {
      stateColor.setHex(0xa855f7); // bright purple
      if (labelDiv) labelDiv.classList.add('active');
    } else if (state === 'success' || state === 'sorted') {
      stateColor.setHex(0x10b981); // emerald green
      if (labelDiv) labelDiv.style.borderColor = '#10b981';
    } else if (state === 'spawn') {
      stateColor.setHex(0xf59e0b); // orange warning
    }

    nodeGroup.userData.targetColor.copy(stateColor);
    nodeGroup.userData.baseColor.copy(stateColor);

    // Apply color to core and halo
    if (coreMesh && coreMesh.material) {
      coreMesh.material.color.copy(nodeGroup.userData.currentColor);
      if (coreMesh.material.emissive) {
        coreMesh.material.emissive.copy(nodeGroup.userData.currentColor).multiplyScalar(0.2);
      }
    }
    if (haloMesh && haloMesh.material) {
      haloMesh.material.color.copy(nodeGroup.userData.currentColor);
    }
  }

  // Draw arrow connections between nodes
  createLink(fromId, toId, state, isDirected = false) {
    const fromNode = this.nodesMap.get(fromId);
    const toNode = this.nodesMap.get(toId);
    if (!fromNode || !toNode) return;

    // We draw a line between the two current positions
    const p1 = fromNode.position;
    const p2 = toNode.position;

    // Calculate link parameters
    const distance = p1.distanceTo(p2);
    if (distance === 0) return;

    const cylinderGeo = new THREE.CylinderGeometry(0.05, 0.05, distance, 12);
    cylinderGeo.translate(0, distance / 2, 0);
    cylinderGeo.rotateX(Math.PI / 2);

    let linkColor = 0x1f2e4d; // faint dark blue default
    if (state === 'active') linkColor = 0xa855f7; // purple active wavefront
    else if (state === 'highlighted') linkColor = 0xff2e7e; // pink active link

    const material = new THREE.MeshBasicMaterial({
      color: linkColor,
      transparent: true,
      opacity: 0.6
    });

    const linkMesh = new THREE.Mesh(cylinderGeo, material);
    linkMesh.position.copy(p1);
    linkMesh.lookAt(p2);

    // If directed, add a small directional cone indicating vector flow
    if (isDirected) {
      const coneGeo = new THREE.ConeGeometry(0.15, 0.3, 12);
      coneGeo.rotateX(Math.PI / 2);
      const coneMat = new THREE.MeshBasicMaterial({ color: linkColor });
      const coneMesh = new THREE.Mesh(coneGeo, coneMat);
      
      // Position cone at 70% of the path to avoid overlaps
      const dirVec = new THREE.Vector3().subVectors(p2, p1).normalize();
      coneMesh.position.copy(dirVec).multiplyScalar(distance * 0.7);
      
      linkMesh.add(coneMesh);
    }

    this.structureGroup.add(linkMesh);
    this.linksList.push(linkMesh);
  }

  // Linear interpolation & levitation loops
  animate(time, deltaTime) {
    // Keep interpolation frame-rate independent
    const lerpSpeed = Math.min(deltaTime * 8, 1.0);

    // Update 3D Buttons animations
    if (this.pokeButtons) {
      this.pokeButtons.forEach(btn => {
        if (btn.userData.cooldown > 0) {
          btn.userData.cooldown -= deltaTime;
        }
        
        // Smoothly restore scale and position
        const targetScaleY = btn.userData.isPressed ? 0.3 : 1.0;
        const targetY = btn.userData.isPressed ? btn.userData.originalY - 0.1 : btn.userData.originalY;
        
        btn.scale.y = THREE.MathUtils.lerp(btn.scale.y, targetScaleY, deltaTime * 15);
        btn.position.y = THREE.MathUtils.lerp(btn.position.y, targetY, deltaTime * 15);
      });
    }

    this.nodesMap.forEach(node => {
      const ud = node.userData;

      // Rotate halos slowly for high-tech micro-animation
      const halo = node.getObjectByName('halo');
      if (halo) {
        halo.rotation.y += deltaTime * 0.5;
        halo.rotation.x += deltaTime * 0.2;
      }

      // Smooth color transitions
      ud.currentColor.lerp(ud.targetColor, lerpSpeed);

      // Apply color back to meshes
      const core = node.getObjectByName('core');
      if (core && core.material) {
        core.material.color.copy(ud.currentColor);
        if (core.material.emissive) {
          core.material.emissive.copy(ud.currentColor).multiplyScalar(0.15);
        }
      }
      const haloMesh = node.getObjectByName('halo');
      if (haloMesh && haloMesh.material) {
        haloMesh.material.color.copy(ud.currentColor);
      }

      // If grabbed by hand, let the grab controller handle positioning
      if (ud.isGrabbed) {
        ud.currentPos.copy(node.position);
        return;
      }

      // Lerp scale
      ud.currentScale.lerp(ud.targetScale, lerpSpeed);
      node.scale.copy(ud.currentScale);

      // Lerp base position
      ud.currentPos.lerp(ud.targetPos, lerpSpeed);

      // Apply zero-gravity multi-frequency floating drift
      const floatX = Math.sin(time * 1.2 + ud.phaseX) * 0.08 + Math.cos(time * 0.6) * 0.03;
      const floatY = Math.cos(time * 1.5 + ud.phaseY) * 0.12 + Math.sin(time * 0.9) * 0.05;
      const floatZ = Math.sin(time * 1.0 + ud.phaseX) * 0.06;

      node.position.copy(ud.currentPos).add(new THREE.Vector3(floatX, floatY, floatZ));
    });
  }
}
