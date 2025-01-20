# -*- coding: utf-8 -*-
"""
Created on Mon Oct 16 21:49:53 2023

@author: Paul
"""
import subprocess
import re
import platform
import time
import requests
import os
import sys
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import json
from colorama import Fore, Back, Style
import xml.etree.ElementTree as ET
import paramiko
from tqdm import tqdm
import psutil
import getpass
import socket
import pyotp



# Dichiarazione di variabili globali

current_vpn_connections = []  # Lista per le connessioni VPN attive
terminal_width, _ = os.get_terminal_size() #Giusto per delle stampe più ordinate
count_config = True

#Save dei risultati delle connessioni con un Operatore e un Employee
Result_Operator=""
Result_Employee=""
Result_IPSec=""


role="" #Variabile usata per definire via via, i role dei vari file di configurazione lanciati [RW_Privileged,RW_User, RW_Admin]
NameRole="" #Variabile usata per definire via via, i nomi delle role dei vari file di configurazione lanciati [Operator,Employee,Admin]

#Path del file di configurazione XML e delle credenziali per accedere in SSH al Firewall
Backup_file_xml = ""
SSH_credentials_file = ""


#Gestione dell'output del "menu" opzioni
options = ["--employee", "--operator", "--ipsec", "--result", "--exit"]
done_options=[]

#Gestione della chiamata "--all" al lancio dello script.
All_Execute=False

#File di output (nome di default) dove verran salvati i risultati
output_filename="result_log.txt"

"""
DEFINIZIONE DI VARIE FUNZIONI DI UTILITY IN GENERALE:
------------------------------------------------------------------------------------------------------------------------------
"""

def clear_process():
    #Ad ogni rilancio del codice rimuoviamo eventuali processi "OpenVPN" rimasti in esecuzione in caso di errore.

    
    if os.name == 'nt':  # Windows
        # Ottieni una lista di tutti i processi in esecuzione
        all_processes = psutil.process_iter(attrs=['pid', 'name'])
        
        # Itera attraverso la lista dei processi e termina quelli con il nome "OpenVPN.exe"
        for process in all_processes:
            if process.info['name'] == 'openvpn.exe':
                try:
                    process.terminate()
                except psutil.NoSuchProcess:
                    pass
    else:
        # Usa il comando pkill per terminare tutti i processi con il nome "OpenVPN"
        subprocess.call(["pkill", "openvpn.exe"])



def clear_console():
    # Verifica il sistema operativo e utilizza il comando appropriato per pulire la console.
        #IN PIU...togliamo eventuali processi "OpenVPN" rimasti in esecuzione in caso di errore.
    if os.name == 'nt':  # Windows
        os.system('cls')

    else:  # Unix-based systems (Linux, macOS)
        os.system('clear')


