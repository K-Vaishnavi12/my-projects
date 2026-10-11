export class WebcamHandsManager {
  constructor(handSimulator) {
    this.handSimulator = handSimulator;
    this.videoElement = document.getElementById('webcam-feed');
    this.canvasElement = document.getElementById('webcam-overlay');
    this.canvasCtx = this.canvasElement ? this.canvasElement.getContext('2d') : null;
    this.webcamDeck = document.getElementById('webcam-deck');
    this.isActive = false;

    // Set canvas resolution
    if (this.canvasElement) {
      this.canvasElement.width = 240;
      this.canvasElement.height = 150;
    }

    if (window.Hands && window.Camera) {
      this.init();
    } else {
      console.warn('MediaPipe script resources not found. Webcam tracking deactivated.');
    }
  }

  init() {
    this.hands = new window.Hands({
      locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
    });

    this.hands.setOptions({
      maxNumHands: 2,
      modelComplexity: 0, // Optimize for speed to prevent hand tracking lag
      minDetectionConfidence: 0.55,
      minTrackingConfidence: 0.55
    });

    this.hands.onResults(this.onResults.bind(this));

    this.camera = new window.Camera(this.videoElement, {
      onFrame: async () => {
        if (this.isActive) {
          try {
            await this.hands.send({ image: this.videoElement });
          } catch (err) {
            // Suppress frames error on background tabs
          }
        }
      },
      width: 320,
      height: 240
    });
  }

  start() {
    if (!this.camera) return;
    this.isActive = true;
    if (this.webcamDeck) {
      this.webcamDeck.classList.remove('hidden');
    }
    this.camera.start()
      .then(() => {
        console.log('Webcam gesture tracking active.');
      })
      .catch(err => {
        console.error('Webcam access failed:', err);
        if (this.webcamDeck) {
          this.webcamDeck.classList.add('hidden');
        }
      });
  }

  stop() {
    this.isActive = false;
    if (this.webcamDeck) {
      this.webcamDeck.classList.add('hidden');
    }
  }

  onResults(results) {
    if (!this.canvasCtx) return;

    this.canvasCtx.save();
    this.canvasCtx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);
    
    // Draw mirrored skeletons for feedback
    this.canvasCtx.scale(-1, 1);
    this.canvasCtx.translate(-this.canvasElement.width, 0);

    const hasHands = results.multiHandLandmarks && results.multiHandLandmarks.length > 0;
    
    if (hasHands) {
      // Forward tracked landmarks to handSimulator for 3D mapping
      this.handSimulator.updateFromWebcam(results.multiHandLandmarks, results.multiHandedness);
      
      // Draw overlay bones
      results.multiHandLandmarks.forEach((landmarks, index) => {
        const handedness = results.multiHandedness[index].label; // "Left" or "Right"
        // Note: MediaPipe mirrors camera internally, so Left is visually Right and vice versa
        const isRight = handedness === 'Left'; // Map opposite to align visually on mirrored canvas
        
        this.canvasCtx.fillStyle = isRight ? '#00f2fe' : '#ff2e7e';
        this.canvasCtx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
        this.canvasCtx.lineWidth = 1.5;

        // Draw joints
        landmarks.forEach(lm => {
          const cx = lm.x * this.canvasElement.width;
          const cy = lm.y * this.canvasElement.height;
          this.canvasCtx.beginPath();
          this.canvasCtx.arc(cx, cy, 2.5, 0, 2 * Math.PI);
          this.canvasCtx.fill();
        });

        // Skeleton joint loops
        const connections = [
          [0, 1], [1, 2], [2, 3], [3, 4], // Thumb
          [0, 5], [5, 6], [6, 7], [7, 8], // Index
          [5, 9], [9, 10], [10, 11], [11, 12], // Middle
          [9, 13], [13, 14], [14, 15], [15, 16], // Ring
          [13, 17], [17, 18], [18, 19], [19, 20], // Pinky
          [0, 17] // Palm wrap
        ];

        connections.forEach(conn => {
          const p1 = landmarks[conn[0]];
          const p2 = landmarks[conn[1]];
          this.canvasCtx.beginPath();
          this.canvasCtx.moveTo(p1.x * this.canvasElement.width, p1.y * this.canvasElement.height);
          this.canvasCtx.lineTo(p2.x * this.canvasElement.width, p2.y * this.canvasElement.height);
          this.canvasCtx.stroke();
        });
      });
    } else {
      this.handSimulator.updateFromWebcam([], []);
    }
    
    this.canvasCtx.restore();
  }
}
