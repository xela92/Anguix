#!/bin/bash
#this is free software; it is licensed under the GNU GPLv2 license;
#Author: xela92 <xela92@linuxzogno.org>
PKG_NAME=`cat DEB/DEBIAN/control |grep Package |sed 's/Package:\ //g'` 
PKG_VERS=`cat DEB/DEBIAN/control |grep Version |sed 's/Version:\ //g'`
PKG_ARCH=`cat DEB/DEBIAN/control |grep Architecture |sed 's/Architecture:\ //g'`
case $1 in
	--manual)
	cd DEB
	tar czvf control.tar.gz ./DEBIAN
	tar czvf data.tar.gz ./usr
	echo "2.0" > debian-binary
	ar -crf "$PKG_NAME"_"$PKG_VERS"_"$PKG_ARCH".deb ./debian-binary ./data.tar.gz ./control.tar.gz
	rm control.tar.gz
	rm data.tar.gz
	rm debian-binary
	mv "$PKG_NAME"_"$PKG_VERS"_"$PKG_ARCH".deb ..
	echo "complete."
	;;
        --help) echo "usage: ./build.sh {parameters: --manual}"
        ;;

	*) dpkg -b DEB "$PKG_NAME"_"$PKG_VERS"_"$PKG_ARCH".deb
	;;
esac


