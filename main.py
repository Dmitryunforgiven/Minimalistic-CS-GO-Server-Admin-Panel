import paramiko
from threading import Lock, Event
import sys
import signal
import time
import os

server = {
    "ip": "insert your ip here",
    "username": "insert your username here",
    "password": "insert your password here"
}

class SSHManager:
    def __init__(self):
        self.client = None
        self.lock = Lock()
        self.active = True
        self.stop_event = Event()
        self.channel = None

    def connect(self, host, username, password):
        with self.lock:
            try:
                self.client = paramiko.SSHClient()
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.client.connect(host, username=username, password=password)
                self.active = True
                self.stop_event.clear()
                return True
            except paramiko.AuthenticationException:
                print("Authentication failed")
                return False
            except paramiko.SSHException as e:
                print(f"Failed to connect to the host: {str(e)}")
                return False
            except Exception as e:
                print(f"Unexpected error connecting to the host: {str(e)}")
                return False

    def execute_command(self, command, log_callback=None, use_pty=False, timeout=120):
        if not self.client:
            raise Exception("Not connected to the server")
        
        with self.lock:
            try:
                stdin, stdout, stderr = self.client.exec_command(command, get_pty=use_pty)
                self.channel = stdout.channel
                start_time = time.time()
                
                if log_callback:
                    while self.active and not self.stop_event.is_set():
                        if stdout.channel.exit_status_ready() and not stdout.channel.recv_ready():
                            break
                        
                        if stdout.channel.recv_ready():
                            line = stdout.readline()
                            if not line:
                                break
                            should_stop = log_callback(line.strip())
                            if should_stop:
                                break
                        
                        if time.time() - start_time > timeout:
                            print("Input timeout")
                            break
                        
                        time.sleep(0.1)
                else:
                    stdout.channel.recv_exit_status()
                
                error = stderr.read().decode()
                if error:
                    filtered_error = []
                    for line in error.splitlines():
                        if "Connection to" not in line and "[sudo]" not in line and "password for" not in line:
                            filtered_error.append(line)
                    
                    if filtered_error:
                        print(f"Error: {' '.join(filtered_error)}")
                return True
            except Exception as e:
                print(f"Error: {e}")
                return False
            finally:
                self.channel = None
                self.stop_event.clear()

    def execute_sudo_command(self, command, password):
        """Executes a command with sudo, providing the password"""
        if not self.client:
            raise Exception("Not connected to the server")
        
        with self.lock:
            try:
                full_command = f"echo {password} | sudo -S {command}"
                stdin, stdout, stderr = self.client.exec_command(full_command)
                exit_status = stdout.channel.recv_exit_status()
                
                error = stderr.read().decode()
                if error:
                    filtered_error = []
                    for line in error.splitlines():
                        if "Connection to" not in line and "[sudo]" not in line and "password for" not in line:
                            filtered_error.append(line)
                    
                    if filtered_error:
                        print(f"Error: {' '.join(filtered_error)}")
                
                return exit_status == 0
            except Exception as e:
                print(f"Error executing sudo command: {e}")
                return False

    def stop_execution(self):
        """Stops the current command execution without closing the channel"""
        self.stop_event.set()

    def close(self):
        with self.lock:
            if self.client:
                try:
                    self.active = False
                    self.stop_event.set()
                    self.client.close()
                    print("\nSSH session closed successfully.")
                except Exception as e:
                    print(f"Error closing SSH session: {e}")
                finally:
                    self.client = None
                    self.channel = None

def log_server_start(message):
    print(message)
    if "GC Connection established" in message:
        return True
    return False


CSGO_STOP_COMMAND = "screen -wipe && screen -ls | grep Detached | awk '{print $1}' | xargs -I {} screen -S {} -X quit"
CSGO_START_COMMAND = "bash ~/csgo_launch.sh"

ssh_manager = SSHManager()
interrupt_flag = False

