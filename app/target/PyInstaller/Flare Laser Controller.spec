# -*- mode: python -*-

block_cipher = None


a = Analysis(['C:\\Users\\lspmpc\\Documents\\Python Scripts\\flare-laser\\app\\src\\main\\python\\main.py'],
             pathex=['C:\\Users\\lspmpc\\Documents\\Python Scripts\\flare-laser\\app\\target\\PyInstaller'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='Flare Laser Controller',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=False , icon='C:\\Users\\lspmpc\\Documents\\Python Scripts\\flare-laser\\app\\src\\main\\icons\\Icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='Flare Laser Controller')
