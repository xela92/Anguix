#!/bin/bash
PKG_NAME=`cat CONTROL/control |grep Package |sed 's/Package:\ //g'` 
PKG_VERS=`cat CONTROL/control |grep Version |sed 's/Version:\ //g'`
PKG_ARCH=`cat CONTROL/control |grep Architecture |sed 's/Architecture:\ //g'`
tar czvf control.tar.gz ./CONTROL
tar czvf data.tar.gz ./usr
echo "2.0" > debian-binary
ar -crf "$PKG_NAME"_"$PKG_VERS"_"$PKG_ARCH".deb ./debian-binary ./data.tar.gz ./control.tar.gz
rm control.tar.gz
rm data.tar.gz
rm debian-binary
echo "complete."


