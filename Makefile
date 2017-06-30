build:
	python setup.py build_ext --inplace

test: build
	pytest

package: build
	cd packaging && \
	pyinstaller -y --clean --windowed TuneScope.spec && \
	cd dist && \
	hdiutil create ./TuneScope.dmg -srcfolder TuneScope.app -ov

clean:
	python setup.py clean
	rm -rf build/
	rm -f tunescope/*.{pyc,so}
	rm -rf tunescope/__pycache__
	rm -rf packaging/build/ packaging/dist/
