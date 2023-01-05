#!/bin/bash
# Start attempting to import packages

echo -e "Installing packages..."

for PACKAGE in genericpath time datetime spidev array numpy csv os sys threading numpy openpyxl queue re json socket
do
echo -e "Installing $PACKAGE"
pip3 install $PACKAGE
done

echo -e "\033[1;32mDone.\033[0m"