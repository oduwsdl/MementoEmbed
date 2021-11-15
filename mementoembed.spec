Name: MementoEmbed
Version: {{ mementoembed_version }}
Summary: MementoEmbed is service that provides archive-aware embeddable surrogates (social cards, thumbnails, etc.) for archived web pages (mementos).
Release: 1%{?dist}
License: MIT
Source0: %{name}-%{version}.tar.gz
ExclusiveArch: x86_64

BuildRequires: sed, grep, tar, makeself, python3-virtualenv, python38
Requires: nodejs, sed, grep, tar, which, redis, python38, cairo, libjpeg-turbo, zlib, libtiff, freetype-devel, freetype, lcms2, libwebp, tcl, tk, openjpeg2, fribidi, harfbuzz, libxcb, nss, atk, at-spi2-atk, cups-libs, libdrm-devel, libxkbcommon-devel, libXcomposite, libXdamage, libXrandr-devel, mesa-libgbm, pango, alsa-lib, libxshmfence
# Requires: nodejs, sed, grep, tar, python3-virtualenv, makeself, which, python38, redis, libX11, libXcomposite, libXdamage, libXext, libXfixes, libXrandr, alsa-lib, atk, at-spi2-atk, at-spi2-core, cairo, cups-libs, libdrm, mesa-libgbm, libgfortran, libjpeg-turbo, libjpeg-turbo-devel, libjpeg-turbo-utils, libffi, libffi-devel, xz-devel, nspr, nspr-devel, nss, nss-devel, nss-util, nss-util-devel, pango, pango-devel, libpng16, libquadmath, libquadmath-devel, libxcb, libxcb-devel, libxshmfence, libxshmfence-devel, zlib, zlib-devel
# Provides: libffi-9c61262e.so.8.1.0(LIBFFI_BASE_8.0)(64bit), libffi-9c61262e.so.8.1.0(LIBFFI_CLOSURE_8.0)(64bit), libgfortran-040039e1.so.5.0.0(GFORTRAN_8)(64bit), libgfortran-2e0d59d6.so.5.0.0(GFORTRAN_8)(64bit), libjpeg-183418da.so.9.4.0(LIBJPEG_9.0)(64bit), liblzma-d540a118.so.5.2.5(XZ_5.0)(64bit), libpng16, libpng16-213e245f.so.16.37.0(PNG16_0)(64bit), libquadmath-2d0c479f.so.0.0.0(QUADMATH_1.0)(64bit), libquadmath-96973f99.so.0.0.0(QUADMATH_1.0)(64bit), libz-dd453c56.so.1.2.11(ZLIB_1.2.3.4)(64bit), libz-dd453c56.so.1.2.11(ZLIB_1.2.9)(64bit)
AutoReq: no

%description
MementoEmbed is a tool to create archive-aware embeddable surrogates for archived web pages (mementos), like the social card above. MementoEmbed is different from other surrogate-generation systems in that it provides access to archive-specific information, such as the original domain of the URI-M, its memento-datetime, and to which collection a memento belongs. MementoEmbed can also create browser thumbnails. In addition, MementoEmbed can create imagereels, animated GIFs of the best five images from the memento.

%define  debug_package %{nil}
%define _build_id_links none
%global _enable_debug_package 0
%global _enable_debug_package ${nil}
%global __os_install_post /usr/lib/rpm/brp-compress %{nil}

%prep
%setup -q

%build
rm -rf $RPM_BUILD_ROOT
export VIRTUAL_ENV=system
make generic_installer

# thanks -- https://fedoraproject.org/wiki/Packaging%3aUsersAndGroups
%pre
getent group dsa >/dev/null || groupadd -r dsa
getent passwd mementoembed >/dev/null || \
    useradd -r -g dsa -d /opt/raintale -s /sbin/nologin \
    -c "MementoEmbed service account" mementoembed
exit 0

%install
echo RPM_BUILD_ROOT is $RPM_BUILD_ROOT
mkdir -p ${RPM_BUILD_ROOT}/opt/mementoembed
mkdir -p ${RPM_BUILD_ROOT}/etc/systemd/system
bash ./installer/generic-unix/install-mementoembed.sh -- --install-directory ${RPM_BUILD_ROOT}/opt/mementoembed --python-exe /usr/bin/python --mementoembed-user mementoembed
# TODO: fix this, everything should stay in RPM_BUILD_ROOT
mv /etc/mementoembed.cfg ${RPM_BUILD_ROOT}/etc/mementoembed.cfg
mv /etc/systemd/system/mementoembed.service ${RPM_BUILD_ROOT}/etc/systemd/system/mementoembed.service
find ${RPM_BUILD_ROOT}/opt/mementoembed/mementoembed-virtualenv/bin -type f -exec sed -i "s?${RPM_BUILD_ROOT}??g" {} \;
find ${RPM_BUILD_ROOT}/opt/mementoembed/node_modules -name 'package.json' -exec sed -i "s?${RPM_BUILD_ROOT}??g" {} \;
sed -i "s?${RPM_BUILD_ROOT}??g" ${RPM_BUILD_ROOT}/etc/mementoembed.cfg
sed -i "s?${RPM_BUILD_ROOT}??g" ${RPM_BUILD_ROOT}/etc/systemd/system/mementoembed.service
sed -i "s?/opt/mementoembed/mementoembed-virtualenv/lib/python3.9/?/opt/mementoembed/mementoembed-virtualenv/lib/python3.8/?g" ${RPM_BUILD_ROOT}/etc/mementoembed.cfg

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-, mementoembed, dsa, 0755)
/opt/mementoembed/
%attr(0755, root, root) /etc/systemd/system/mementoembed.service
%attr(0644, mementoembed, dsa) %config(noreplace) /etc/mementoembed.cfg

%post
/usr/bin/systemctl enable mementoembed.service
# TODO: for some reason the service does not always do this at runtime on CentOS
mkdir -m0755 -p /opt/mementoembed/var/run/thumbnails
mkdir -m0755 -p /opt/mementoembed/var/run/imagereels
mkdir -m0755 -p /opt/mementoembed/var/run/docreels
chown -R mementoembed:dsa /opt/mementoembed/var/run/

%preun
/usr/bin/systemctl stop mementoembed.service
/usr/bin/systemctl disable mementoembed.service

%postun
/usr/sbin/userdel mementoembed
if [ -d /opt/mementoembed/var ]; then
    backup_file="var-backup-`date '+%Y%m%d%H%M%S'`.tar.gz"
    tar -C /opt/mementoembed -c -v -z -f ${backup_file} var
    rm -rf /opt/mementoembed/var
    echo "created ${backup_file} in /opt/mementoembed"
fi
