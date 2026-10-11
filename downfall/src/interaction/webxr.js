import * as THREE from 'three';

export class XRManager {
  constructor(renderer, scene, camera, animEngine) {
    this.renderer = renderer;
    this.scene = scene;
    this.camera = camera;
    this.animEngine = animEngine;
    this.xrSession = null;
    this.controllers = [];
    this.hands = [];

    this.checkXRSupport();
  }

  async checkXRSupport() {
    const btn = document.getElementById('btn-xr');
    if (!btn) return;

    if ('xr' in navigator) {
      const isSupported = await navigator.xr.isSessionSupported('immersive-vr');
      if (isSupported) {
        btn.addEventListener('click', this.toggleXRSession.bind(this));
      } else {
        btn.querySelector('span').textContent = 'VR NOT SUPPORTED';
        btn.style.opacity = '0.5';
        btn.style.pointerEvents = 'none';
      }
    } else {
      btn.querySelector('span').textContent = 'XR API NOT FOUND';
      btn.style.opacity = '0.5';
      btn.style.pointerEvents = 'none';
    }
  }

  async toggleXRSession() {
    if (!this.xrSession) {
      // Enter VR
      try {
        const session = await navigator.xr.requestSession('immersive-vr', {
          optionalFeatures: ['local-floor', 'bounded-floor', 'hand-tracking']
        });
        
        this.renderer.xr.enabled = true;
        await this.renderer.xr.setSession(session);
        this.xrSession = session;
        
        document.getElementById('btn-xr').querySelector('span').textContent = 'EXIT IMMERSIVE MODE';
        
        this.setupXRControllers();
        
        session.addEventListener('end', () => {
          this.xrSession = null;
          document.getElementById('btn-xr').querySelector('span').textContent = 'ENTER IMMERSIVE MODE';
        });
      } catch (err) {
        console.error('Failed to start WebXR Session:', err);
      }
    } else {
      // Exit VR
      this.xrSession.end();
    }
  }

  setupXRControllers() {
    // Controller 0 (Left)
    const controller1 = this.renderer.xr.getController(0);
    this.scene.add(controller1);
    this.controllers.push(controller1);

    // Controller 1 (Right)
    const controller2 = this.renderer.xr.getController(1);
    this.scene.add(controller2);
    this.controllers.push(controller2);

    // Hand tracking (Standard WebXR hand skeleton profiles)
    const hand1 = this.renderer.xr.getHand(0);
    this.scene.add(hand1);
    this.hands.push(hand1);

    const hand2 = this.renderer.xr.getHand(1);
    this.scene.add(hand2);
    this.hands.push(hand2);

    // Add pointer lasers for controllers
    const laserGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, 0, 0),
      new THREE.Vector3(0, 0, -5)
    ]);
    const laserMat = new THREE.LineBasicMaterial({ color: 0x00f2fe });
    
    this.controllers.forEach(c => {
      const laser = new THREE.Line(laserGeo, laserMat);
      c.add(laser);
    });

    // Joint visualization meshes if hand tracking is active
    // We can equip each hand with standard joint spheres when they appear
    this.hands.forEach(hand => {
      hand.addEventListener('connected', () => {
        // Standard WebXR input joint count is 25 joints
        for (let i = 0; i < 25; i++) {
          const jointGeo = new THREE.SphereGeometry(0.015, 8, 8);
          const jointMat = new THREE.MeshBasicMaterial({ color: 0xa855f7 });
          const jointMesh = new THREE.Mesh(jointGeo, jointMat);
          hand.add(jointMesh);
        }
      });
    });
  }

  update() {
    // Check joint distance for pinch gestures in VR if hand tracking is active
    if (this.xrSession && this.hands.length > 0) {
      this.hands.forEach(hand => {
        // WebXR exposing joints
        const indexTip = hand.joints ? hand.joints['index-finger-tip'] : null;
        const thumbTip = hand.joints ? hand.joints['thumb-tip'] : null;

        if (indexTip && thumbTip) {
          const dist = indexTip.position.distanceTo(thumbTip.position);
          if (dist < 0.02) {
            // Pinch detected! Run raycast from index tip to trigger grabs.
            this.handleXRPinch(indexTip.position);
          }
        }
      });
    }
  }

  handleXRPinch(pinchPos) {
    // Loop through sceneAnimator node groups and check proximity
    this.animEngine.nodesMap.forEach(group => {
      const nodePos = new THREE.Vector3();
      group.getWorldPosition(nodePos);
      const dist = nodePos.distanceTo(pinchPos);
      
      if (dist < 0.5) {
        // Drag node to pinch position
        group.position.copy(pinchPos);
        group.userData.currentPos.copy(pinchPos);
      }
    });
  }
}