#Stoppiamo e facciamo ripartire il servizio openvpnservice per evitare conflitti con le rotte
def stop_and_start_openvpn_service():
    # Determina il sistema operativo corrente
    operating_system = platform.system()

    if operating_system == "Windows":
        # Comandi per fermare e avviare il servizio OpenVPN su Windows
        stop_command = "net stop openvpnservice"
        start_command = "net start openvpnservice"
    elif operating_system == "Linux":
        # Comandi per fermare e avviare il servizio OpenVPN su Linux
        stop_command = "sudo systemctl stop openvpnservice"
        start_command = "sudo systemctl start openvpnservice"
    else:
        return

    # Esegui il comando per fermare il servizio OpenVPN
    subprocess.run(stop_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Attendere che il servizio venga completamente arrestato
    time.sleep(2)  

    # Esegui il comando per avviare il servizio OpenVPN
    subprocess.run(start_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Attendere che il servizio venga completamente fatto ripartire
    time.sleep(2)
       


#Controlliamo se abbiamo tutti i file per lanciare il verificatore (poi in caso di errore ci pensano le altre funzioni che li usano)
def inizialization_json_file():
    global Backup_file_xml
    global SSH_credentials_file
    
    json_file = [f for f in os.listdir() if f.endswith(".json")]
    
    #SE Device.JSON (non modificabile ricordiamo) non dovesse essere presente fermiamo subito il tutto, ancor prima di arrivare al controllo sull'XML
    if not json_file:
        print(Fore.RED+ "-->Il File 'device.json' NON è presente, si prega di ripristinarlo per avviare il verificatore.", Style.RESET_ALL)
        return False
    
    return True
    

def inizialization_XML_file():
    global count_config
    global Backup_file_xml
    
    #Soltanto al lancio dell'ADMIN lo scarichiamo.
    if(count_config):
        count_config=False
        #Possiamo definirli staticamente in quanto non si cambia lo schema d'indirizzamento nell'ACME
        hostname = "100.100.0.2"
        port = 22
        
        print("---------------------------------------------------------------------")
        print("Apertura di una connessione SSH col Main-Firewall usando la chiave definita nell'infrastruttura:")
        
        remote_file_path = '/conf/config.xml'
    
        # Creazione dell'oggetto SSHClient
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        key_name = "SSHKey"
        
        if os.path.exists(key_name):
            try:
                # Connessione all'host OPNsense
                #ssh.connect(hostname, port, username, password)
                ssh.connect(hostname, port, username='root', key_filename='SSHKey')
                
                time.sleep(2)
        
                # Creazione di un canale SFTP
                sftp = ssh.open_sftp()
        
                # Copia del file remoto sulla macchina locale
                sftp.get(remote_file_path, os.getcwd()+"/config.xml")
        
                # Chiusura del canale SFTP
                sftp.close()
                
                # Chiusura della connessione SSH
                ssh.close()
                
                time.sleep(2)
                
                Backup_file_xml=os.getcwd()+"/config.xml"
                
                print(Fore.GREEN+"* Porting del file di Backup 'config.XML' dal Firewall e chiusura della connessione SSH, avvenute con successo.",Style.RESET_ALL)
                print("---------------------------------------------------------------------")
                return True
        
            except Exception as e:
                print(Fore.RED+f"* Errore durante la connessione SSH al Firewall principale.",Style.RESET_ALL)
                
                with open(output_filename, "a") as file:
                    file.write("- Errore durante la connessione SSH al Firewall principale, chiave errata o non configurata sul Firewall o accesso disabilitato per la connessione SSH")
                
                print("---------------------------------------------------------------------")
                return False
        else:
            print(f"Il file della chiave SSH '{key_name}' non esiste, nella directory: impossibile scaricare il file di backup della configurazione del Firewall e continuare.")
            return False
    else:
        #Di base dopo la prima volta sempre True, così che non dobbiamo sempre re-inserire le credenziali e riscaricarlo
        return True
        



# CERCHIAMO IL FILE DI CONFIGURAZIONE DA LANCIARE
def browse_for_config():
    root = tk.Tk()
    root.withdraw()
    openvpn_config_path = filedialog.askopenfilename(filetypes=[("OpenVPN Config Files", "*.ovpn")])
    return openvpn_config_path




# AGGIORNIAMO I FILE DI CONFIGURAZIONE COI COMANDI PER GENERARE I FILE DI LOG
def update_openvpn_config(config_path):
    # Estrai il nome del file .ovpn dalla path
    config_name = config_path.split('/')[-1]
    config_name = config_name.split('.')[0]

    # Leggi il file di configurazione .ovpn
    with open(config_path, "r") as config_file:
        config_lines = config_file.readlines()

    # Controlla se le linee "log" e "verb" sono già presenti
    log_exists = any("log " in line for line in config_lines)
    verb_exists = any("verb " in line for line in config_lines)

    # Aggiungi le linee mancanti se necessario
    if not log_exists:
        config_lines.append(f"\nlog log_{config_name}.txt\n")
    if not verb_exists:
        config_lines.append("verb 3\n")
        
    # Sostituisci le linee mancanti se necessario (cambia il nome del file di configurazione)
    if log_exists:
        # Se la linea "log" non esiste, trova la sua posizione e sostituiscila
        for i, line in enumerate(config_lines):
            if "log " in line:
                config_lines[i] = f"log log_{config_name}.txt\n"
                break

    # Scrivi le linee nel file di configurazione
    with open(config_path, "w") as config_file:
        config_file.writelines(config_lines)

    return config_name




# DISTINGUIAMO IL RUOLO DEL NOSTRO IP SORGENTE
def classify_role(source_ip, config_name):
    if source_ip.startswith("100.101.0"):
        return ["Admin","RW_Admin"]
    else:
        ruolo = interrogate_Backup_XML(config_name)
        
        if ("employe" in ruolo.lower()) or ("employe" in config_name):
            return ["Employees", "RW_User"]
        elif ("operator" in ruolo.lower()) or ("operator" in config_name):
            return ["Operators", "RW_Privileged"]
        else:
            return [ruolo, "Unknown"]





def interrogate_Backup_XML(config_name):
    finded_role="Unknown"
    
    # Definisci il pattern della regex
    pattern = r"_([A-Za-z]+)$"

    # Applica la regex alle stringhe
    match1 = re.search(pattern, config_name)

    # Estrai il nome dai match
    nome1 = match1.group(1)
    
    nome_gruppo, otp_seed_utente = trova_gruppo_e_otp_seed_per_utente("config.xml", nome1)
    
    
    finded_role = nome_gruppo
    
    return finded_role



# Definiamo lo starting Point per riconoscere il ruolo degli user in base al loro nome e UID di riferimento al gruppo a cui appartengono
def trova_gruppo_e_otp_seed_per_utente(file_xml, nome_utente):
    tree = ET.parse(file_xml)
    root = tree.getroot()

    # Cerca l'elemento <user> con il nome specificato (case-insensitive)
    utente_trovato = None
    for user_elem in root.findall('.//user'):
        nome_utente_elem = user_elem.find('name')
        if nome_utente_elem is not None and nome_utente_elem.text.lower() == nome_utente.lower():
            utente_trovato = user_elem
            break

    if utente_trovato is not None:
        # Ottieni il uid e l'otp_seed dell'utente trovato
        uid_utente = utente_trovato.find('uid').text
        otp_seed_utente = utente_trovato.find('otp_seed').text

        # Cerca il gruppo che contiene l'utente con il uid trovato
        for group_elem in root.findall('.//group'):
            membri_group = group_elem.findall('member')
            for membro_elem in membri_group:
                if membro_elem.text == uid_utente:
                    # Restituisci il nome del gruppo e l'otp_seed trovato
                    nome_gruppo = group_elem.find('name').text
                    return nome_gruppo, otp_seed_utente

    # Se l'utente o il gruppo non sono stati trovati, restituisci None
    return None, None



# SUDDIVIDIAMO GLI HOST DELLA TOPOLOGIA VIRTUALE
def split_devices(internal_devices):
    internal_network_devices = []
    external_network_devices = []

    for device in internal_devices:
        if device["IP"].startswith("100.100.1."):
            internal_network_devices.append(device)
        else:
            external_network_devices.append(device)

    return internal_network_devices, external_network_devices

"""
------------------------------------------------------------------------------------------------------------------------------
"""




"""
DEFINIZIONE FUNZIONI DI TEST DI CONNETTIVITA':
------------------------------------------------------------------------------------------------------------------------------
"""

# Controlla la connessione a Internet
def check_internet_connection():
    public_url = "https://www.google.com"
    try:
        response = requests.get(public_url)
        if response.status_code == 200:
          
            print("- Connessione all'indirizzo pubblico '{}', {} tramite OpenVPN.".format(public_url, Fore.GREEN + "riuscita" + Style.RESET_ALL))
            return True
        
        else:
         
            print("- Connessione all'indirizzo pubblico '{}', {} tramite OpenVPN.".format(public_url, Fore.RED + "fallita" + Style.RESET_ALL))
            return False
    
    except Exception as e:

        print("-Errore durante il controllo di connettività verso {}. Errore: {}".format(public_url, str(e)))
        return False


#Funzione di testing di connettività, per i RW.
def test_connectivity(ip, port, source_ip):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)  # Imposta un timeout per la connessione
        s.shutdown(socket.SHUT_RDWR)  # Chiude la socket in lettura e scrittura
        s.connect((ip, port))
        s.close()
        
        return True
    except socket.error as e:
        
        #Se la Socket non va a buon fine, proviamo anche un più basilare "Ping".
        try:
            
            # Determina il sistema operativo per adattare il comando ping
            sistema_operativo = platform.system().lower()
    
            # Imposta il comando ping in base al sistema operativo
            if sistema_operativo == "windows":
                comando_ping = ['ping', '-n', str(1), '-w', '2000', ip, "-S", source_ip]
                #comando_ping = ['ping', '-n', str(1), '-w', '3000', ip]
            else:
                comando_ping = ['ping', '-c', str(1), '-w', '2', ip, "-I", source_ip]
                #comando_ping = ['ping', '-c', str(1), '-w', '3', ip]
    
            # Esegui il comando ping
            risultato = subprocess.run(comando_ping, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
            output = risultato.stdout
            #print(output)
            
            if("reply" in output.lower()):
                return True
    
            # Se ci sono errori nel risultato, stampa l'errore
            if risultato.returncode != 0:
                return False
            
        except subprocess.CalledProcessError as e:
            return False



# CHECK CONNETTIVITA' NODI RETE
def check_custom_connection(source_ip):
    
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), output_filename), "a") as file: 
        
        #Separatore nel Log.txt tra una sezione e l'altra, ognuno ha la sua "testa" che chiude la sezione precedente
        file.write("---------------------------------------------------------------------\n")
        
        print(Fore.YELLOW + Style.BRIGHT + "* RUOLO:", NameRole, Style.RESET_ALL )  
        text= str("* TEST RW: " + NameRole + "\n")
        file.write(text)
    
        with open("devices.json", "r") as json_file:
            devices = json.load(json_file)
        
        success_connections = 0
        failure_connections = 0
        result=""
        
        internal_network_devices, external_network_devices = split_devices(devices)
    
        for device in devices:
            ip = device["IP"]
            name = device["Name"]
    
            try:
                

                if(test_connectivity(ip, 22, source_ip)):
                    success_connections += 1
                    text=str("- Connessione a {} ({}): V".format(name, ip) + "\n")
                    file.write(text)
                    
                    print("- Connessione a {} ({}): {}V{}".format(name, ip, Fore.GREEN, Style.RESET_ALL))

                # Se ci sono errori nel risultato, stampa l'errore
                else:
                    failure_connections += 1
                    
                    text=str("- Connessione a {} ({}): X".format(name, ip) + "\n")
                    file.write(text)
                    
                    print("- Connessione a {} ({}): {}X{}".format(name, ip, Fore.RED, Style.RESET_ALL))
                
            except subprocess.CalledProcessError as e:
                failure_connections += 1
                
                text=str("- Connessione a {} ({}): X".format(name, ip) + "\n")
                file.write(text)
                
                print("- Connessione a {} ({}): {}X{}".format(name, ip, Fore.RED, Style.RESET_ALL))
        
        check_internet= check_internet_connection()
        
        text=str("- Connessione alla rete pubblica tramite VPN: " + str(check_internet) + "\n")
        file.write(text)
        
        if (role == "RW_Admin" or role == "RW_Privileged") and (success_connections == len(external_network_devices) + len(internal_network_devices)) and failure_connections == 0 and check_internet:
            print("")
            
            print(Back.GREEN + "Requisiti rispettati per la VPN aperta.", Style.RESET_ALL)
            
            file.write("-->Requisiti rispettati per la VPN aperta. \n")
            
            print("")
            result= "-->Result: Success"
        
        elif role == "RW_User" and success_connections == len(external_network_devices) and failure_connections == len(internal_network_devices) and check_internet:
            print("")
            
            print(Back.GREEN + "Requisiti rispettati per la VPN aperta.", Style.RESET_ALL)
            file.write("-->Requisiti rispettati per la VPN aperta. \n")
            
            print("")
            result= "-->Result: Success"
       
        else:
            print("")
            
            print(Back.RED + "Requisiti NON rispettati per la VPN aperta.", Style.RESET_ALL)
            file.write("-->Requisiti NON rispettati per la VPN aperta. \n")
            
            print("")
            result= "-->Result: Failed"
        



    
    #Chiudiamo la connessione corrente dopo ogni Test sia di successo che di fallimento.
    close_vpn_connection()
    return result
        


