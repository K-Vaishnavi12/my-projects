export class VirtualKeyboard {
  constructor() {
    this.activeInput = null;
    this.container = null;
    this.init();
  }

  init() {
    // 1. Create keyboard container
    this.container = document.createElement('div');
    this.container.id = 'virtual-keyboard';
    this.container.className = 'glass-panel hidden';
    
    // Style container
    Object.assign(this.container.style, {
      position: 'fixed',
      bottom: '260px',
      left: '50%',
      transform: 'translateX(-50%)',
      width: '480px',
      zIndex: '200',
      padding: '12px',
      gap: '6px',
      display: 'flex',
      flexDirection: 'column',
      boxShadow: '0 12px 40px rgba(0, 0, 0, 0.5)',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      background: 'rgba(15, 23, 42, 0.85)',
      backdropFilter: 'blur(16px)',
      borderRadius: '12px',
      transition: 'opacity 0.3s ease, transform 0.3s ease'
    });

    // Add keyboard title header
    const header = document.createElement('div');
    header.style.display = 'flex';
    header.style.justify = 'space-between';
    header.style.alignItems = 'center';
    header.style.borderBottom = '1px solid rgba(255, 255, 255, 0.08)';
    header.style.paddingBottom = '4px';
    header.style.marginBottom = '6px';
    header.innerHTML = `
      <span style="font-family: Outfit, sans-serif; font-size: 10px; font-weight: bold; color: #00f2fe; letter-spacing: 1.5px;">GUESTURE INPUT DECK</span>
      <span id="keyboard-close-btn" style="color: #ff2e7e; font-size: 12px; cursor: pointer; font-weight: bold;">✕</span>
    `;
    this.container.appendChild(header);

    // Keyboard layout rows
    const layout = [
      ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
      ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
      ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', '-'],
      ['Z', 'X', 'C', 'V', 'B', 'N', 'M', 'Space', 'Back'],
      ['Clear', 'Enter', 'Close']
    ];

    layout.forEach(row => {
      const rowDiv = document.createElement('div');
      Object.assign(rowDiv.style, {
        display: 'flex',
        gap: '6px',
        width: '100%',
        justifyContent: 'center'
      });

      row.forEach(keyText => {
        const keyBtn = document.createElement('button');
        keyBtn.className = 'action-btn btn-secondary';
        keyBtn.textContent = keyText;
        
        // Base key styling
        Object.assign(keyBtn.style, {
          padding: '8px 0',
          fontSize: '11px',
          fontFamily: 'JetBrains Mono, monospace',
          fontWeight: 'bold',
          flex: '1',
          minWidth: '24px',
          textAlign: 'center',
          cursor: 'pointer',
          borderRadius: '6px',
          border: '1px solid rgba(255, 255, 255, 0.05)',
          background: 'rgba(255, 255, 255, 0.03)',
          transition: 'all 0.1s ease'
        });

        // Special sizes
        if (keyText === 'Space') keyBtn.style.flex = '2';
        if (keyText === 'Back') {
          keyBtn.style.flex = '1.5';
          keyBtn.style.color = '#ff2e7e';
        }
        if (['Clear', 'Close'].includes(keyText)) {
          keyBtn.style.color = '#ff2e7e';
        }
        if (keyText === 'Enter') {
          keyBtn.style.color = '#00f2fe';
          keyBtn.style.borderColor = '#00f2fe';
          keyBtn.style.background = 'rgba(0, 242, 254, 0.05)';
        }

        // Add action listener
        keyBtn.addEventListener('click', (e) => {
          e.preventDefault();
          this.handleKeyPress(keyText);
        });

        rowDiv.appendChild(keyBtn);
      });

      this.container.appendChild(rowDiv);
    });

    document.body.appendChild(this.container);

    // Bind Close Button click
    this.container.querySelector('#keyboard-close-btn').addEventListener('click', () => this.hide());

    // Bind Focus events to inputs on the page
    this.bindToInputs();
  }

  bindToInputs() {
    const inputs = document.querySelectorAll('input[type="text"], input[type="number"]');
    inputs.forEach(input => {
      input.addEventListener('focus', () => {
        this.show(input);
      });
    });
  }

  handleKeyPress(key) {
    if (!this.activeInput) return;

    const cursorStart = this.activeInput.selectionStart || 0;
    const cursorEnd = this.activeInput.selectionEnd || 0;
    const currentVal = this.activeInput.value;

    if (key === 'Close' || key === '✕') {
      this.hide();
      return;
    } else if (key === 'Clear') {
      this.activeInput.value = '';
    } else if (key === 'Back') {
      if (cursorStart === cursorEnd) {
        if (cursorStart > 0) {
          this.activeInput.value = currentVal.slice(0, cursorStart - 1) + currentVal.slice(cursorStart);
          try {
            this.activeInput.setSelectionRange(cursorStart - 1, cursorStart - 1);
          } catch (e) {}
        }
      } else {
        this.activeInput.value = currentVal.slice(0, cursorStart) + currentVal.slice(cursorEnd);
        try {
          this.activeInput.setSelectionRange(cursorStart, cursorStart);
        } catch (e) {}
      }
    } else if (key === 'Enter') {
      // Find the closest parent form or the action button to submit
      const parentGroup = this.activeInput.closest('.ctrl-group, .command-container');
      if (parentGroup) {
        // Trigger click on primary button
        const enterBtn = parentGroup.querySelector('.glow-btn-cyan, #btn-cmd-enter');
        if (enterBtn) {
          enterBtn.click();
        }
      }
      this.hide();
      return;
    } else {
      const char = (key === 'Space') ? ' ' : key;
      this.activeInput.value = currentVal.slice(0, cursorStart) + char + currentVal.slice(cursorEnd);
      const newPos = cursorStart + char.length;
      try {
        this.activeInput.setSelectionRange(newPos, newPos);
      } catch (e) {}
    }

    if (this.activeInput) {
      // Trigger input event so framework/listeners recognize value change
      this.activeInput.dispatchEvent(new Event('input', { bubbles: true }));
    }
  }

  show(input) {
    this.activeInput = input;
    this.container.classList.remove('hidden');
    this.container.style.opacity = '1';
    this.container.style.transform = 'translateX(-50%) translateY(0)';
  }

  hide() {
    this.container.classList.add('hidden');
    this.container.style.opacity = '0';
    this.container.style.transform = 'translateX(-50%) translateY(10px)';
    if (this.activeInput) {
      this.activeInput.blur();
      this.activeInput = null;
    }
  }
}
