import subprocess
import shlex
import json
import threading
import socket as soc

class Shell:
    def __init__(self, shell_type: str = "bash"):
        self.shell = subprocess.Popen(shlex.split(shell_type), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    def set_command(self, command):
        return self.shell.communicate(command)#shlex.split(command))

class Connect:
    def __init__(self, port: int, host: str, request_size: int, end_string: str, socket: soc.socket = soc.socket(soc.AF_INET, soc.SOCK_STREAM)):
        self.socket = socket
        self.socket.bind((host, port))
        self.socket.listen(1)
        self.accept_socket, _ = self.socket.accept()
        self.request_size = request_size
        self.end_string = end_string

    def close(self):
        self.accept_socket.close()
        self.socket.close()

    def read(self):
        resalt = ""
        while True:
            text = self.accept_socket.recv(self.request_size).decode("utf-8")
            resalt += text
            if self.end_string in resalt:
                break
        resalt = resalt[:-len(self.end_string)]
        print(resalt)
        return json.loads(resalt)

    def write(self, text: str | bytes | bytearray):
        if isinstance(text, str):
            text = text.encode("utf-8")
        self.accept_socket.sendall(text)

class Main(Connect):
    def __init__(self, port: int, host: str, request_size: int, end_string: str, password: str, socket: soc.socket = soc.socket(soc.AF_INET, soc.SOCK_STREAM), shell_type: str = "bash"):
        super().__init__(port, host, request_size, end_string, socket)
        self.password = password
        self.list_of_shell = [Shell(shell_type)]

    def exec_and_write(self, shell, command):
        stdout, stderr = shell.set_command(command)
        self.write(json.dumps({"stdout": stdout, "stderr": stderr}).encode("utf-8"))

    def read_data(self):
        while True:
            data = self.read()
            if data["password"] != self.password:
                self.write(json.dumps({"stdout": "", "stderr": "Wrong password"}).encode("utf-8"))
                continue

            match data["target"]:
                case "command":
                    print(data["id"], len(self.list_of_shell))
                    if data["id"] > len(self.list_of_shell):
                        for _ in range(data["id"] - len(self.list_of_shell)):
                            self.list_of_shell.append(Shell(shell_type))
                    threading.Thread(target=self.exec_and_write, args=(self.list_of_shell[data["id"]], data["data"])).start()

                case "close":
                    self.close()
                    break
                case _:
                    self.write(json.dumps({"stdout": "", "stderr": "No target transparent"}).encode("utf-8"))

if __name__ == "__main__":
    import hashlib
    import getpass

    host = "127.0.0.1"
    default_port = 5462
    request_size = 1024
    end_string = "<END>"
    shell_type = "S:/msys64/msys2_shell.cmd -defterm -no-start -msys2"

    def is_port_open(host, port):
        try:
            s = soc.socket(soc.AF_INET, soc.SOCK_STREAM)
            s.bind((host, port))
            s.close()
            return True
        except OSError:
            return False

    sock = soc.socket(soc.AF_INET, soc.SOCK_STREAM)

    while True:
        input_port = input(f"Enter port (default = {default_port}): ").strip()
        if not input_port:
            input_port = default_port
        if not is_port_open(host, input_port):
            print("This port is in use. Please enter another one.")
            continue
        break

    try:
        file = open("settings", "r", encoding="utf-8")
        settings = json.load(file)
        host = settings["host"]
        default_port = settings["default_port"]
        request_size = settings["request_size"]
        end_string = settings["end_string"]
        shell_type = settings["shell_type"]
        file.close()

    except FileNotFoundError:
        file = open("settings", "w", encoding="utf-8")
        while True:
            print(1)
            print("Please use a strong password, as knowing it grants full remote access to the console. However, the choice of password is up to you, and we are not responsible if it is guessed.")
            password = getpass.getpass("Enter password: ").strip()
            print(2)
            if input("You are confident [y/N]: ").lower() == "y":
                print("You can change password by python termux-bridge.py --change-password [new password]")
                break
            print(3)
        settings = {"password": hashlib.sha256(password.encode("utf-8")).hexdigest(), "host": host, "default_port": default_port, "request_size": request_size, "end_string": end_string, "shell_type": shell_type,
                   "description": "We do not recommend changing any values here other than shell_type"}
        print(4)
        file.write(json.dumps(settings))
        file.close()


    print(5)
    main_class = Main(input_port, host, request_size, end_string, settings["password"], sock, shell_type)
    print(6)
    main_class.read_data()
