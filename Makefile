me_version = $(shell grep "__appversion__ = " mementoembed/version.py | sed 's/__appversion__ = //g' | sed "s/'//g")

all: native_installer rpm

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
	
clean:
	-docker stop rpmbuild_mementoembed
	-docker rm rpmbuild_mementoembed
	-rm -rf .eggs
	-rm -rf build
	-rm -rf _build
	-rm -rf docs/build
	-rm -rf docs/source/_build
	-rm -rf dist
	-rm -rf .web_cache
	-rm -rf installer
	-rm -rf mementoembed.egg-info
	-rm -rf node_modules
	-rm -rf *.log
	-rm mementoembed.sqlite
	-find . -name '*.pyc' -exec rm {} \;
	-find . -name '__pycache__' -exec rm -rf {} \;
	-rm -rf source-distro
	-rm -rf rpmbuild
	python ./setup.py clean

build:
	python ./setup.py sdist

native_installer:
	./create-linux-installer.sh

rpm: source
	-rm -rf rpmbuild
	mkdir -p rpmbuild/RPMS rpmbuild/SRPMS
	docker build -t rpmbuild:dev -f build-rpm-Dockerfile . --build-arg mementoembed_version=$(me_version) --progress=plain
	docker container run --name rpmbuild_mementoembed --rm -it -v $(CURDIR)/rpmbuild/RPMS:/root/rpmbuild/RPMS -v $(CURDIR)/rpmbuild/SRPMS:/root/rpmbuild/SRPMS rpmbuild:dev
	-docker stop rpmbuild_mementoembed
	-docker rm rpmbuild_mementoembed
	@echo "an RPM structure exists in the rpmbuild directory"

# dpkg:
# 	-rm -rf dpkgbuild
# 	mkdir dpkgbuild
# 	docker build -t dpkgbuild:dev -f build-dpkg-Dockerfile . --build-arg mementoembed_version=$(me_version) --progress=plain
	
	

release: source build native_installer rpm
	-rm -rf release
	-mkdir release
	cp ./installer/install-mementoembed.sh release/install-mementoembed-${me_version}.sh
	cp ./source-distro/MementoEmbed-${me_version}.tar.gz release/
	cp ./rpmbuild/RPMS/x86_64/MementoEmbed-${me_version}-1.el8.x86_64.rpm release/
	cp ./rpmbuild/SRPMS/MementoEmbed-${me_version}-1.el8.src.rpm release/
# TODO: copy RPM...
	
