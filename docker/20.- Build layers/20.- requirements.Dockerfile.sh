#!/bin/bash

set -e

# Set not iterative
export DEBIAN_FRONTEND=noninteractive


# Configure timezone
ln -snf /usr/share/zoneinfo/${TZ} /etc/localtime
echo ${TZ} > /etc/timezone


# Upgrade system
PACKAGES=()
apt update --fix-missing
apt upgrade -y


# Intall Yocto Proyect basic dependencies and extras

PACKAGES+=(wget)
PACKAGES+=(git)

PACKAGES+=(unzip)

PACKAGES+=(python3)
PACKAGES+=(python3-pip)
PACKAGES+=(xz-utils)

PACKAGES+=(curl)
PACKAGES+=(vim)
PACKAGES+=(tzdata)


PACKAGES+=(mosquitto)


# Set up locales
DEBIAN_FRONTEND=noninteractive
PACKAGES+=(locales)
PACKAGES+=(apt-utils)
PACKAGES+=(sudo)



# Install all
apt install -y ${PACKAGES[@]}


# Reconfigure
dpkg-reconfigure locales
locale-gen ${LANG}
update-locale LC_ALL=${LC_ALL} LANG=${LANG}


# Replace dash with bash
rm /bin/sh
ln -s /bin/bash /bin/sh


# Install repo
curl -o /usr/local/bin/repo https://storage.googleapis.com/git-repo-downloads/repo
chmod a+x /usr/local/bin/repo
