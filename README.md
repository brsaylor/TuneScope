# TuneScope

## Build instructions

### macOS

1. Install [Homebrew](http://brew.sh/)
2. Install GStreamer:
    ```
    brew reinstall --build-bottle gstreamer gst-plugins-{base,good,bad,ugly}
    ```
3. Install SDL:
    ```
    brew reinstall --build-bottle sdl2 sdl2_image sdl2_ttf sdl2_mixer
    ```
4. Install current version of Python 2:
    ```
    brew install python2
    ```
5. Create a virtual environment for TuneScope. Recommended method:
    - Install [virtualenvwrapper](http://virtualenvwrapper.readthedocs.io/en/latest/install.html)
	1. `pip2 install virtualenvwrapper`
	2. Add the following lines to ~/.bashrc:
	    ```
	    export VIRTUALENVWRAPPER_PYTHON=/usr/local/bin/python2
	    export WORKON_HOME=$HOME/.virtualenvs
	    export PROJECT_HOME=$HOME/src
	    source /usr/local/bin/virtualenvwrapper.sh
	    ```
	3. `source ~/.bashrc`
    - `mkvirtualenv -a <path-to-TuneScope> -p /usr/local/bin/python2 tunescope`
6. Install Python dependencies:
    ```
    pip install -r requirements.txt	
    ```
7. Download and build Rubber Band Library:
    ```
    cd <path-to-TuneScope>
    pushd .
    mkdir lib
    cd lib
    hg clone https://brsaylor@bitbucket.org/brsaylor/rubberband
    cd rubberband
    hg checkout api-get-buffered-input-duration
    make -f Makefile.osx lib static
    popd
    ```
8. `python setup.py develop`
9. Run the tests
    ```
    make test
    ```
10. Run TuneScope
    ```
    python tunescope/main.py
    ```

Copyright 2017 Benjamin R. Saylor
