# Minimalistic CS:GO Server Admin Panel

This is a simple Python script that provides a minimalistic admin panel for managing a CS:GO server via SSH. You can compile it into an executable using PyInstaller to easily share it with people you want to grant access to your server management tools.

## Script Functionality

The script offers a command-line interface to perform the following actions on your CS:GO server:
- **Restart the server machine**: Reboots the entire Linux server.
- **Stop the CS:GO server**: Terminates any running CS:GO server instances.
- **Start the CS:GO server**: Launches the CS:GO server in a `screen` session and monitors its startup process.
- **Exit**: Closes the SSH connection and terminates the script.

It uses the `paramiko` library for SSH communication and supports sudo commands for privileged operations.

## Setup Instructions

1. **Prepare the Script:**
   - Open the main script file and update the following variables with your server details:
     - `server["ip"]`: The IP address of your Linux server.
     - `server["username"]`: The Linux username for SSH access.
     - `server["password"]`: The corresponding password for the username.
   - Save the changes.

2. **Deploy Required Files:**
   - Place `start.sh` in the same directory as the `srcds` file (Source Dedicated Server executable) on your server.
   - Place `csgo_launch.sh` in the home directory of the main user (e.g., `/home/username/`).
   - In `start.sh`, update the Steam account details and adjust server startup settings (e.g., map, game mode, etc.) as needed.

3. **Install Dependencies on the Server:**
   - Ensure the `screen` package is installed on your Linux machine. You can install it with:
     ```bash
     sudo apt update && sudo apt install screen  # For Debian/Ubuntu
