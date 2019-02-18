# -*- mode: python -*-

import glob
import os.path
import re
import subprocess
from PyInstaller.depend import bindepend

block_cipher = None
from kivy.tools.packaging.pyinstaller_hooks import get_deps_all, hookspath, runtime_hooks


def find_gst_plugin_path():
    p = subprocess.Popen(
        ['gst-inspect-1.0', 'coreelements'],
        stdout=subprocess.PIPE)
    (stdoutdata, stderrdata) = p.communicate()

    match = re.search(r'\s+(\S+libgstcoreelements\.\S+)', stdoutdata)

    if not match:
        raise Exception('could not find GStreamer plugins')

    return os.path.dirname(match.group(1))


def find_gst_binaries():
    plugin_path = find_gst_plugin_path()

    plugin_filepaths = glob.glob(os.path.join(plugin_path, 'libgst*'))

    lib_filepaths = set()
    for plugin_filepath in plugin_filepaths:
        plugin_deps = bindepend.selectImports(plugin_filepath)
        lib_filepaths.update([path for _, path in plugin_deps])

    plugin_binaries = [(f, 'gst-plugins') for f in plugin_filepaths]
    lib_binaries = [(f, '.') for f in lib_filepaths]

    return plugin_binaries + lib_binaries


a = Analysis(['../tunescope/main.py'],
             pathex=['.'],
             binaries=find_gst_binaries(),
             datas=[
                ('../tunescope/data', 'data'),
                ('../tunescope/*.kv', '.'),
                ('../tunescope/widgets/*.kv', 'widgets'),
             ],
             hiddenimports=['tunescope.audio.audioutil',
                            'tunescope.audio.audiobackend',
                            'tunescope.visualization.pitch_plot',
                            'tunescope.visualization.spectrogram',
                            'pathlib2',
                            'plyer.platforms.macosx.filechooser',
                            ],
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
             bundle_identifier=None,
             info_plist={'NSHighResolutionCapable': 'True'})
