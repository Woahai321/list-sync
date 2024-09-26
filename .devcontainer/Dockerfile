ARG PYTHON_VERSION=3.9
FROM mcr.microsoft.com/devcontainers/python:${PYTHON_VERSION}

USER root

RUN apt-get update -y -qq && \
    apt-get dist-upgrade -y -qq && \
    apt-get autoremove -y -qq

# git safe directories
RUN git config --global --add safe.directory "*"

RUN apt-get -y -qq install \
    fzf \
    jq \
    yq \
    zsh

RUN pip install pipx
RUN pipx --global ensurepath
RUN pipx --global install poetry==1.8.3 ruff pre-commit

USER vscode
