Name: MementoEmbed
Version: {{ mementoembed_version }}
Summary: MementoEmbed is service that provides archive-aware embeddable surrogates (social cards, thumbnails, etc.) for archived web pages (mementos).
Release: 1%{?dist}
License: MIT
Source0: %{name}-%{version}.tar.gz
BuildArch: x86_64

BuildRequires: sed, grep, tar
Requires: nodejs, sed, grep, tar, python3-virtualenv, makeself, which, python38, redis

%description
MementoEmbed is a tool to create archive-aware embeddable surrogates for archived web pages (mementos), like the social card above. MementoEmbed is different from other surrogate-generation systems in that it provides access to archive-specific information, such as the original domain of the URI-M, its memento-datetime, and to which collection a memento belongs. MementoEmbed can also create browser thumbnails. In addition, MementoEmbed can create imagereels, animated GIFs of the best five images from the memento.

%define  debug_package %{nil}

%prep
%setup -q

%build
rm -rf $RPM_BUILD_ROOT
make native_installer

%install
echo RPM_BUILD_ROOT is $RPM_BUILD_ROOT
mkdir -p ${RPM_BUILD_ROOT}/opt/mementoembed
bash ./installer/install-mementoembed.sh -- --install-directory ${RPM_BUILD_ROOT}/opt/mementoembed --python-exe /usr/bin/python
find ${RPM_BUILD_ROOT}/opt/mementoembed/mementoembed-virtualenv/bin -type f -exec sed -i "s?${RPM_BUILD_ROOT}??g" {} \;
find ${RPM_BUILD_ROOT}/opt/mementoembed/node_modules -name 'package.json' -exec sed -i "s?${RPM_BUILD_ROOT}??g" {} \;

%clean
rm -rf $RPM_BUILD_ROOT

%files
/opt/mementoembed/
