import json
import paramiko
import os
import shutil
import sys


def generate_ssh_key_pair(private_key_filename, public_key_filename):
    
    if os.path.isfile(private_key_filename) or os.path.isfile(public_key_filename):
        print(f"La coppia '{private_key_filename}' e '{public_key_filename}' esiste già.")
        return
    
    # Genera una chiave SSH senza password
    key = paramiko.RSAKey.generate(2048)

    # Salva la chiave privata su disco
    key.write_private_key_file(private_key_filename)

    # Salva la chiave pubblica su disco
    with open(public_key_filename, 'w') as public_key_file:
        public_key_file.write(f"{key.get_name()} {key.get_base64()}")

    print("Coppia di chiavi SSH generata con successo:")
    print(f"Chiave privata: {private_key_filename}")
    print(f"Chiave pubblica: {public_key_filename}")



#Funzione per dare a tutti gli HOST (meno GreenBone? e IFW le chiavi)
def publish_key():
    public_key_file = 'SSHKey.pub'
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
            #ssh_client.exec_command('useradd -m Tester && echo "Tester:Passw0rd.1" | chpasswd')
            
            # Leggi il contenuto della chiave pubblica
            with open(public_key_file, 'r') as key_file:
                public_key = key_file.read()
            
            
            # Aggiungi la chiave pubblica all'elenco delle chiavi autorizzate su utente già user
            ssh_client.exec_command('mkdir ~/.ssh')
            ssh_client.exec_command(f'echo "{public_key}" >> ~/.ssh/authorized_keys')
            
            print(f"{ip_ssh}/{user_ssh}: Chiave pubblica aggiunta alle chiavi autorizzate con successo!")
        except Exception as e:
            print(f"Errore durante la connessione SSH: {str(e)}")
        finally:
            ssh_client.close()



def copy_KeysDir():
    # Ottieni il percorso completo della chiave privata e pubblica prima di cambiare la directory
    current_directory = os.getcwd()
    private_key_path = os.path.join(current_directory, private_key_filename)
    public_key_path = os.path.join(current_directory, public_key_filename)
    
    # Crea la coppia di chiavi SSH
    #generate_ssh_key_pair(private_key_path, public_key_path)
    
    # Salta una cartella rispetto a quella corrente
    os.chdir('..')
    
    # Cartelle in cui copiare i file
    folders_first_level = ['Hosts.AllowDeny-Script', 'UserGenerate.Script', 'Hosts.AllowDeny-Script']
    folders_second_level = ['Verificator_A1', 'Verificator_A2']
    
    # Copia solo i file nelle cartelle del primo livello
    for folder in folders_first_level:
        shutil.copy2(private_key_path, os.path.join(folder, private_key_filename))
        shutil.copy2(public_key_path, os.path.join(folder, public_key_filename))
    
    # Salta una cartella rispetto a quella corrente
    os.chdir('..')
    
    # Copia solo i file nelle cartelle del secondo livello
    for folder in folders_second_level:
        shutil.copy2(private_key_path, os.path.join(folder, private_key_filename))
        shutil.copy2(public_key_path, os.path.join(folder, public_key_filename))




# Nomi dei file per la chiave privata e pubblica
private_key_filename = 'SSHKey'
public_key_filename = 'SSHKey.pub'


# Leggi gli argomenti dalla riga di comando
if len(sys.argv) >= 2:
        command = sys.argv[1].lower()
        
        if command == "generate":
            # Crea la coppia di chiavi SSH
            generate_ssh_key_pair(private_key_filename, public_key_filename)
            
            #le distribuiamo alle directory di lavoro
            copy_KeysDir()
            

        elif command == "pubblish":
            publish_key()
        
        elif command == "all":
            # Crea la coppia di chiavi SSH
            generate_ssh_key_pair(private_key_filename, public_key_filename)
            
            #le distribuiamo alle directory di lavoro
            copy_KeysDir()
            
            publish_key()
        
        else:
            print("Sintassi: 'python Generator_SSH.py <generate/pubblish/all>")

else:
    scelta=input("Vuoi generare una coppia di chiavi, distribuirla sull'ACME...o fare ambe le operazioni? (generate, pubblish, ALL) \n")
    
    command = scelta.lower()
    if command == "generate":
        # Crea la coppia di chiavi SSH
        generate_ssh_key_pair(private_key_filename, public_key_filename)
        
        #le distribuiamo alle directory di lavoro
        copy_KeysDir()
        

    elif command == "pubblish":
        publish_key()
    
    elif command == "all":
        # Crea la coppia di chiavi SSH
        generate_ssh_key_pair(private_key_filename, public_key_filename)
        
        #le distribuiamo alle directory di lavoro
        copy_KeysDir()
        
        publish_key()
    
    else:
        print("Sintassi: 'Opzione non valida, il range deve essere inerente a questo: <generate/pubblish/all>")