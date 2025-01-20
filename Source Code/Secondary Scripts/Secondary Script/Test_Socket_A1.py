import socket

def test_socket(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)  # Imposta un timeout per la connessione
        s.connect((ip, port))
        s.close()
        print("La connessione è riuscita!")
        return True
    except socket.error as e:
        print(f"Errore durante la connessione: {e}")
        return False

ip = '100.100.6.3'  # IP dell'host da testare
port = 22  # Porta su cui provare a connettersi (LA TCP è sicuro aperta, altrimenti non potresti aver configurati le chiavi e gli utenti tester per l'A2)

if test_socket(ip, port):
    print(f"La socket su {ip}:{port} è aperta e funzionante.")
else:
    print(f"La socket su {ip}:{port} non è raggiungibile o non è aperta.")
