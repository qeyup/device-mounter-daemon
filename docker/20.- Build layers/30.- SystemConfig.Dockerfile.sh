#!/bin/bash
set -e

# Add yocto user
useradd --create-home --shell "/bin/bash" docker
passwd -d docker
echo "docker ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
