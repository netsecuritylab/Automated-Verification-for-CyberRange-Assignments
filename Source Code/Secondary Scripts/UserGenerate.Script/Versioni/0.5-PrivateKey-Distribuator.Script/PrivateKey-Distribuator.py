import paramiko
import json
import sys
import os


# Funzione per eseguire comandi SSH
def execute_command_ssh(hostname, hostusername, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Nome del file da copiare
    file_da_copiare = 'SSHKey'
    
    # Percorso della destinazione remota
    percorso_destinazione_remota = '/home/tester/.ssh/'

    try:
        
        #client.connect(hostname= hostname, username= hostusername, key_filename = 'SSHKey')
        client.connect(hostname=hostname, username=username, password=password)
        
        
        # Apre un canale SFTP sulla connessione SSH
        sftp = client.open_sftp()
        
        # Copia il file sulla destinazione remota
        sftp.put(file_da_copiare, percorso_destinazione_remota + file_da_copiare)
        
        
        # Imposta i permessi del file copiato
        # 0o600 = permessi solo per l'utente proprietario
        permessi = 0o600
        sftp.chmod(percorso_destinazione_remota + file_da_copiare, permessi)
        
        
        # Chiudi il canale SFTP e la connessione SSH
        sftp.close()
        
            
        
    except paramiko.AuthenticationException as auth_error:
        print(f"Authentication failed for {hostname}: {auth_error}")
    except paramiko.SSHException as ssh_error:
        print(f"SSH connection failed for {hostname}: {ssh_error}")
    finally:
        client.close()
    
    print(hostname, "-->FATTO!\n")




# Controlla se il file "SSHKey" esiste nella cartella corrente
if not os.path.exists("SSHKey"):
    print("La chiave 'SSHKey' non esiste nella cartella corrente, generala con l'apposito script!")
    sys.exit()

# Caricamento dei dati dal file JSON
with open('devices.json') as json_file:
    data = json.load(json_file)


#Leggiamo i vari blocchi di dati dei device a cui dare la chiave.
for entry in data:
    hostname = (entry['IP'])
    username = (entry['User'])
    password = (entry['Password'])
    execute_command_ssh(hostname, username, password)
 


