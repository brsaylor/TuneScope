.PHONY: build
build:
	python2 setup.py build_ext --inplace

.PHONY: test
test: build
	pytest

.PHONY: test-debug
test-debug: build
	pytest --pdb

.PHONY: package
package: build
	cd packaging && \
	pyinstaller -y --clean --windowed TuneScope.spec && \
	cd dist && \
	hdiutil create ./TuneScope.dmg -srcfolder TuneScope.app -ov

.PHONY: clean
clean:
	python2 setup.py clean
	rm -rf build/
	rm -f tunescope/*.{pyc,so}
	rm -rf tunescope/__pycache__
	rm -rf tests/__pycache__
	rm -rf packaging/build/ packaging/dist/
