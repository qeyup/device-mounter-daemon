#!/bin/bash

# Install apt packages
PACKAGES=()
PACKAGES+=(vim)
PACKAGES+=(bash-completion)
PACKAGES+=(tree)
PACKAGES+=(net-tools)
apt update
apt install -y ${PACKAGES[@]}

# Extract
ExtractFolder fzf.zip fzf
mv fzf /home/.fzf
echo "" | /home/.fzf/install


# Install and configure zsh
#wget https://github.com/ohmyzsh/ohmyzsh/archive/master.zip
#unzip master.zip && rm master.zip
#mv ohmyzsh-master ~/.oh-my-zsh
#cp ~/.oh-my-zsh/templates/zshrc.zsh-template ~/.zshrc
#chsh -s /bin/zsh
#sed -i s/"ZSH_THEME=.*"/"ZSH_THEME=bira"/g ~/.zshrc