# Estrai il nome del file .ovpn dal percorso
def select_and_configure_vpn():
    openvpn_config_path = browse_for_config()
    if ((openvpn_config_path != '')):
        config_name = update_openvpn_config(openvpn_config_path)
        return openvpn_config_path, config_name
    else:
        return None,None



# Lanciare una connessione VPN
def start_vpn_connection(openvpn_config_path, config_name, expected_role):
    
    check_credentials = False
    global role 
    global NameRole
    global current_vpn_connections
    global All_Execute
    
    #Dobbiamo eventualmente aggiornare i file di config. per la generazione dei Log.
    update_openvpn_config(openvpn_config_path)
    
    #Apriamo il file di configurazione
    with open(openvpn_config_path, 'r') as config_file:
        config_content = config_file.read()
        
        #Se presente la dicitura apposita, inseriamo le credenziali.
        if 'auth-user-pass' in config_content:
            check_credentials = True
            
            # Definisci il pattern della regex
            pattern = r"_([A-Za-z]+)$"

            # Applica la regex alle stringhe
            match1 = re.search(pattern, config_name)

            # Estrai il nome dai match
            nome1 = match1.group(1)
            
            #Cerchiamo l'eventuale OTP Seed associato al client VPN che si sta connettendo
            nome_gruppo, otp_seed_utente = trova_gruppo_e_otp_seed_per_utente("config.xml", nome1)
            
            # Verifica se sono stati passati argomenti
            if All_Execute:
                
                #Dobbiamo eventualmente aggiornare i file di config. per la generazione dei Log.
                #update_openvpn_config(openvpn_config_path)
                
                # Carica il contenuto del file JSON
                with open('RW-Information.json', 'r') as file:
                    data = json.load(file)
                for item in data:
                    if item['Role'] == expected_role:
                        username = item['Username']
                        password = item['Password']
                        break
            else:
                username = input("° Inserisci il tuo nome utente VPN: ")
                password = getpass.getpass ("° Inserisci la tua password VPN: ")
            
            
            #Generiamo un TOTP e fondiamolo alla password, se c'era un Seed associato all'utente VPN
            if otp_seed_utente is not None:
                # Crea un oggetto TOTP con il seed
                totp = pyotp.TOTP(otp_seed_utente)
                
                # Genera e stampa il token corrente
                token = totp.now()
                
                password = password + token
            
            with open('pass.txt', 'w') as file:
                file.write(username + '\n')
                file.write(password)
            
            #Lanciamo il comando "openVPN" per aprire e lanciare la connessione
            current_vpn_process = subprocess.Popen(['openvpn', '--config', openvpn_config_path, '--auth-user-pass', 'pass.txt'], creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            current_vpn_process = subprocess.Popen(['openvpn', '--config', openvpn_config_path], creationflags=subprocess.CREATE_NO_WINDOW)
        
        # Durata della temporizzazione (in secondi)
        duration = 9
        
        # Lunghezza personalizzata della barra
        custom_bar_length = 20
        
        # Colore personalizzato per la barra (utilizziamo Fore.GREEN come esempio)
        custom_bar_color = Fore.YELLOW
        
        # Personalizza il formato della barra di avanzamento
        custom_format = f"{Style.BRIGHT}-->{Style.RESET_ALL} {Style.BRIGHT}{Fore.CYAN}Tentativo di connessione VPN:{Style.RESET_ALL} {Style.BRIGHT}{custom_bar_color}|{{bar:{custom_bar_length}}}|{Style.RESET_ALL}"

        
        # Ciclo di aggiornamento della progress bar
        with tqdm(total=duration, position=0, leave=True, bar_format=custom_format) as pbar:
            for _ in range(duration):
                time.sleep(1)  # Attendi 1 secondo
                pbar.update(1)  # Aggiorna la barra di avanzamento di 1 secondo
        
        if os.path.exists('pass.txt'):
            os.remove('pass.txt')
        
        # Leggi il file di log
        log_file_path = f"log_{config_name}.txt"
        with open(log_file_path, "r") as log_file:
            log_lines = log_file.readlines()
        
        # Cerca l'indirizzo IP virtuale nel file di log e il ruolo usandolo eventualmente
        virtual_ip = None
        role = None
        check_presence_externalVPN = True
        for line in log_lines:
            
            if "UDP link remote" in line:
                #Questa variabile rimarrà false, sse UDP link remote si trova sull'ultima riga del Log letto, e questo avviene solo se si apre una VPN interna prima dell'esterna
                check_presence_externalVPN = False
                
            elif "PUSH: Received control message" in line:
                #Risettiamo il Check a True in quanto allora è presente la VPN esterna, o non leggeremo il "PUSH"
                check_presence_externalVPN = True
                match = re.search(r"ifconfig ([\d\.]+) ([\d\.]+)", line)
                if match: #TROVATO IP-->VUOL DIRE CHE HAI CORRETTAMENTE LANCIATO ADMIN, o RW dopo di lui
                    
                    virtual_ip = match.group(1)  # Questo estrae il primo indirizzo IPv4 dopo "ifconfig"
                    
                    #Questo IF non viene letto se si lancia un RW prima di Admin, o se non ci viene rilasciato un IP dal file 'ovpn'
                    if(inizialization_XML_file() == False): #Si sbagliano le credenziali SSH = Niente XML = Bisogna arrestarsi
                        virtual_ip = None
                        break
                    
                    #Indirizziamo l'IP con un Ruolo
                    role_ip = classify_role(virtual_ip, config_name)
                    
                    role = role_ip[1] #-->Formato: ["Admin/Operator/Employee", Token] ...ma anche "Unknown"
                    NameRole= role_ip[0]
                    
                    if(role == "Unknown"):
                        #L'unico caso per avere "Unknown" è quello scritto nei Print.
                            #Poichè se non fossero configurate le Subnet, l'IP non verrebbe proprio rilasciato.
                        print(Style.BRIGHT + Fore.RED+ "Requisiti NON rispettati:")
                        print(Fore.YELLOW +"IP rilasciato e connessione al Main-Firewall eseguita, tuttavia c'è un ambiguità nel riconoscere il tipo di client-VPN.")
                        print(Fore.YELLOW +"Assicurati che nell'assegnazione dei gruppi sul server VPN, e/o nella dicitura dei loro nomi, ci sia una corretta e testuale distinzione Employee/Operator come specificato nell'Assignment!")
                        virtual_ip = None
                        break
                        
                    elif (role != expected_role):
                        print(Style.BRIGHT + Fore.RED+"Il file di configurazione scelto non appartiene al gruppo disegnato per questo test!", "\n", Style.RESET_ALL)
                        #Dobbiamo resettarlo a None per segnalare che non dobbiamo continuare oltre.
                        virtual_ip = None
                        break
                        
                    
                    if(check_credentials):
                        print(Style.BRIGHT + Fore.GREEN+"Credenziali inserite CORRETTE.", "\n", Style.RESET_ALL)
                    
                    break  # Visto che è stato trovato, esci dal ciclo

            # Se troviamo la stringa corrispondente all'autenticazione fallita dobbiamo segnalarlo!
            elif (("AUTH_FAILED" in line)):
                #Resettiamo il Check a True in quanto allora è presente la VPN esterna, o non leggeremo il "AUTH_FAILED"
                check_presence_externalVPN = True
                
                print("")
                print(Style.BRIGHT + Fore.RED+"Credenziali inserite SCORRETTE: Autenticazione fallita.", Style.RESET_ALL)
                
                #Nessuna domanda, se abbiamo selezionato l'ALL come parametro di esecuzione.
                if(All_Execute == False):
                    question= input(Fore.YELLOW+"Vuoi riprovare ad inserirle? [Y/N]: ")
                    
                    #QUI i casi sono 2, o ciclerò all'infinito finchè non do le giuste credenziali, oppure uscirò col test fallito quando gli dirò "NO".
                    while question!="Y" or question!="N":
                        if (question.lower() == "y"):
                            virtual_ip= start_vpn_connection(openvpn_config_path, config_name, expected_role)
                            #uccido il ramo di computazione precedente, se decido di re-inserire le credenziali generandone uno nuovo
                            current_vpn_process.terminate()
                            
                            return virtual_ip 
                        elif (question.lower() == "n"):
                            break  # Visto che è stato trovato il messaggio e si è deciso di non riprovare, esci dal ciclo
                        else:
                            question= input("Input non valido, vuoi riprovare a inserire le credenziali? [Y/N]: ")
            
            
            #IF di gestione nel caso in cui l'errore sia dovuto al certificato nel file ".ovpn"
            elif "fatal error" in line:
                #Risettiamo il Check a True in quanto allora è presente la VPN esterna, o non leggeremo il "fatal error"
                check_presence_externalVPN = True
                print(Style.BRIGHT + Fore.RED+"Errore: Chiave SSH o certificato non valido definiti per questo file di configurazione! ", "\n")
                
                break  # Visto che è stato trovato il messaggio, esci dal ciclo
        
        #Qui 'check_presence_externalVPN' lo usiamo solo per vedere la "completezza" del file di log...e si blocca se:
            #O abbiam lanciato le VPN interne per prime.
        if(check_presence_externalVPN == False and len(current_vpn_connections)==0):
            print("")
            print("Scelto file di configurazione di tipo 'Operator/Employee' prima di lanciare un Admin!")
    
            #O se il file non trova OpenVPN server configurati a rilasciargli un IP
        elif (check_presence_externalVPN == False):
            print("")
            print(Style.BRIGHT + Fore.RED+"Non è stato possibile trovare nessun OpenVPN Server configurato o abilitato per questo file di configurazione!", Style.RESET_ALL)
        
        #ci salviamo un report della connessione aperta dentro "connection_info" e poi lo lavoriamo dopo...
        connection_info = {"PID": current_vpn_process, "IP": virtual_ip, "ROLE": role}
        current_vpn_connections.append(connection_info)
        
        #Ci ritorna "None" solo se le credenziali erano errate o l'IP non è stato trovato, magari perchè si è aperto prima Bob che Sanna ad esempio.
        return virtual_ip





# Configurazione delle VPN per i test sulle connettività
def configure_start_internal_vpn(assigned_role):
    
    global Result_Operator
    global Result_Employee
    
    global All_Execute
    openvpn_config_path=None
    config_name=None 
    
    # Verifica se sono stati passati argomenti
    if All_Execute:
        
        cartella_di_lavoro = os.getcwd()

        # Ottenere la lista di tutti i file nella cartella di lavoro
        files = os.listdir(cartella_di_lavoro)
        
        
        # Filtrare i file che contengono la stringa "operator" (senza distinzione tra maiuscole e minuscole) e hanno estensione ".ovpn"
        for file in files:
            
            if file.lower().endswith(".ovpn"):
                
                stringa1 = file.rstrip(".ovpn")
                
                # Definisci il pattern della regex
                pattern = r"_([A-Za-z]+)$"
                
                # Applica la regex alle stringhe
                match1 = re.search(pattern, stringa1)
                
                #Se c'è match (e quindi escludiamo il file "admin") vai avanti
                if match1:
                    # Estrai il nome dai match
                    nome1 = match1.group(1)
                    
                    nome_gruppo, otp_seed_utente = trova_gruppo_e_otp_seed_per_utente("config.xml", nome1)
            
                    if(assigned_role=="RW_Privileged"):
                        if "operator" in nome_gruppo.lower():
                            openvpn_config_path = file
                            config_name = stringa1
                            break
            
                    elif(assigned_role=="RW_User"):
                        # Filtrare i file che contengono la stringa "operator" (senza distinzione tra maiuscole e minuscole) e hanno estensione ".ovpn"
                        if "employee" in nome_gruppo.lower():
                            openvpn_config_path = file
                            config_name = stringa1
                            break
        
    else:
        openvpn_config_path, config_name = select_and_configure_vpn()
    
    #Gestiamo il fatto di non aver messo niente nell'esplora risorse che ci fa scegliere il file di configurazione
    if(openvpn_config_path and config_name) != None:
        print("")
        print(Style.BRIGHT + Fore.CYAN +f"Configurazione VPN '{config_name}' pronta per essere avviata.", Style.RESET_ALL)
        
        
        #Lanciamo la connessione
        virtual_ip= start_vpn_connection(openvpn_config_path, config_name, assigned_role)
        
        if virtual_ip is None:
            print(Back.RED + "Test fallito: connessione non avvenuta.", Style.RESET_ALL)
            print("")
            
            Result="-->Result: Failed"
            close_vpn_processes() #chiudiamo l'ultimo processo OpenVPN aperto (ossia il precedente)
            
        else:
            # Stampa l'indirizzo IP virtuale
            print("Indirizzo IP privato virtuale:", Style.BRIGHT + Fore.CYAN+ virtual_ip, Style.RESET_ALL, "\n")
            
            Result=check_custom_connection(virtual_ip)
        
        if(assigned_role=="RW_Privileged"):
            Result_Operator=Result
        elif(assigned_role=="RW_User"):
            Result_Employee=Result
    else:
        #METTI POP-UP QUI
        messagebox.showinfo("Attenzione!", "Seleziona almeno un file.", icon='warning')
        #print("Seleziona almeno un file.", "\n")
        configure_start_internal_vpn(assigned_role)
 
    

# Chiudere l'ultima connessione VPN aperta
def close_vpn_connection():
    if len(current_vpn_connections)>0:
        Last_VPN_Opened= current_vpn_connections[-1]
        Last_PID= Last_VPN_Opened["PID"]
        Last_PID.terminate()
        current_vpn_connections.pop()
        print(Style.BRIGHT + Fore.CYAN +"Connessione VPN: ",Last_VPN_Opened["IP"], "chiusa con successo.", "\n", Style.RESET_ALL)
    else:
        print("Nessuna connessione VPN aperta.", "\n")
      


def close_vpn_processes():
        #Chiudiamo la VPN esterna (senza messaggio di output "Connessione IP: //' chiusa)
        Last_VPN_Opened= current_vpn_connections[-1]
        Last_PID= Last_VPN_Opened["PID"]
        Last_PID.terminate()
        current_vpn_connections.pop()

"""
------------------------------------------------------------------------------------------------------------------------------
"""




"""
DEFINIZIONE DI FUNZIONI DI CONTROLLO PER LA COMPONENTE IPSEC:
------------------------------------------------------------------------------------------------------------------------------
"""
#Funzione per l'inserimento da Tastiera delle credenziali SSH
def Launch_SSH_IPSecTest():
    #Possiamo definirli staticamente in quanto non si cambia lo schema d'indirizzamento nell'ACME
    hostname = "100.100.0.2"
    port = 22
           
    print(Fore.YELLOW + Style.BRIGHT+ "Esito dello stato dell'IPSec':", Style.RESET_ALL)
    print("---------------------------------------------------------------------")
   
    #Una volta inserite le credenziali lanciamo il test sull'IPSec con SSH sfruttando quanto inserito.
    test_IPSec(hostname, port)


#Se abbiam trovato le credenziali e la porta andiamo a testare il comando dell'IPSec per leggerne lo stato
def test_IPSec(hostname, port): 
    
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), output_filename), "a") as file: 
        
        #Separatore nel Log.txt tra una sezione e l'altra, ognuno ha la sua "testa" che chiude la sezione precedente
        file.write("---------------------------------------------------------------------\n")
        
        file.write("* TEST IPSEC:\n")
    
        #TUTTO OK: ora diamo il comando da eseguire sulla shell remota
        command_to_run = 'ipsec status'
        global Result_IPSec
        
        try:
            # Creare una connessione SSH
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            #ssh.connect(hostname, port, username, password, timeout=3)
            ssh.connect(hostname, port, username='root', key_filename='SSHKey')
            # Eseguire il comando sulla shell remota e ottenere l'output
            stdin, stdout, stderr = ssh.exec_command(command_to_run)
    
            # Leggere l'output del comando
            output = stdout.read().decode()
    
            # Chiudere la connessione SSH
            ssh.close()
    
            # Analizza l'output per verificare lo stato di IPSec
            if "up" in output.lower() and "established" in output.lower():
                print(Back.GREEN +"IPSec è attivo e configurato correttamente.", Style.RESET_ALL)
                
                text="--> IPSec è attivo e configurato correttamente. \n"
                file.write(text)
                
                Result_IPSec="-->Result: Success"
                return Result_IPSec
                
            else:
                print(Back.RED +"IPSec non è attivo o potrebbe non essere configurato correttamente.", Style.RESET_ALL)
                
                text="--> IPSec NON è attivo o potrebbe non essere configurato correttamente."
                file.write(text)
                
                Result_IPSec="-->Result: Failed"
                return Result_IPSec
            
        except paramiko.SSHException as e:
            print(Back.RED +f"Errore nella connessione SSH: {str(e)}",  Style.RESET_ALL)
            
            Result_IPSec="-->Result: Failed"
            return Result_IPSec
        
        except Exception as e:
            print(Back.RED +f"Errore: {e}",Style.RESET_ALL)
            
            Result_IPSec="-->Result: Failed"
            return Result_IPSec
        
    
    # Ripristina l'output standard
    sys.stdout = sys.__stdout__

