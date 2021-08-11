#!/bin/bash

mkdir -p install
rm -rf install/*
wget https://archives.tedm.io/latest_archive && mv latest_archive install/pkg.zip
pushd install
unzip pkg.zip
rm pkg.zip
popd
