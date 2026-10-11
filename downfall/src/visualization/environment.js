import * as THREE from 'three';

export class ClassroomEnvironment {
  constructor(scene) {
    this.scene = scene;
    this.particleCount = 200;
    
    this.createGridFloor();
    this.createStarfield();
    this.createDriftingParticles();
  }

  createGridFloor() {
    // Holographic wireframe grid
    const size = 60;
    const divisions = 40;
    
    // Main grid
    this.grid = new THREE.GridHelper(size, divisions, 0x00f2fe, 0x1f2e4d);
    this.grid.position.y = -4;
    // Lower opacity to keep it subtle
    this.grid.material.opacity = 0.25;
    this.grid.material.transparent = true;
    this.scene.add(this.grid);

    // Outer boundary ring
    const ringGeo = new THREE.RingGeometry(29.8, 30, 64);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0xa855f7,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.15
    });
    this.boundaryRing = new THREE.Mesh(ringGeo, ringMat);
    this.boundaryRing.rotation.x = Math.PI / 2;
    this.boundaryRing.position.y = -3.98;
    this.scene.add(this.boundaryRing);
  }

  createStarfield() {
    const starCount = 800;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(starCount * 3);
    const colors = new Float32Array(starCount * 3);

    for (let i = 0; i < starCount; i++) {
      // Distribute stars in a large sphere
      const u = Math.random();
      const v = Math.random();
      const theta = u * 2.0 * Math.PI;
      const phi = Math.acos(2.0 * v - 1.0);
      const r = 100 + Math.random() * 50; // Distance

      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = r * Math.cos(phi);

      // Star colors (whitish cyan and purple tints)
      const colorVal = 0.6 + Math.random() * 0.4;
      if (Math.random() > 0.5) {
        colors[i * 3] = colorVal * 0.8;
        colors[i * 3 + 1] = colorVal * 0.9;
        colors[i * 3 + 2] = colorVal;
      } else {
        colors[i * 3] = colorVal;
        colors[i * 3 + 1] = colorVal * 0.8;
        colors[i * 3 + 2] = colorVal * 0.95;
      }
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
      size: 0.5,
      vertexColors: true,
      transparent: true,
      opacity: 0.8,
      sizeAttenuation: true
    });

    this.starfield = new THREE.Points(geometry, material);
    this.scene.add(this.starfield);
  }

  createDriftingParticles() {
    // Upward drifting ambient particles
    this.particleGeometry = new THREE.BufferGeometry();
    this.particlePositions = new Float32Array(this.particleCount * 3);
    this.particleSpeeds = new Float32Array(this.particleCount);

    for (let i = 0; i < this.particleCount; i++) {
      // Spawn within a bounding box
      this.particlePositions[i * 3] = (Math.random() - 0.5) * 30;     // X
      this.particlePositions[i * 3 + 1] = (Math.random() - 0.5) * 20; // Y
      this.particlePositions[i * 3 + 2] = (Math.random() - 0.5) * 30; // Z
      
      this.particleSpeeds[i] = 0.01 + Math.random() * 0.02; // Speed
    }

    this.particleGeometry.setAttribute('position', new THREE.BufferAttribute(this.particlePositions, 3));

    // Simple round particle texture using a canvas
    const pCanvas = document.createElement('canvas');
    pCanvas.width = 16;
    pCanvas.height = 16;
    const ctx = pCanvas.getContext('2d');
    const grad = ctx.createRadialGradient(8, 8, 0, 8, 8, 8);
    grad.addColorStop(0, 'rgba(0, 242, 254, 1)');
    grad.addColorStop(1, 'rgba(0, 242, 254, 0)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 16, 16);

    const texture = new THREE.CanvasTexture(pCanvas);

    const material = new THREE.PointsMaterial({
      size: 0.4,
      map: texture,
      transparent: true,
      opacity: 0.4,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      sizeAttenuation: true
    });

    this.particles = new THREE.Points(this.particleGeometry, material);
    this.scene.add(this.particles);
  }

  animate(time) {
    // Rotate grid floor slowly
    if (this.grid) {
      this.grid.rotation.y = time * 0.02;
    }
    if (this.boundaryRing) {
      this.boundaryRing.rotation.z = -time * 0.02;
    }

    // Slowly rotate background starfield
    if (this.starfield) {
      this.starfield.rotation.y = time * 0.003;
      this.starfield.rotation.x = time * 0.001;
    }

    // Update drifting particles position
    if (this.particles) {
      const positions = this.particleGeometry.attributes.position.array;

      for (let i = 0; i < this.particleCount; i++) {
        // Increment Y (upward drift)
        positions[i * 3 + 1] += this.particleSpeeds[i];

        // Reset to bottom if drifted too high
        if (positions[i * 3 + 1] > 12) {
          positions[i * 3 + 1] = -12;
          positions[i * 3] = (Math.random() - 0.5) * 30;
          positions[i * 3 + 2] = (Math.random() - 0.5) * 30;
        }
      }

      this.particleGeometry.attributes.position.needsUpdate = true;
    }
  }
}
