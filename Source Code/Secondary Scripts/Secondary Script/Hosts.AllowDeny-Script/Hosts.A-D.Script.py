import json
import paramiko
import time
import os
import sys


# Controlla se il file "SSHKey" esiste nella cartella corrente
if not os.path.exists("SSHKey"):
    print("La chiave 'SSHKey' non esiste nella cartella corrente, generala con l'apposito script!")
    sys.exit()

# Carica i dati dal file JSON
with open("devices.json", "r") as json_file:
    devices = json.load(json_file)

for device in devices:
    user_ssh = device["User"]
    ip_ssh = device["IP"]
    password_ssh = device["Password"]


    # Crea una connessione SSH
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh_client.connect(ip_ssh, username=user_ssh, password=password_ssh)
        time.sleep(1)
        print("USER: ", user_ssh,"/",ip_ssh)
        
        # I comandi per appendere le righe al file hosts.allow
        comando1 = "echo 'sshd: 100.100.2.0/24' | tee -a /etc/hosts.allow"
        #comando2 = "echo 'sshd: 100.101.0.5' | tee -a /etc/hosts.allow"
        comando2 = "echo 'sshd: 100.101.0.0/24' | tee -a /etc/hosts.allow"
        comando3 = "echo 'sshd: ALL' | tee -a /etc/hosts.deny"
        
        
        
        ssh_client.exec_command(comando1)
        ssh_client.exec_command(comando2)
        ssh_client.exec_command(comando3)
        
        print("File degli Host-Permessi/Negati aggiornati!")
      
        print("-----------")
        
    except Exception as e:
        print(f"Errore durante la connessione SSH: {str(e)}")
    finally:
        ssh_client.close()
