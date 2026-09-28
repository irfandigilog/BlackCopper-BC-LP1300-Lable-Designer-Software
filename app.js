// TSPL Label Designer Core Engine

const state = {
    labelWidth: 40,   // mm
    labelHeight: 30,  // mm
    scale: 8,         // 1mm = 8px on screen roughly (scaling logic)
    elements: [],
    selectedId: null,
    printerPort: null,
    connectionType: null
};

// Elements DOM
const els = {
    widthInput: document.getElementById('label-width'),
    heightInput: document.getElementById('label-height'),
    canvas: document.getElementById('label-canvas'),
    btnAddText: document.getElementById('btn-add-text'),
    btnAddBarcode: document.getElementById('btn-add-barcode'),
    btnAddBox: document.getElementById('btn-add-box'),
    btnAddLine: document.getElementById('btn-add-line'),
    btnAddCircle: document.getElementById('btn-add-circle'),
    propertiesPanel: document.getElementById('property-controls'),
    emptyState: document.querySelector('.empty-state'),
    btnConnect: document.getElementById('btn-connect'),
    btnPrintDirect: document.getElementById('btn-print-direct'),
    btnCalibrate: document.getElementById('btn-calibrate'),
    modal: document.getElementById('code-modal'),
    btnCloseModal: document.getElementById('btn-close-modal'),
    tsplOutput: document.getElementById('tspl-output'),
    btnCopyCode: document.getElementById('btn-copy-code'),
    btnPrintCode: document.getElementById('btn-print')
};

// Initialize
function init() {
    updateCanvasSize();

    // Listeners
    els.widthInput.addEventListener('input', (e) => { state.labelWidth = Number(e.target.value); updateCanvasSize(); });
    els.heightInput.addEventListener('input', (e) => { state.labelHeight = Number(e.target.value); updateCanvasSize(); });

    els.btnAddText.addEventListener('click', () => addElement('text'));
    els.btnAddBarcode.addEventListener('click', () => addElement('barcode'));

    // Print directly
    els.btnPrintDirect.addEventListener('click', printLabel);

    // Close modal
    els.btnCloseModal.addEventListener('click', () => els.modal.classList.add('hidden'));

    // Connect Printer
    els.btnConnect.addEventListener('click', connectPrinter);
}

function updateCanvasSize() {
    els.canvas.style.width = `${state.labelWidth * state.scale}px`;
    els.canvas.style.height = `${state.labelHeight * state.scale}px`;
}

function generateId() {
    return 'el_' + Math.random().toString(36).substr(2, 9);
}

function addElement(type) {
    const el = {
        id: generateId(),
        type: type,
        x: 10,  // mm
        y: 10,  // mm
    };

    if (type === 'text') {
        el.text = "Hello World";
        el.fontType = "2"; // TSPL built-in font
        el.fontSize = 1; // multi
    } else if (type === 'barcode') {
        el.data = "12345678";
        el.barcodeType = "128";
        el.height = 10; // mm
    } else if (type === 'box') {
        el.w = 20; // width mm
        el.h = 10; // height mm
        el.thickness = 2; // dots
    } else if (type === 'line') {
        el.w = 30; // mm
        el.h = 1;  // mm (thickness)
    } else if (type === 'circle') {
        el.diameter = 15; // mm
        el.thickness = 2; // dots
    }

    state.elements.push(el);
    selectElement(el.id);
    renderCanvas();
}

function selectElement(id) {
    state.selectedId = id;
    renderCanvas();
    renderProperties();
}

function updateElement(id, updates) {
    const idx = state.elements.findIndex(e => e.id === id);
    if (idx > -1) {
        state.elements[idx] = { ...state.elements[idx], ...updates };
        renderCanvas();
    }
}

