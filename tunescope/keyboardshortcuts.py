import platform

keyboard_shortcuts = [
    {
        'description': 'Open File',
        'platform': {
            'macos': {
                'keys': ['meta', 'o'],
            },  
            'linux': {},
            'windows': {},
        },
        'action': 'open_file',
    },
    {
        'description': 'Show Recent Files',
        'platform': {
            'macos': {
                'keys': ['shift', 'meta', 'o'],
            },
            'linux': {},
            'windows': {},
        },
        'action': 'show_recent_files',

    },
    {
        'description': 'Play/Pause',
        'platform': {
            'macos': {
                'keys': [' '],
            },
            'linux': {},
            'windows': {},
        },
        'action': 'play_pause',
    },

]


if platform.system() == 'Darwin':
    _platform = 'macos'
else:
    _platform = 'linux'
_shortcut_map = {}
for shortcut in keyboard_shortcuts:
    keys = shortcut['platform'][_platform]['keys']
    _shortcut_map[tuple(sorted(keys))] = shortcut['action']


def keyboard_action(text, modifiers):
    map_key = tuple(sorted([text] + modifiers))
    return _shortcut_map.get(map_key)
    