"""
------------------------------------------------------------------------------------------------------------------------------
"""




"""
DEFINIZIONE DEL MENU E DEI VARI LAUNCHER DI CONTROLLO SUI REQUISITI:
------------------------------------------------------------------------------------------------------------------------------
"""


def Select_Test_Option():
    global Result_Operator
    global Result_Employee
    global Result_IPSec
    
    global options 
    global done_options
    
    #print("A1------>",options, done_options)
    
    remaining_options = [option for option in options if option not in done_options]
    
    print("")
    question=input((Style.BRIGHT+ "Ora seleziona un opzione per proseguire " + Style.RESET_ALL + Fore.YELLOW + f"{remaining_options}: " + Style.RESET_ALL))
    
    question = question.lower()
    
    if question in done_options:
        messagebox.showinfo("Attenzione!", "Test già verificato, prosegui con i rimanenti elencati.", icon='warning')
        Select_Test_Option()
        
    elif question in options:
        if((question == "--result") and ((Result_Operator and Result_Employee and Result_IPSec)== "")):
            messagebox.showinfo("Attenzione!", "Non è ancora possibile ottenere un report completo, mancano dei check da eseguire.", icon='warning')
            Select_Test_Option()  
        else:
            
            done_options.append(question)
            
            # Esegui la funzione corrispondente
            if question == "--employee":
                launch_Employee()
            elif question == "--operator":
                launch_Operator()
            elif question == "--ipsec":
                launch_IPSec()
            elif question == "--exit":
                close_vpn_processes()
            elif question == "--result":
                percentuale_di_Successo()
         
            done_options.append(question)
            
    
    else:
        messagebox.showinfo("Attenzione!", "Input non valido per la scelta.", icon='warning')
        Select_Test_Option()




