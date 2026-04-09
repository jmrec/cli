# JM's Collection of Scripts
A containerized CLI toolkit built with Python, Typer, and Docker. This setup allows you to run scripts (like document conversion) from any directory without needing to install dependencies like Pandoc or Python locally.

## Prerequisites
- Docker

## Usage

1. Pull the Docker Image
   
   Before running the scripts for the first time (or to update them), pull the latest version of the image:

   ```sh
   docker pull jmrec-cli:latest
   ```

2. Set up the Terminal Alias
   
   To use the scripts command (or another alias) from any folder on your machine, add the following function to your shell configuration file (~/.zshrc for Mac/Zsh or ~/.bashrc for Linux/Bash):

   Example:
   ```sh
    # Replace 'scripts' to any alias of your liking
    scripts() {
        export UID=$UID
        export GID=$(id -g)

        # Replace with the actual absolute path to your project
        docker compose -f /Users/jmrecondo/jmrec-cli/compose.yml run --rm jmrec-cli "$@"
    }
    ```

    After adding, run source ~/.zshrc to activate it.

3. General Commands

    Check the available tools and subcommands:

    ```sh
    # View all command groups (docs, users, etc.)
    scripts --help

    # View specific help for a command group
    scripts docs --help
    ```
