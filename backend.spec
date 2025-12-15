# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['start_backend.py'],
    pathex=['.'],  # 현재 디렉토리를 Python 경로에 추가
    binaries=[],
    datas=[
        ('frontend/static', 'frontend/static'),
        ('frontend/templates', 'frontend/templates'),
        ('backend', 'backend'),  # backend 폴더를 데이터로 포함
        ('src', 'src'),  # src 폴더도 포함 (크롤러 코드)
    ],
    hiddenimports=[
        'uvicorn',
        'fastapi',
        'pydantic',
        'watchfiles',
        'aiofiles',
        'starlette',
        'PIL',
        'selenium',
        'webdriver_manager',
        'dotenv',
        'jinja2',
        'requests',
        'multipart',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'backend',
        'backend.main',
        'backend.api',
        'backend.api.routes',
        'backend.models',
        'backend.models.schemas',
        'backend.services',
        'backend.services.crawler_service',
        'backend.services.parallel_crawler_service',
        'backend.services.ai_service',
        'backend.services.history_service',
        'backend.config_manager',
        'backend.utils',
        'backend.utils.path_utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='backend',
)