def launch_Admin():
    global All_Execute
    
    clear_console()
    text = "* File di tipo Admin da connettere: *"
    centered_text = text.center(terminal_width)

    print(Style.BRIGHT + Fore.MAGENTA + centered_text, Style.RESET_ALL)
    
    #Apriamo la VPN Esterna
    
    
    # Verifica se sono stati passati argomenti
    if All_Execute:
       
        cartella_di_lavoro = os.getcwd()

        # Ottenere la lista di tutti i file nella cartella di lavoro
        files = os.listdir(cartella_di_lavoro)

        # Definire il pattern per cercare i file con il formato desiderato
        #pattern = re.compile(r'^[a-zA-Z]+\.\d{7}\.ovpn$')
       
    
        # Filtrare i file che corrispondono al pattern
        file_ovpn = [f for f in files if 'alice' not in f.lower() and 'bob' not in f.lower()]
        
        
        openvpn_config_path = file_ovpn[0]
        config_name = openvpn_config_path.split('.')[0]
        
    else:
        openvpn_config_path, config_name = select_and_configure_vpn()
    
    if(openvpn_config_path and config_name) != None:
        print("")
        print(Style.BRIGHT + Fore.CYAN + f"Configurazione VPN '{config_name}' pronta per essere avviata.", Style.RESET_ALL)
        virtual_ip= start_vpn_connection(openvpn_config_path, config_name, "RW_Admin")
        
        #QUI se apriamo un "Operator/Employee" prima di "Admin" o se il suo certificato non è valido sarà None
        if virtual_ip is None:
            print(Style.BRIGHT + Fore.RED+ "--> Si è verificato un errore, non è possibile lanciare i test!", Style.RESET_ALL)
            close_vpn_processes()
        else:
            # Attendi l'input dell'utente prima di continuare
            print(Style.BRIGHT + Fore.GREEN+"--> 'Connection' e 'import' riusciti con Successo.", "\n", Style.RESET_ALL)
            
            # Verifica se sono stati passati argomenti
            if All_Execute:
                time.sleep(3)
                launch_Employee()
                time.sleep(3)
                launch_Operator()
                time.sleep(3)
                launch_IPSec()
                time.sleep(3)
                percentuale_di_Successo()
            else:
                Select_Test_Option()
    else:
       
        messagebox.showinfo("Attenzione!", "Seleziona un file di configurazione.", icon='warning')
        launch_Admin()
        
        


