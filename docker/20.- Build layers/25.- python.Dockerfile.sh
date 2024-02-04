#!/bin/bash
set -e


# Upgrade system
PACKAGES=()
PACKAGES+=(d2dcn)


# Install all
pip3 install ${PACKAGES[@]}