function renderCanvas() {
    els.canvas.innerHTML = '';
    state.elements.forEach(el => {
        const div = document.createElement('div');
        div.className = `canvas-element ${el.id === state.selectedId ? 'selected' : ''}`;
        div.style.left = `${el.x * state.scale}px`;
        div.style.top = `${el.y * state.scale}px`;

        if (el.type === 'text') {
            div.classList.add('element-text');
            div.style.fontSize = `${el.fontSize * 16}px`;
            div.textContent = el.text;
        } else if (el.type === 'barcode') {
            div.classList.add('element-barcode');
            const lines = document.createElement('div');
            lines.className = 'mock-barcode-lines';
            lines.style.height = `${el.height * state.scale}px`;
            const text = document.createElement('div');
            text.className = 'mock-barcode-text';
            text.textContent = el.data;
            div.appendChild(lines);
            div.appendChild(text);
        } else if (el.type === 'box') {
            div.style.width = `${el.w * state.scale}px`;
            div.style.height = `${el.h * state.scale}px`;
            div.style.border = `${el.thickness}px solid #000`;
            div.style.backgroundColor = 'transparent';
        } else if (el.type === 'line') {
            div.style.width = `${el.w * state.scale}px`;
            // Using min 1px for visible mock length
            div.style.height = `${Math.max(1, el.h * state.scale)}px`;
            div.style.backgroundColor = '#000';
        } else if (el.type === 'circle') {
            // Draw circle based on diameter
            div.style.width = `${el.diameter * state.scale}px`;
            div.style.height = `${el.diameter * state.scale}px`;
            div.style.border = `${el.thickness}px solid #000`;
            div.style.borderRadius = '50%';
            div.style.backgroundColor = 'transparent';
        }

        // Drag logic
        div.addEventListener('mousedown', (e) => startDrag(e, el));
        els.canvas.appendChild(div);
    });
}

function startDrag(e, el) {
    e.stopPropagation();
    selectElement(el.id);

    let startX = e.clientX;
    let startY = e.clientY;
    let originalX = el.x;
    let originalY = el.y;

    function onMouseMove(moveEvent) {
        const dx = (moveEvent.clientX - startX) / state.scale;
        const dy = (moveEvent.clientY - startY) / state.scale;

        updateElement(el.id, {
            x: Math.max(0, originalX + dx),
            y: Math.max(0, originalY + dy)
        });

        // Update properties panel instantly if active
        const xInput = document.getElementById('prop-x');
        const yInput = document.getElementById('prop-y');
        if (xInput && yInput) {
            xInput.value = Math.round(Math.max(0, originalX + dx));
            yInput.value = Math.round(Math.max(0, originalY + dy));
        }
    }

    function onMouseUp() {
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
    }

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
}

// Deselect on canvas background click
els.canvas.addEventListener('mousedown', (e) => {
    if (e.target === els.canvas) {
        selectElement(null);
    }
});