def launch_Operator():
    clear_console()
    global All_Execute
    text = "* File di tipo Operator da testare: *"
    centered_text = text.center(terminal_width)

    print(Style.BRIGHT + Fore.MAGENTA + centered_text, Style.RESET_ALL)
    configure_start_internal_vpn("RW_Privileged")
    
    if All_Execute == False:
        #Finito un'altro si prosegue
        Select_Test_Option()
    
    return 



def launch_Employee():
    clear_console()
    global All_Execute
    text = "* File di tipo Employee da testare: *"
    centered_text = text.center(terminal_width)
    
    print(Style.BRIGHT + Fore.MAGENTA + centered_text, Style.RESET_ALL)
    configure_start_internal_vpn("RW_User")
    
    
    if All_Execute == False:
        #Finito un'altro si prosegue
        Select_Test_Option()
    
    return 
   



def launch_IPSec():
    clear_console()
    global All_Execute
    text = "* Test dell'IPSec in corso tramite SSH: *"
    centered_text = text.center(terminal_width)
    
    print(Style.BRIGHT + Fore.MAGENTA + centered_text, Style.RESET_ALL)
    Launch_SSH_IPSecTest()
    
    if All_Execute == False:
        #Finito un'altro si prosegue
        Select_Test_Option()
    
    return 
