#!/bin/bash

# Install requied
sudo apt install software-properties-common apt-transport-https wget -y


# Add vcode repo
wget -q https://packages.microsoft.com/keys/microsoft.asc -O- | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://packages.microsoft.com/repos/vscode stable main"


# Install vcode
sudo apt install code -y


export HOME_FOLDER="/home/docker"


# Install vcode tools
su docker -c "mkdir -p ${HOME_FOLDER}/.vscode"
su docker -c "code --install-extension auchenberg.vscode-open-file-folder"
su docker -c "code --install-extension cschlosser.doxdocgen"
su docker -c "code --install-extension DeepakPahawa.flowbookmark"
su docker -c "code --install-extension donjayamanne.githistory"
su docker -c "code --install-extension emilast.LogFileHighlighter"
su docker -c "code --install-extension everettjf.filter-line"
su docker -c "code --install-extension ezforo.copy-relative-path-and-line-numbers"
su docker -c "code --install-extension hediet.vscode-drawio"
su docker -c "code --install-extension mhutchie.git-graph"
su docker -c "code --install-extension ms-vscode.cpptools"
su docker -c "code --install-extension ryu1kn.text-marker"
su docker -c "code --install-extension sandcastle.vscode-open"
su docker -c "code --install-extension twxs.cmake"
su docker -c "code --install-extension zachflower.uncrustify"
su docker -c "code --install-extension eamodio.gitlens"
su docker -c "code --install-extension ms-python.python"
su docker -c "code --install-extension spadin.memento-inputs"


# Condigure user settings
cat << 'EOF' > ${HOME_FOLDER}/.config/Code/User/settings.json
{
    "extensions.ignoreRecommendations": true,
    "terminal.integrated.enableMultiLinePasteWarning": false,
    "editor.renderWhitespace": "boundary",
    "hediet.vscode-drawio.theme": "Kennedy"
}
EOF
chown docker ${HOME_FOLDER}/.config/Code/User/settings.json