function renderProperties() {
    if (!state.selectedId) {
        els.emptyState.classList.remove('hidden');
        els.propertiesPanel.classList.add('hidden');
        return;
    }

    els.emptyState.classList.add('hidden');
    els.propertiesPanel.classList.remove('hidden');

    const el = state.elements.find(e => e.id === state.selectedId);
    let html = `
        <div class="input-group">
            <label>X Position (mm)</label>
            <input type="number" id="prop-x" value="${Math.round(el.x)}">
        </div>
        <div class="input-group">
            <label>Y Position (mm)</label>
            <input type="number" id="prop-y" value="${Math.round(el.y)}">
        </div>
    `;

    if (el.type === 'text') {
        html += `
            <div class="input-group" style="margin-top: 0.5rem">
                <label>Text Content</label>
                <input type="text" id="prop-text" value="${el.text}">
            </div>
            <div class="input-group" style="margin-top: 0.5rem">
                <label>Font Type</label>
                <select id="prop-fontType">
                    <option value="1" ${el.fontType === '1' ? 'selected' : ''}>Built-in 1</option>
                    <option value="2" ${el.fontType === '2' ? 'selected' : ''}>Built-in 2</option>
                    <option value="3" ${el.fontType === '3' ? 'selected' : ''}>Built-in 3</option>
                    <option value="TSS24.BF2" ${el.fontType === 'TSS24.BF2' ? 'selected' : ''}>Chinese (TSS24.BF2)</option>
                    <option value="KOREAN" ${el.fontType === 'KOREAN' ? 'selected' : ''}>Korean (KOREAN)</option>
                </select>
            </div>
            <div class="input-group" style="margin-top: 0.5rem">
                <label>Multiplier Size (1-10)</label>
                <input type="number" id="prop-fontSize" value="${el.fontSize}" min="1" max="10">
            </div>
        `;
    } else if (el.type === 'barcode') {
        html += `
            <div class="input-group" style="margin-top: 0.5rem">
                <label>Barcode Data</label>
                <input type="text" id="prop-data" value="${el.data}">
            </div>
            <div class="input-group" style="margin-top: 0.5rem">
                <label>Height (mm)</label>
                <input type="number" id="prop-height" value="${el.height}" min="5">
            </div>
            <div class="input-group" style="margin-top: 0.5rem">
                <label>Type</label>
                <select id="prop-type">
                    <option value="128" ${el.barcodeType === '128' ? 'selected' : ''}>Code 128</option>
                    <option value="39" ${el.barcodeType === '39' ? 'selected' : ''}>Code 39</option>
                    <option value="EAN13" ${el.barcodeType === 'EAN13' ? 'selected' : ''}>EAN 13</option>
                </select>
            </div>
        `;
    } else if (el.type === 'box') {
        html += `
            <div class="input-group" style="margin-top: 0.5rem">
                <label>Width (mm)</label>
                <input type="number" id="prop-w" value="${el.w}" min="1">
            </div>
            <div class="input-group" style="margin-top: 0.5rem">
                <label>Height (mm)</label>
                <input type="number" id="prop-h" value="${el.h}" min="1">
            </div>
            <div class="input-group" style="margin-top: 0.5rem">
                <label>Border Thickness (dots)</label>
                <input type="number" id="prop-thick" value="${el.thickness}" min="1">
            </div>
        `;
    } else if (el.type === 'line') {
        html += `
            <div class="input-group" style="margin-top: 0.5rem">
                <label>Length (width mm)</label>
                <input type="number" id="prop-w" value="${el.w}" min="1">
            </div>
            <div class="input-group" style="margin-top: 0.5rem">
                <label>Thickness (height mm)</label>
                <input type="number" id="prop-h" value="${el.h}" min="1">
            </div>
        `;
    } else if (el.type === 'circle') {
        html += `
             <div class="input-group" style="margin-top: 0.5rem">
                <label>Diameter (mm)</label>
                <input type="number" id="prop-dia" value="${el.diameter}" min="1">
            </div>
            <div class="input-group" style="margin-top: 0.5rem">
                <label>Border Thickness (dots)</label>
                <input type="number" id="prop-thick" value="${el.thickness}" min="1">
            </div>
        `;
    }

    html += `<button id="btn-delete" class="btn btn-danger">Delete Element</button>`;

    els.propertiesPanel.innerHTML = html;

    // Attach listeners
    document.getElementById('prop-x').addEventListener('input', (e) => updateElement(el.id, { x: Number(e.target.value) }));
    document.getElementById('prop-y').addEventListener('input', (e) => updateElement(el.id, { y: Number(e.target.value) }));

    if (el.type === 'text') {
        document.getElementById('prop-text').addEventListener('input', (e) => updateElement(el.id, { text: e.target.value }));
        document.getElementById('prop-fontType').addEventListener('change', (e) => updateElement(el.id, { fontType: e.target.value }));
        document.getElementById('prop-fontSize').addEventListener('input', (e) => updateElement(el.id, { fontSize: Number(e.target.value) }));
    } else if (el.type === 'barcode') {
        document.getElementById('prop-data').addEventListener('input', (e) => updateElement(el.id, { data: e.target.value }));
        document.getElementById('prop-height').addEventListener('input', (e) => updateElement(el.id, { height: Number(e.target.value) }));
        document.getElementById('prop-type').addEventListener('change', (e) => updateElement(el.id, { barcodeType: e.target.value }));
    } else if (el.type === 'box') {
        document.getElementById('prop-w').addEventListener('input', (e) => updateElement(el.id, { w: Number(e.target.value) }));
        document.getElementById('prop-h').addEventListener('input', (e) => updateElement(el.id, { h: Number(e.target.value) }));
        document.getElementById('prop-thick').addEventListener('input', (e) => updateElement(el.id, { thickness: Number(e.target.value) }));
    } else if (el.type === 'line') {
        document.getElementById('prop-w').addEventListener('input', (e) => updateElement(el.id, { w: Number(e.target.value) }));
        document.getElementById('prop-h').addEventListener('input', (e) => updateElement(el.id, { h: Number(e.target.value) }));
    } else if (el.type === 'circle') {
        document.getElementById('prop-dia').addEventListener('input', (e) => updateElement(el.id, { diameter: Number(e.target.value) }));
        document.getElementById('prop-thick').addEventListener('input', (e) => updateElement(el.id, { thickness: Number(e.target.value) }));
    }

    document.getElementById('btn-delete').addEventListener('click', () => {
        state.elements = state.elements.filter(e => e.id !== el.id);
        selectElement(null);
        renderCanvas();
    });
}

