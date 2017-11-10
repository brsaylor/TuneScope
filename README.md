# TuneScope

TuneScope is audio player for learning music by ear. It allows you to slow down
an audio file without changing its pitch, so you can follow along more easily on
your instrument. You can also transpose it to a different key, adjust the
tuning, and loop selections.

## Build instructions

### macOS

1. Clone the TuneScope repository:
    ```
    git clone https://github.com/brsaylor/TuneScope.git
    ```
1. Install [Homebrew](http://brew.sh/)
1. Install GStreamer (this can take a long time):
    ```
    brew reinstall --build-bottle --with-libvorbis gstreamer gst-plugins-{base,good,bad,ugly}
    ```
1. Install SDL:
    ```
    brew reinstall --build-bottle sdl2 sdl2_image sdl2_ttf sdl2_mixer
    ```
1. Install current version of Python 2:
    ```
    brew install python2
    ```
1. Create a virtual environment for TuneScope. Recommended method:
    1. Install [virtualenvwrapper](http://virtualenvwrapper.readthedocs.io/):
        1. `pip2 install virtualenvwrapper`
        2. Edit (or create) the file ~/.bashrc, adding the following lines:
            ```
            export VIRTUALENVWRAPPER_PYTHON=/usr/local/bin/python2
            export WORKON_HOME=$HOME/.virtualenvs
            export PROJECT_HOME=$HOME/src
            source /usr/local/bin/virtualenvwrapper.sh
            ```
        3. `source ~/.bashrc`
    2. `cd` _path-to-TuneScope_
    3. `mkvirtualenv -a . -p /usr/local/bin/python2 tunescope`
1. Install Python dependencies:
    ```
    pip install Cython==0.25.2
    pip install numpy==1.12.1
    pip install -r requirements.txt	
    ```
1. Download and build Rubber Band Library:
    ```
    pushd .
    mkdir lib
    cd lib
    hg clone https://brsaylor@bitbucket.org/brsaylor/rubberband
    cd rubberband
    hg checkout api-get-buffered-input-duration
    make -f Makefile.osx lib static
    popd
    ```
1. `python setup.py develop`
1. Run the tests
    ```
    make test
    ```
1. Run TuneScope
    ```
    python tunescope/main.py
    ```

Copyright 2017 Benjamin R. Saylor
