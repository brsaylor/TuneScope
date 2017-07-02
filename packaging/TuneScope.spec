# -*- mode: python -*-

block_cipher = None


a = Analysis(['../tunescope/main.py'],
             pathex=['.'],
             binaries=[],
             datas=[('../tunescope/*.kv', '.')],
             hiddenimports=['tunescope.audioutil',
                            'tunescope.audiobackend',
                            'pathlib2'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['_tkinter', 'Tkinter', 'enchant', 'twisted'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='TuneScope',
          debug=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='TuneScope')
app = BUNDLE(coll,
             name='TuneScope.app',
             icon=None,
             bundle_identifier=None)