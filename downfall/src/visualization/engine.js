import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { CSS2DRenderer } from 'three/examples/jsm/renderers/CSS2DRenderer.js';

export class VisualEngine {
  constructor(containerId, labelsContainerId) {
    this.container = document.getElementById(containerId);
    this.labelsContainer = document.getElementById(labelsContainerId);
    
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x050811); // Midnight blue deep space
    this.scene.fog = new THREE.FogExp2(0x050811, 0.015);

    // Setup WebGL Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFShadowMap;
    this.container.appendChild(this.renderer.domElement);

    // Setup CSS 2D Renderer for HTML labels
    this.labelRenderer = new CSS2DRenderer();
    this.labelRenderer.setSize(this.container.clientWidth, this.container.clientHeight);
    this.labelRenderer.domElement.style.position = 'absolute';
    this.labelRenderer.domElement.style.top = '0px';
    this.labelRenderer.domElement.style.pointerEvents = 'none'; // Click-through
    this.labelsContainer.appendChild(this.labelRenderer.domElement);

    // Setup Camera
    this.camera = new THREE.PerspectiveCamera(
      60,
      this.container.clientWidth / this.container.clientHeight,
      0.1,
      1000
    );
    this.camera.position.set(0, 5, 12);

    // Setup Orbit Controls
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    this.controls.maxPolarAngle = Math.PI / 2 + 0.1; // Limit below ground
    this.controls.minDistance = 2;
    this.controls.maxDistance = 40;

    // Initialize camera targets for smooth transition lerps
    this.targetCameraPos = this.camera.position.clone();
    this.targetControlsTarget = this.controls.target.clone();
    this.focusModeActive = false;

    // Add Lights
    this.setupLights();

    // Resize Event
    window.addEventListener('resize', this.onWindowResize.bind(this));
  }

  setupLights() {
    // Soft Ambient lighting
    const ambientLight = new THREE.AmbientLight(0x1a243d, 1.5);
    this.scene.add(ambientLight);

    // Glowing Neon Spotlight - Cyan (saved as class properties)
    this.spotCyan = new THREE.SpotLight(0x00f2fe, 120, 30, Math.PI / 4, 0.5, 1);
    this.spotCyan.position.set(-6, 10, 4);
    this.spotCyan.castShadow = true;
    this.scene.add(this.spotCyan);

    // Glowing Neon Spotlight - Purple
    this.spotPurple = new THREE.SpotLight(0xa855f7, 120, 30, Math.PI / 4, 0.5, 1);
    this.spotPurple.position.set(6, 10, -4);
    this.spotPurple.castShadow = true;
    this.scene.add(this.spotPurple);

    // Soft directional overhead light
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(0, 15, 0);
    this.scene.add(dirLight);
  }

  setFocusMode(enabled) {
    this.focusModeActive = enabled;
    if (enabled) {
      this.scene.fog.density = 0.08; // High fog to mask background starfield
      if (this.spotCyan) this.spotCyan.intensity = 30; // Dim spotlights
      if (this.spotPurple) this.spotPurple.intensity = 30;
      this.targetCameraPos.set(0, 2.0, 6.0); // Move camera closer
      this.targetControlsTarget.set(0, 0.5, 0); // Aim slightly higher
    } else {
      this.scene.fog.density = 0.015; // Reset fog
      if (this.spotCyan) this.spotCyan.intensity = 120;
      if (this.spotPurple) this.spotPurple.intensity = 120;
      this.targetCameraPos.set(0, 5, 12); // Reset camera
      this.targetControlsTarget.set(0, 0, 0);
    }
  }

  onWindowResize() {
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;

    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();

    this.renderer.setSize(width, height);
    this.labelRenderer.setSize(width, height);
  }

  update(deltaTime = 0.016) {
    const lerpSpeed = Math.min(deltaTime * 4, 1.0);
    
    // Only auto-lerp if user is not actively dragging/manipulating camera
    if (this.controls.state === -1) {
      this.camera.position.lerp(this.targetCameraPos, lerpSpeed);
      this.controls.target.lerp(this.targetControlsTarget, lerpSpeed);
    }
    
    this.controls.update();
  }

  render() {
    this.renderer.render(this.scene, this.camera);
    this.labelRenderer.render(this.scene, this.camera);
  }
}
