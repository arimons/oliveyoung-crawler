const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');

let mainWindow;
let backendProcess;

const BACKEND_PORT = 8000;
const URL = `http://localhost:${BACKEND_PORT}`;

// Setup logging
const logPath = path.join(app.getPath('userData'), 'app.log');
function log(message) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}\n`;
    fs.appendFileSync(logPath, logMessage);
    console.log(message);
}

log(`App starting. Log path: ${logPath}`);

function getBackendCommand() {
    if (app.isPackaged) {
        // 패키징된 환경: resources/app 폴더에서 Python 실행
        const resourcesPath = process.resourcesPath;
        const pythonPath = path.join(resourcesPath, 'app', 'venv', 'Scripts', 'python.exe');
        const scriptPath = path.join(resourcesPath, 'app', 'run_server.py');
        
        log(`Packaged mode`);
        log(`Python: ${pythonPath}`);
        log(`Script: ${scriptPath}`);
        log(`Python exists: ${fs.existsSync(pythonPath)}`);
        log(`Script exists: ${fs.existsSync(scriptPath)}`);
        
        return {
            command: pythonPath,
            args: [scriptPath],
            cwd: path.join(resourcesPath, 'app')
        };
    } else {
        // 개발 환경
        log('Dev mode: backend should be running separately');
        return null;
    }
}

function startBackend() {
    const backendCmd = getBackendCommand();
    if (!backendCmd) return;

    const { command, args, cwd } = backendCmd;
    
    // Check if files exist
    if (!fs.existsSync(command)) {
        log(`ERROR: Python not found at ${command}`);
        return;
    }

    log(`Starting backend: ${command} ${args.join(' ')}`);
    log(`CWD: ${cwd}`);

    try {
        backendProcess = spawn(command, args, {
            cwd: cwd,
            stdio: 'pipe',
            env: { ...process.env }
        });

        log(`Backend process spawned with PID: ${backendProcess.pid}`);

        backendProcess.stdout.on('data', (data) => {
            log(`Backend STDOUT: ${data.toString().trim()}`);
        });

        backendProcess.stderr.on('data', (data) => {
            log(`Backend STDERR: ${data.toString().trim()}`);
        });

        backendProcess.on('error', (err) => {
            log(`Failed to start backend: ${err.message}`);
        });
        
        backendProcess.on('exit', (code, signal) => {
            log(`Backend exited with code ${code} and signal ${signal}`);
        });
    } catch (e) {
        log(`Exception spawning backend: ${e.message}`);
    }
}

function checkBackendReady(callback) {
    log(`Checking if backend is ready at ${URL}...`);
    http.get(URL, (res) => {
        log(`Backend response: ${res.statusCode}`);
        if (res.statusCode === 200) {
            callback();
        } else {
            setTimeout(() => checkBackendReady(callback), 1000);
        }
    }).on('error', (err) => {
        setTimeout(() => checkBackendReady(callback), 1000);
    });
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1280,
        height: 900,
        backgroundColor: '#f3f4f6',
        show: false,
        autoHideMenuBar: true,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true
        }
    });

    mainWindow.loadFile('loading.html');
    
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    if (app.isPackaged) {
        startBackend();
        checkBackendReady(() => {
            log('Backend ready! Loading main URL.');
            mainWindow.loadURL(URL);
        });
    } else {
        checkBackendReady(() => {
            mainWindow.loadURL(URL);
        });
    }
    
    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

app.on('ready', createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('quit', () => {
    if (backendProcess) {
        log('Quitting app, killing backend...');
        backendProcess.kill();
    }
});

