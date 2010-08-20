#!/bin/bash
#script for the building of Anguix-installer.
ANGUIX=`pwd`
if [ ! -e Anguix-files.tar.gz ]; then
cd $ANGUIX/Anguix-files
tar czvf Anguix-files.tar.gz ./*
mv Anguix-files.tar.gz $ANGUIX
fi
cd $ANGUIX
cp Anguix-installer_nobinary Anguix-installer
cat Anguix-files.tar.gz >> Anguix-installer
chmod +x Anguix-installer
rm Anguix-files.tar.gz
echo "done."
exit 0
