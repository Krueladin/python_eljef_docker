clean:
	rm -rf build dist eljef_docker.egg-info eljef/__pycache__ eljef/docker/__pycache__

install:
	python3 setup.py install

lint:
	tools/dolint.sh