function generateTSPL() {
    let tspl = `SIZE ${state.labelWidth} mm, ${state.labelHeight} mm\r\n`;
    tspl += `GAP 2 mm, 0 mm\r\n`;
    tspl += `DIRECTION 1\r\n`;
    tspl += `CLS\r\n`;

    // 8 dots per mm is standard for 200dpi printers.
    const DPI_MULTIPLIER = 8;

    state.elements.forEach(el => {
        const xDots = Math.round(el.x * DPI_MULTIPLIER);
        const yDots = Math.round(el.y * DPI_MULTIPLIER);

        if (el.type === 'text') {
            // TEXT x,y,"font",rotation,x-multi,y-multi,"content"
            tspl += `TEXT ${xDots},${yDots},"${el.fontType}",0,${el.fontSize},${el.fontSize},"${el.text}"\r\n`;
        } else if (el.type === 'barcode') {
            // BARCODE x,y,"code type",height,human-readable,rotation,narrow,wide,"content"
            const heightDots = Math.round(el.height * DPI_MULTIPLIER);
            tspl += `BARCODE ${xDots},${yDots},"${el.barcodeType}",${heightDots},1,0,2,4,"${el.data}"\r\n`;
        } else if (el.type === 'box') {
            // BOX x,y,x_end,y_end,line_thickness
            const xEndDots = xDots + Math.round(el.w * DPI_MULTIPLIER);
            const yEndDots = yDots + Math.round(el.h * DPI_MULTIPLIER);
            tspl += `BOX ${xDots},${yDots},${xEndDots},${yEndDots},${el.thickness}\r\n`;
        } else if (el.type === 'line') {
            // BAR x,y,width,height
            const wDots = Math.round(el.w * DPI_MULTIPLIER);
            const hDots = Math.round(el.h * DPI_MULTIPLIER);
            tspl += `BAR ${xDots},${yDots},${wDots},${hDots}\r\n`;
        } else if (el.type === 'circle') {
            // CIRCLE X-coordinate, Y-coordinate, diameter, thickness
            const diaDots = Math.round(el.diameter * DPI_MULTIPLIER);
            tspl += `CIRCLE ${xDots},${yDots},${diaDots},${el.thickness}\r\n`;
        }
    });

    tspl += `PRINT 1,1\r\n`;
    return tspl;
}

// Keep this around if they ever want the modal, but main button is print now.
function showTSPLCode() {
    els.tsplOutput.textContent = generateTSPL();
    els.modal.classList.remove('hidden');
    if (state.printerPort) {
        els.btnPrintCode.classList.remove('hidden');
    }
}

