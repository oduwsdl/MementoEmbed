me_version = $(shell grep "__appversion__ = " mementoembed/version.py | sed 's/__appversion__ = //g' | sed "s/'//g")

all: generic_installer rpm

source:
	-rm -rf /tmp/mementoembed-source
	-rm -rf /tmp/MementoEmbed-$(me_version)
	-rm -rf /tmp/MementoEmbed-$(me_version).tar.gz
	mkdir /tmp/mementoembed-source
	pwd
	cp -r . /tmp/mementoembed-source
	-rm -rf /tmp/mementoembed-source/working-dontcommit
	-rm -rf /tmp/mementoembed-source/.vscode
	-rm -rf /tmp/mementoembed-source/.git
	(cd /tmp/mementoembed-source && make clean)
	mv /tmp/mementoembed-source /tmp/MementoEmbed-$(me_version)
	tar -C /tmp --exclude='.DS_Store' -c -v -z -f /tmp/MementoEmbed-$(me_version).tar.gz MementoEmbed-$(me_version)
	-rm -rf source-distro
	mkdir source-distro
	cp /tmp/MementoEmbed-$(me_version).tar.gz source-distro
	
clean: clean-installer
	-docker stop rpmbuild_mementoembed
	-docker rm rpmbuild_mementoembed
	-rm -rf .eggs
	-rm -rf build
	-rm -rf _build
	-rm -rf docs/build
	-rm -rf docs/source/_build
	-rm -rf dist
	-rm -rf .web_cache
	-rm -rf mementoembed.egg-info
	-rm -rf node_modules
	-rm -rf *.log
	-rm mementoembed.sqlite
	-find . -name '*.pyc' -exec rm {} \;
	-find . -name '__pycache__' -exec rm -rf {} \;
	-rm -rf source-distro

clean-installer:
	-rm -rf installer

clean-all: clean
	-rm -rf release

build-sdist: check-virtualenv
	python ./setup.py sdist

generic_installer: check-virtualenv
	./create-linux-installer.sh

rpm: source
	-rm -rf installer/rpmbuild
	mkdir -p installer/rpmbuild/RPMS installer/rpmbuild/SRPMS
	docker build -t mementoembed_rpmbuild:dev -f build-rpm-Dockerfile . --build-arg mementoembed_version=$(me_version) --progress=plain
	docker container run --name rpmbuild_mementoembed --rm -it -v $(CURDIR)/installer/rpmbuild/RPMS:/root/rpmbuild/RPMS -v $(CURDIR)/installer/rpmbuild/SRPMS:/root/rpmbuild/SRPMS mementoembed_rpmbuild:dev
	-docker stop rpmbuild_mementoembed
	-docker rm rpmbuild_mementoembed
	@echo "an RPM structure exists in the installer/rpmbuild directory"

deb: generic_installer
	-rm -rf installer/debbuild
	mkdir -p installer/debbuild
	docker build -t mementoembed_debbuild:dev -f build-deb-Dockerfile . --build-arg mementoembed_version=$(me_version) --progress=plain
	docker container run --name deb_mementoembed --rm -it -v $(CURDIR)/installer/debbuild:/buildapp/debbuild mementoembed_debbuild:dev
	-docker stop deb_mementoembed
	-docker rm deb_mementoembed
	@echo "a DEB exists in the installer/debbuild directory"

release: source build-sdist generic_installer rpm deb
	-rm -rf release
	-mkdir release
	cp ./installer/generic-unix/install-mementoembed.sh release/install-mementoembed-${me_version}.sh
	cp ./source-distro/MementoEmbed-${me_version}.tar.gz release/
	cp ./installer/rpmbuild/RPMS/x86_64/MementoEmbed-${me_version}-1.el8.x86_64.rpm release/
	cp ./installer/rpmbuild/SRPMS/MementoEmbed-${me_version}-1.el8.src.rpm release/	
	cp ./installer/debbuild/MementoEmbed-${me_version}.deb release/

check-virtualenv:
ifndef VIRTUAL_ENV
	$(error VIRTUAL_ENV is undefined, please establish a virtualenv before building)
endif

clean-virtualenv: check-virtualenv
	-pip uninstall -y raintale
	@for p in $(shell pip freeze | awk -F== '{ print $$1 }'); do \
		pip uninstall -y $$p ; \
	done
	@echo "done removing all packages from virtualenv"
