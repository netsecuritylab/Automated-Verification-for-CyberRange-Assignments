import paramiko
import json
import time
import sys
import os
import subprocess


public_key_file = 'SSHKey.pub'



# Funzione per eseguire comandi SSH
def execute_command_ssh(hostname, username, password, command,sshcopykey_command, owner_command1, owner_command2, authorized_key_command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        
        client.connect(hostname=hostname, username=username, key_filename='SSHKey')
        #Comando se non generi le chiavi per tutti: client.connect(hostname=hostname, username=username, password=password)
        
        #*)SE SIAMO USER:
            #-->Lanciamo il comando di creazione dell'utente e della sua cartella .SSH (come root)
        stdin, stdout, stderr = client.exec_command(command)
        print(f"stdout: {stdout.read().decode()}")
        print(f"stderr: {stderr.read().decode()}")
        time.sleep(1)

       
           #-->Settiamo l'owner di .ssh come "user".
        client.exec_command(owner_command1)
       
        
            #-->Ci creiamo il file "authorized_keys"
        stdin, stdout, stderr = client.exec_command(authorized_key_command)
        print(f"stdout: {stdout.read().decode()}")
        print(f"stderr: {stderr.read().decode()}")
       
            #-->Settiamo come "owner" di "authorized_keys" user.
        client.exec_command(owner_command2)
        
            #-->Ci copiamo il contenuto della chiave pubblica dentro "authorized_keys" (come user)
        client.exec_command(sshcopykey_command)
        
        #*)ALTRIMENTI SE NON SIAMO USER, procediamo come root direttamente e normalmente con altri comandi
        
        if(username == "user"):
            #-->Finite le nostre operazioni settiamo le cartelle e file creati come "owner" dell'utente nuovo.
            owner_command1= 'echo "Passw0rd.1" | sudo -S chown tester:tester /home/tester/.ssh'
            owner_command2= 'echo "Passw0rd.1" | sudo -S chown tester:tester /home/tester/.ssh/authorized_keys'
            
            client.exec_command(owner_command1)
            client.exec_command(owner_command2)
        
        #Impostiamo la chiave anche per gli utenti root
        try:
            # Leggi il contenuto della chiave pubblica
            with open("SSHKey.pub", "r") as key_file:
                public_key = key_file.read()
                client.exec_command("mkdir .ssh")
                client.exec_command("touch .ssh/authorized_keys")
                sshcopykey_command = f'echo "{public_key}" >> .ssh/authorized_keys'
                client.exec_command(sshcopykey_command)
               

        except Exception as e:
                print(f"Errore durante la lettura del file dei device a cui distribuire la chiave pubblica SSH: {str(e)}")
        
        """
        #Non serve, ai fini pratici, di dare la SSHKey agli utenti non-root sullo user Tester(?)
        if(username != "user"):   
            # Percorso della destinazione remota per la copia della SSHKey per ogni utente tester
            percorso_destinazione_remota = '/home/tester/.ssh/'
            
            # Nome del file da copiare
            file_da_copiare = 'SSHKey'
            
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
        """
        # Percorso della destinazione remota per la copia della SSHKey per ogni utente tester
        percorso_destinazione_remota = '/home/tester/.ssh/'
        
        # Nome del file da copiare
        file_da_copiare = 'SSHKey'
        
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
        
        print(hostname, "-->enviroment di testing creato!")
        
    except paramiko.AuthenticationException as auth_error:
        print(f"Authentication failed for {hostname}: {auth_error}")
    except paramiko.SSHException as ssh_error:
        print(f"SSH connection failed for {hostname}: {ssh_error}")
    finally:
        client.close()
    
    




# Controlla se il file "SSHKey" esiste nella cartella corrente
if not os.path.exists("SSHKey"):
    print("Il file 'SSHKey' non esiste nella cartella corrente. Uscita.")
    sys.exit()

# Controlla se il file "SSHKey.pub" esiste nella cartella corrente
if not os.path.exists("SSHKey.pub"):
    print("Il file 'SSHKey' non esiste nella cartella corrente. Uscita.")
    sys.exit()


# Caricamento dei dati dal file JSON
with open('devices.json') as json_file:
    data = json.load(json_file)


try:
    # Leggi il contenuto della chiave pubblica
    with open("SSHKey.pub", "r") as key_file:
        public_key = key_file.read()

except Exception as e:
        print(f"Errore durante la lettura del file dei device a cui distribuire la chiave pubblica SSH: {str(e)}")


#Leggiamo i vari blocchi di dati dei device a cui dare la chiave.
for entry in data:
    hostname = (entry['IP'])
    username = (entry['User'])
    password = (entry['Password'])
    
    if(username == "user"):
        #Facciamo tutte le nostre operazioni (creazione tester etc.) come user, l'utente di default presente sulla macchina
        command = "echo 'Passw0rd.1' | sudo -S useradd -m -p $(echo 'Passw0rd.1' | openssl passwd -1 -stdin) tester && sudo -S mkdir -p /home/tester/.ssh && sudo -S touch /home/tester/.ssh/authorized_keys"
        authorized_key_command = "echo 'Passw0rd.1' | sudo -S touch /home/tester/.ssh/authorized_keys"
        owner_command1= 'echo "Passw0rd.1" | sudo -S chown user:user /home/tester/.ssh'
        owner_command2= 'echo "Passw0rd.1" | sudo -S chown user:user /home/tester/.ssh/authorized_keys'
        sshcopykey_command = f'echo "Passw0rd.1" | sudo -S echo "{public_key}" >> /home/tester/.ssh/authorized_keys'
        
        #Ci servirà per dopo quando eseguiremo la copia della chiave privata sugli host.
        username="tester"
    else:
        #Facciamo tutte le nostre operazioni (creazione tester etc.) come root, l'utente di default presente sulla macchina
        command = "useradd -m -p $(echo 'Passw0rd.1' | openssl passwd -1 -stdin) tester && mkdir -p /home/tester/.ssh && touch /home/tester/.ssh/authorized_keys"
        authorized_key_command = "touch /home/tester/.ssh/authorized_keys"
        owner_command1= 'chown tester:tester /home/tester/.ssh'
        owner_command2= 'chown tester:tester /home/tester/.ssh/authorized_keys'
        sshcopykey_command = f'echo "{public_key}" >> /home/tester/.ssh/authorized_keys'
    
    execute_command_ssh(hostname, username, password, command, sshcopykey_command, owner_command1, owner_command2, authorized_key_command)
    
    """
    # Costruisci il comando scp e diamo la chiave ad ogni utente tester
    comando_scp = f"scp -i SSHKey SSHKey {username}@{hostname}:/home/tester/.ssh"
    
    # Esegui il comando
    try:
        subprocess.run(comando_scp, shell=True, check=True, timeout=3)
        print("Trasferimento chiave completato con successo.\n")
    except subprocess.CalledProcessError as e:
        print(f"Errore durante il trasferimento: {e}\n")
    """



#Eliminazione utenti
"""
for entry in data:
    hostname = (entry['IP'])
    username = (entry['User'])
    password = (entry['Password'])
    
    if(username == "user"):
        command = "echo 'Passw0rd.1' | sudo -S userdel -r tester"
    else:
        command = "userdel -r tester"
    
    execute_command_ssh(hostname, username, command, 1,2,3,4)  
   
""" 