async function connectPrinter() {
    try {
        // Try WebUSB first (Better for USBPRINT devices)
        if ('usb' in navigator) {
            console.log("Attempting WebUSB connection...");
            const device = await navigator.usb.requestDevice({
                filters: [] // Allow all USB devices so user can see it
            });
            await device.open();

            // Select configuration and interface
            if (device.configuration === null) {
                await device.selectConfiguration(1);
            }
            const interfaceNumber = device.configuration.interfaces[0].interfaceNumber;
            await device.claimInterface(interfaceNumber);

            state.printerPort = device;
            state.connectionType = 'usb';

            updateConnectButtonStatus();
            return;
        }
    } catch (e) {
        console.warn("WebUSB failed or was cancelled, falling back to Web Serial:", e);
    }

    // Fallback to Web Serial (COM Ports)
    try {
        if ('serial' in navigator) {
            console.log("Attempting Web Serial connection...");
            const port = await navigator.serial.requestPort();
            await port.open({ baudRate: 9600 });

            state.printerPort = port;
            state.connectionType = 'serial';

            updateConnectButtonStatus();
        } else {
            alert("Neither WebUSB nor Web Serial API is supported in this browser.");
        }
    } catch (err) {
        console.error("Connection failed entirely", err);
        alert("Could not connect to the printer. Please ensure it is plugged in and you select it.");
    }
}

function updateConnectButtonStatus() {
    els.btnConnect.innerHTML = `Connected (${state.connectionType.toUpperCase()})`;
    els.btnConnect.classList.remove('btn-primary');
    els.btnConnect.classList.add('btn-success');
    if (els.btnPrintCode) els.btnPrintCode.classList.remove('hidden');
}

// Print action execution
async function printLabel() {
    if (!state.printerPort) {
        alert("Please explicitly connect the printer first.");
        return;
    }

    try {
        const tspl = generateTSPL();
        const encoder = new TextEncoder();
        const data = encoder.encode(tspl);

        if (state.connectionType === 'usb') {
            // WebUSB Send
            const device = state.printerPort;
            // Find the bulk OUT endpoint
            let endpointNumber = null;
            for (const endpoint of device.configuration.interfaces[0].alternate.endpoints) {
                if (endpoint.direction === 'out' && endpoint.type === 'bulk') {
                    endpointNumber = endpoint.endpointNumber;
                    break;
                }
            }

            if (endpointNumber === null) {
                throw new Error("Could not find OUT bulk endpoint on this USB device.");
            }

            await device.transferOut(endpointNumber, data);

        } else if (state.connectionType === 'serial') {
            // Web Serial Send
            const writer = state.printerPort.writable.getWriter();
            await writer.write(data);
            writer.releaseLock();
        }

    } catch (e) {
        console.error("Print error: ", e);
        alert("Print error: " + e.message + ". Check console for details.");
    }
}

// Calibrate printer functionality
async function calibratePrinter() {
    if (!state.printerPort) {
        alert("Please connect the printer first.");
        return;
    }

    try {
        const encoder = new TextEncoder();
        // Standard TSPL sequence to test feed and detect gaps
        const cmd = "SIZE 40 mm, 30 mm\r\nGAP 2 mm, 0 mm\r\nGAPDETECT\r\nBEEP 2,200\r\n";
        const data = encoder.encode(cmd);

        if (state.connectionType === 'usb') {
            const device = state.printerPort;
            let endpointNumber = null;
            for (const endpoint of device.configuration.interfaces[0].alternate.endpoints) {
                if (endpoint.direction === 'out' && endpoint.type === 'bulk') {
                    endpointNumber = endpoint.endpointNumber;
                    break;
                }
            }
            if (endpointNumber !== null) {
                await device.transferOut(endpointNumber, data);
            }
        } else if (state.connectionType === 'serial') {
            const writer = state.printerPort.writable.getWriter();
            await writer.write(data);
            writer.releaseLock();
        }

        alert("Calibration commanded sent! The printer should roll a few labels and beep.");
    } catch (e) {
        console.error("Calibration error: ", e);
        alert("Calibration error: " + e.message);
    }
}

// Run Init
init();
