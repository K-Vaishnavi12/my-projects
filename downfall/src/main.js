import * as THREE from 'three';
import { VisualEngine } from './visualization/engine';
import { ClassroomEnvironment } from './visualization/environment';
import { SceneAnimator } from './visualization/animator';
import { DesktopHandSimulator } from './interaction/handSim';
import { WebcamHandsManager } from './interaction/webcamHands';
import { XRManager } from './interaction/webxr';
import { HUDController } from './ui/hud';
import './style.css';

document.addEventListener('DOMContentLoaded', () => {
  // 1. Boot up 3D Visual Engine
  const visualEngine = new VisualEngine('canvas-container', 'css-labels-container');

  // 2. Setup Holographic Classroom environment
  const environment = new ClassroomEnvironment(visualEngine.scene);

  // 3. Setup Scene Animator mapping data to meshes
  const sceneAnimator = new SceneAnimator(visualEngine.scene);

  // Bind controls references inside sceneAnimator for keyboard/orbit interactions
  sceneAnimator.controls = visualEngine.controls;

  // 4. Setup Desktop Cyber-glove Raycast Simulator
  const handSimulator = new DesktopHandSimulator(
    visualEngine.scene,
    visualEngine.camera,
    visualEngine.renderer,
    sceneAnimator
  );

  // Setup Webcam Tracking Manager and start camera feed immediately
  const webcamManager = new WebcamHandsManager(handSimulator);
  webcamManager.start();

  // 5. Setup WebXR headset & hand tracker session bindings
  const xrManager = new XRManager(
    visualEngine.renderer,
    visualEngine.scene,
    visualEngine.camera,
    sceneAnimator
  );

  // 6. Setup Front-end HUD panels and user trigger actions
  const hud = new HUDController(sceneAnimator, visualEngine);
  hud.handSimulator = handSimulator;
  handSimulator.hud = hud;

  // 7. Initialize precision timestamp timers (replaces deprecated THREE.Clock)
  let lastTime = performance.now();
  let elapsedTime = 0;

  // 8. Run unified WebXR-compatible rendering loop
  visualEngine.renderer.setAnimationLoop((timestamp) => {
    // timestamp is in milliseconds
    const currentTime = performance.now();
    const deltaTime = Math.min((currentTime - lastTime) / 1000, 0.1); // cap delta to avoid physics jumps
    lastTime = currentTime;
    elapsedTime += deltaTime;

    // Update classroom grids, orbits and upwards particles
    environment.animate(elapsedTime);

    // Update active node positions and levitations
    sceneAnimator.animate(elapsedTime, deltaTime);

    // Update desktop cursor glove springs and momentum physics
    handSimulator.update(elapsedTime, deltaTime);

    // Check VR fingertip pinches
    xrManager.update();

    // Process step timelines
    hud.update(timestamp);

    // Update camera controls
    visualEngine.update(deltaTime);

    // Render WebGL and CSS2D overlays
    visualEngine.render();
  });
});
