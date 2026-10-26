import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2.0)
try:
    s.connect(('192.168.2.28', 8020))
    print("ONLINE")
    s.close()
except Exception as e:
    print("OFFLINE:", e)