"""
------------------------------------------------------------------------------------------------------------------------------
"""




"""
DEFINIZIONE DELLA FUNZIONE DI STAMPA FINALE (con check conclusi):
------------------------------------------------------------------------------------------------------------------------------
"""
def percentuale_di_Successo():
    clear_console()
    #Stampa della percentuale e di verifica finale sui requisiti (o comunque su quelli fatti)

    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), output_filename), "a") as file: 
         
        #Separatore nel Log.txt tra una sezione e l'altra, ognuno ha la sua "testa" che chiude la sezione precedente
        file.write("---------------------------------------------------------------------\n")
        file.write("* ESITO FINALE: \n")
        
        text = "-------------------------STAMPA DEI RISULTATI-------------------------"
        
        
        
        print(Style.BRIGHT + Fore.MAGENTA + text , Style.RESET_ALL)
        
        
        Result_Array=[Result_Operator,Result_Employee,Result_IPSec]
    
        
        print(Fore.CYAN+Style.BRIGHT+ "TEST: RW 'Operator'",Fore.WHITE+Style.BRIGHT+ (Result_Operator),Style.RESET_ALL)
        print(Fore.CYAN+Style.BRIGHT+ "TEST: RW 'Employee'",Fore.WHITE+Style.BRIGHT+ (Result_Employee), Style.RESET_ALL )
        print(Fore.CYAN+Style.BRIGHT+ "TEST: IPSec",Fore.WHITE+Style.BRIGHT+ (Result_IPSec), Style.RESET_ALL)
        
        count_V = Result_Array.count("-->Result: Success")
        percentuale = (count_V / len(Result_Array)) * 100
        
        text = "----------------------------------------------------------------------"
        
        print(Style.BRIGHT + Fore.MAGENTA + text + "\n" , Style.RESET_ALL)
        
        
        if(percentuale<100):
            print("La percentuale svolta e verificata correttamente è del", Fore.RED+ f"{percentuale}%",Style.RESET_ALL)
            print(Back.RED +"La verifica dei requisiti definiti nell'Assignment non è ancora superata.", Style.RESET_ALL)
            file.write("La verifica dei requisiti definiti nell'Assignment NON è ancora totalmente superata -->Percentuale:" + f"{percentuale}%"+"\n")
        else:
            print("La percentuale svolta e verificata correttamente è del", Fore.GREEN+ f"{percentuale}%",Style.RESET_ALL)
            print(Back.GREEN +"La verifica dei requisiti definiti nell'Assignment è stata superata!", Style.RESET_ALL)
            file.write("La verifica dei requisiti definiti nell'Assignment è stata SUPERATA! -->Percentuale:" + f"{percentuale}%"+"\n")
    
        close_vpn_processes()
    
        #Si eliminano i file di log superflui (alice,bob, admin) tranne quello di "result"
        time.sleep(2)
        [os.remove(file) for file in os.listdir() if file.endswith('.txt') and 'result' not in file]
        


