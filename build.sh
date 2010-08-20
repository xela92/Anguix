#!/bin/bash
#script for the building of Anguix-installer.
if [ ! -e Anguix-files.tar.gz ]; then
cd Anguix-files
tar czvf Anguix-files.tar.gz ./*
fi
cp Anguix-installer_nobinary Anguix-installer
cat Anguix-files.tar.gz >> Anguix-installer
echo "done."
exit 0
