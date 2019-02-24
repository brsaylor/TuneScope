.PHONY: build
build:
	python2 setup.py build_ext --inplace

.PHONY: test
test: build
	pytest

.PHONY: test-debug
test-debug: build
	pytest --pdb

.PHONY: licenses
licenses:
	pip-licenses --format-json --with-authors --with-urls \
		--ignore-packages TuneScope \
		> tunescope/data/licenses/pip-licenses.json

.PHONY: package
package: build licenses
	cd packaging && \
	pyinstaller -y --clean --windowed TuneScope.spec && \
	cd dist && \
	mkdir -p dmg-root && \
	mv TuneScope.app dmg-root && \
	cp -r ../Licenses dmg-root && \
	create-dmg \
		--volname "TuneScope Installer" \
		--window-size 500 500 \
		--icon-size 100 \
		--icon "TuneScope.app" 200 100 --icon "Licenses" 100 250 \
		--app-drop-link 300 250 \
		TuneScope.dmg dmg-root

.PHONY: clean
clean:
	python2 setup.py clean
	rm -rf build/
	rm -f tunescope/*.{pyc,so}
	rm -rf tunescope/__pycache__
	rm -rf tests/__pycache__
	rm -rf packaging/build/ packaging/dist/