"""
------------------------------------------------------------------------------------------------------------------------------
"""




"""
DEFINIZIONE DELLA MAIN PAGE:
------------------------------------------------------------------------------------------------------------------------------
"""

clear_console()
clear_process()


# Ripristina l'output standard
sys.stdout = sys.__stdout__

#Titolo verificatore
text = "|| GRADER 'ASSIGNMENT 1: VPN on ACME co.' ||"
centered_text = text.center(terminal_width)
print(Style.BRIGHT + Fore.CYAN + centered_text, Style.RESET_ALL , "\n")

#Breve spiegazione
text=("In questa attività, verrà condotta una verifica della configurazione dei servizi su reti ACME co.\n \
• Verrà controllata la connettività dei Road Warriors (che si dividono in 'Employee/Operator') dopo aver configurato il tunnel VPN esterno a loro dedicato.\n \
• Controllerà l'esistenza e la configurazione di un tunnel IPSec tra i Firewall router posizionati in diverse reti.\n")
centered_text = text.center(terminal_width)
print(Style.BRIGHT + Fore.YELLOW + centered_text, Style.RESET_ALL , "\n")

#Crediti
text = "-Corso di 'Practical Network Defense: Dipartimento Informatica, Sapienza Università di Roma' "
right_aligned_text = text.rjust(terminal_width)
print(Style.BRIGHT + Fore.MAGENTA + right_aligned_text, Style.RESET_ALL , "\n")

#Opzione -ALL da linea di comando all'invocazione del PY
if len(sys.argv) > 1:
    
    
    # Converti gli argomenti a stringhe minuscole
    lowercase_argv = [arg.lower() for arg in sys.argv]
    
    if any('all' in x for x in lowercase_argv):
        if not any('launcher' in x for x in lowercase_argv):
            All_Execute=True
            

    
    if len(sys.argv) >= 2 and All_Execute == False:
        # Ottieni l'argomento JSON dal comando di lancio
        parametri_json = sys.argv[1]
        
        # Decodifica la stringa JSON in un dizionario
        parametri = json.loads(parametri_json)
        # Verifica se il valore di "All" è True nel dizionario
        if parametri.get("All", False):
            All_Execute=True
        
        output_filename = parametri.get("Nome_File", "")


# Scriviamo ora la testa del file di report.
with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), output_filename), "w") as file: 
    # Redirect dell'output dei print verso il file
    sys.stdout = file
    print("|| REPORT-GRADER 'ASSIGNMENT 1: VPN on ACME co.' ||")
    
# Ripristina sys.stdout al suo valore originale
sys.stdout = sys.__stdout__



#Controlliamo se abbiam almeno tutti i file su cui lavorare...principalmente il backup_file.XML
if(inizialization_json_file()):
    
    if All_Execute == False:
        
        #Riavviamo il servizio di OpenVPN
        #stop_and_start_openvpn_service()
        
        input("• Premi INVIO per cominciare, aprendo inazitutto la VPN esterna/principale.")
        
    else:
        
        print("• Si passa ora ad una verifica della configurazione infrastrutturale, interamente nel suo complesso...")
        time.sleep(3)
        #Riavviamo il servizio di OpenVPN
        #stop_and_start_openvpn_service()
    
    launch_Admin()
    

  
       
   