def signal_handler(sig, frame):
    print("\nProgram interrupted (Ctrl+C). Closing SSH session...")
    global interrupt_flag
    interrupt_flag = True
    ssh_manager.stop_execution()
    ssh_manager.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def reconnect_after_reboot():
    print("Waiting for server reboot...")
    while True:
        time.sleep(10)
        print("Attempting to reconnect...")
        if ssh_manager.connect(host=server["ip"], username=server["username"], password=server["password"]):
            print("Server is back online! Connection restored.")
            break
        else:
            print("Server is not yet available. Retrying in 10 seconds...")

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_menu():
    print("\nServer Management Menu:")
    print("1. Restart server (reboot the machine)")
    print("2. Stop CS:GO server")
    print("3. Start CS:GO server")
    print("4. Exit")

def start_csgo_server():
    global interrupt_flag
    interrupt_flag = False
    
    print("Starting CS:GO server...")

    ssh_manager.execute_command(CSGO_STOP_COMMAND)
    print("Previous server instances stopped.")

    ssh_manager.execute_command(CSGO_START_COMMAND)
    print("CS:GO server started in the background.")

    time.sleep(2)
    
    original_handler = signal.getsignal(signal.SIGINT)
    
    def temp_handler(sig, frame):
        print("\nInterrupting log output (server continues running)...")
        global interrupt_flag
        interrupt_flag = True
        ssh_manager.stop_execution()
        signal.signal(signal.SIGINT, original_handler)
    
    signal.signal(signal.SIGINT, temp_handler)
    
    try:
        print("\nServer output (waiting for successful start):")
        print("="*50)
        print("Press Ctrl+C to return to the menu")

        for i in range(30):
            if interrupt_flag:
                break

            ssh_manager.execute_command("screen -ls | grep csgo", log_callback=log_server_start)
            
            if i < 5:
                print(f"Initializing server configuration... ({i+1}/5)")
            elif i < 10:
                print(f"Loading map resources... ({i-4}/5)")
            elif i < 15:
                print(f"Starting game engine... ({i-9}/5)")
            elif i < 20:
                print(f"Connecting to Steam servers... ({i-14}/5)")
            else:
                print("GC Connection established")
                break
                
            time.sleep(1)
            
            if i == 29:
                print("Server started, but failed to connect to the game coordinator.")
                break
        
    except Exception as e:
        print(f"\nError while viewing server output: {e}")
    finally:
        signal.signal(signal.SIGINT, original_handler)
        
        if interrupt_flag:
            print("\nLog output interrupted by user.")
        else:
            print("\nServer started successfully!")
        
        print("Returning to menu...")
        time.sleep(1)
        clear_console()
        print("CS:GO server is running in the background!")
        return

def main():
    global interrupt_flag
    
    try:
        print("Connecting to the server...")
        if not ssh_manager.connect(host=server["ip"], username=server["username"], password=server["password"]):
            print("Failed to connect to the server. Exiting program.")
            return
        
        clear_console()
        print("Successfully connected to the server!")
        
        while True:
            show_menu()
            choice = input("\nEnter a number (1-4): ").strip()
            
            if choice == "1":
                print("Restarting server...")
                if ssh_manager.execute_sudo_command("reboot", server["password"]):
                    print("Command sent. Server is rebooting.")
                    ssh_manager.close()
                    reconnect_after_reboot()
                    clear_console()
                else:
                    print("Error executing reboot command.")
                
            elif choice == "2":
                print("Stopping CS:GO server...")
                ssh_manager.execute_command(CSGO_STOP_COMMAND)
                print("CS:GO server stopped.")
                
            elif choice == "3":
                start_csgo_server()
                interrupt_flag = False
                
            elif choice == "4":
                print("Exiting program...")
                break
                
            else:
                print("Invalid choice, please try again.")
                
    except Exception as e:
        print(f"\nError: {e}")
        
    finally:
        ssh_manager.close()

if __name__ == "__main__":
    main()