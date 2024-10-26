# Installation Guide

This guide provides detailed instructions for installing and setting up ListSync using different methods. Choose the method that best suits your needs and technical expertise.

## Table of Contents

1. [Docker Installation (Recommended)](#docker-installation-recommended)
2. [Standard Python Environment](#standard-python-environment)
3. [Poetry Installation](#poetry-installation)
4. [Configuration](#configuration)

## Docker Installation (Recommended)

Docker ensures ListSync runs consistently across different environments.

### Prerequisites

- Docker installed on your system. If not, follow the [official Docker installation guide](https://docs.docker.com/get-docker/).

### Steps

1. **Create a working directory:**
   Make a folder to house the application's log files (e.g., list-sync)

2. **Pull and Run the Docker Image:**
   Navigate to your directory and use the following command:

   ```sh
   sudo docker pull ghcr.io/woahai321/list-sync:main && sudo docker run -it --rm -v "$(pwd)/data:/usr/src/app/data" -e TERM=xterm-256color ghcr.io/woahai321/list-sync:main
   ```

3. **For subsequent runs:**
   Use this command:

   ```sh
   sudo docker run -it --rm -v "$(pwd)/data:/usr/src/app/data" -e TERM=xterm-256color ghcr.io/woahai321/list-sync:main
   ```

## Standard Python Environment

If you prefer running ListSync in a standard Python environment:

### Prerequisites

- Python 3.9 or higher installed on your system

### Steps

1. **Clone the Repository:**

   ```sh
   git clone https://github.com/woahai321/list-sync.git
   cd list-sync
   ```

2. **Install Dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

3. **Run the Script:**
   ```sh
   python add.py
   ```

## Poetry Installation

Poetry offers advantages in dependency management and environment isolation.

### Prerequisites

- Python 3.9 or higher installed on your system

### Steps

1. **Install Poetry:**

   ```sh
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Clone the Repository:**

   ```sh
   git clone https://github.com/woahai321/list-sync.git
   cd list-sync
   ```

3. **Install Dependencies:**

   ```sh
   poetry install
   ```

4. **Run the Script:**
   ```sh
   poetry run python add.py
   ```

## Configuration

After installation, follow these steps to configure ListSync:

1. Run the script using your chosen installation method.
2. You will be prompted to enter the following information:
   - Overseerr URL: Your Overseerr instance's base URL
   - API Key: The API key from your Overseerr account
   - IMDB List ID(s): The ID(s) of the IMDB list(s) you want to import
   - Trakt List ID(s): The ID(s) of the Trakt list(s) you want to import
3. Enter a password to encrypt your configuration when prompted.
4. Your encrypted configuration will be saved for future use.

For more information on obtaining list IDs, refer to the [Obtaining List IDs](/docs/obtaining-list-ids.md) guide.

If you encounter any issues during installation or configuration, please refer to our [Troubleshooting Guide](/docs/troubleshooting.md).
