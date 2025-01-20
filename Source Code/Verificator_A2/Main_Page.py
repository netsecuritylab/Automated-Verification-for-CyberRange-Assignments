# -*- coding: utf-8 -*-
"""
Created on Sun Nov 19 15:21:31 2023

@author: Paul
"""
import subprocess
import re
import time
import os
import sys
from tkinter import messagebox
from colorama import Fore, Back, Style
import paramiko
from tqdm import tqdm
import psutil
import json


terminal_width, _ = os.get_terminal_size() #Giusto per delle stampe più ordinate
success_array=[]
output_filename="result_log.txt"

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

    # Scrivi le linee nel file di configurazione
    with open(config_path, "w") as config_file:
        config_file.writelines(config_lines)

    return config_name


# Lanciare una connessione VPN
def start_vpn_connection(openvpn_config_path):
    
    config_name=update_openvpn_config(openvpn_config_path)
    
    
    subprocess.Popen(['openvpn', '--config', openvpn_config_path], creationflags=subprocess.CREATE_NO_WINDOW)
    
    # Durata della temporizzazione (in secondi)
    duration = 5
    
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
    
    
    # Leggi il file di log
    log_file_path = f"log_{config_name}.txt"
    with open(log_file_path, "r") as log_file:
        log_lines = log_file.readlines()
    
    # Cerca l'indirizzo IP virtuale nel file di log e il ruolo usandolo eventualmente
    virtual_ip = None
    check_presence_externalVPN = True
    for line in log_lines:
        
        if "UDP link remote" in line:
            #Questa variabile rimarrà false, sse UDP link remote si trova sull'ultima riga del Log letto, e questo avviene solo se si apre una VPN interna prima dell'esterna
            check_presence_externalVPN = False
            
        elif "PUSH: Received control message" in line:
            #Risettiamo il Check a True in quanto allora è presente la VPN esterna, o non leggeremo il "PUSH"
            check_presence_externalVPN = True
            match = re.search(r"ifconfig ([\d\.]+) ([\d\.]+)", line)
            if match: #TROVATO IP-->VUOL DIRE CHE HAI CORRETTAMENTE LANCIATO ADMIN
                virtual_ip = match.group(1)  # Questo estrae il primo indirizzo IPv4 dopo "ifconfig"
        
        
        #IF di gestione nel caso in cui l'errore sia dovuto al certificato nel file ".ovpn"
        elif "fatal error" in line:
            #Risettiamo il Check a True in quanto allora è presente la VPN esterna, o non leggeremo il "fatal error"
            check_presence_externalVPN = True
            print(Style.BRIGHT + Fore.RED+"Errore: Chiave o certificato non valido trovato nel file di configurazione", "\n")
            
            break  # Visto che è stato trovato il messaggio, esci dal ciclo
    
    #Qui 'check_presence_externalVPN' lo usiamo solo per vedere la "completezza" del file di log...e si blocca se:
        #O abbiam lanciato le VPN interne per prime.
    if (check_presence_externalVPN == False):
        print("")
        print(Style.BRIGHT + Fore.RED+"Non è stato possibile trovare nessun OpenVPN Server configurato o abilitato per questo file di configurazione!", Style.RESET_ALL)
    
    
    #Ci ritorna "None" solo se le credenziali erano errate o l'IP non è stato trovato, magari perchè si è aperto prima Bob che Sanna ad esempio.
    return virtual_ip


def update_result_log(messaggio,check_req):
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), output_filename), "a") as file: 
        
           # Redirect dell'output dei print verso il file
           sys.stdout = file
           print(("---------------------------------------------------------------------"))
           print(messaggio)
           print(check_req)
           
    # Ripristina l'output standard
    sys.stdout = sys.__stdout__


def clear_console():
    # Verifica il sistema operativo e utilizza il comando appropriato per pulire la console.
        #IN PIU...togliamo eventuali processi "OpenVPN" rimasti in esecuzione in caso di errore.
    if os.name == 'nt':  # Windows
        os.system('cls')

    else:  # Unix-based systems (Linux, macOS)
        os.system('clear')


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


def execute_all():
    for key in menu.keys():
        check_req = menu[key][0]()
        messaggio= menu[key][1]
        update_result_log(messaggio, check_req)
        success_array.append(check_req)


def final_report():
    final_check = all("SUCCESS" in elem for elem in success_array)
    print("")
    
    success_count = sum("SUCCESS" in elem for elem in success_array)
    percentage_success = (success_count / len(success_array)) * 100
    
    if(final_check):
        messaggio=f"La verifica dei requisiti definiti nell'Assignment è stata superata al {percentage_success}%."
        print(Back.GREEN +messaggio+ Style.RESET_ALL)
        update_result_log(messaggio,'')
    else:
        messaggio=f"La verifica dei requisiti definiti nell'Assignment è stata superata al {percentage_success}%."
        print(Back.RED +messaggio+ Style.RESET_ALL)
        update_result_log(messaggio,'')
    
    clear_process()
    
    #Si eliminano i file di log superflui 
    time.sleep(1)
    for file in os.listdir():
        if file.endswith('.txt') and 'result' not in file:
            os.remove(file)
    
    


def inizialization_XML_file(hostname, namefile):
    
    #Possiamo definirli "staticamente" in quanto non si cambia lo schema d'indirizzamento nell'ACME
    port = 22
    print("---------------------------------------------------------------------")
    print("• Checking del file di configurazione del Main-Firewall tramite SSH, usando la private key definita nell'infrastruttura: ")
    
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
            sftp.get(remote_file_path, os.getcwd()+namefile)
    
            # Chiusura del canale SFTP
            sftp.close()
            
            # Chiusura della connessione SSH
            ssh.close()
            
            time.sleep(2)
            
            print("--> "+Fore.GREEN+"Porting del file di Backup 'config.XML' dal Firewall e chiusura della connessione SSH, avvenute con successo.",Style.RESET_ALL)
            print("---------------------------------------------------------------------")
            
            return True
    
        except Exception as e:
            
            print("--> "+Fore.RED+f"Errore durante la connessione SSH al Firewall principale.",Style.RESET_ALL)
            print("---------------------------------------------------------------------")
            return False
    else:
        print("--> "+Fore.RED+f"Il file della chiave SSH '{key_name}' non esiste, nella directory: impossibile scaricare il file di backup della configurazione del Firewall e continuare.",Style.RESET_ALL)
        return False
   




       

# Ripristina l'output standard
sys.stdout = sys.__stdout__


clear_console()
clear_process()

"""
DEFINIZIONE DELLA MAIN PAGE:
------------------------------------------------------------------------------------------------------------------------------
"""

#Titolo verificatore
text = "|| GRADER 'ASSIGNMENT 2: Firewall Configuration' ||"
centered_text = text.center(terminal_width)
print(Style.BRIGHT + Fore.CYAN + centered_text, Style.RESET_ALL , "\n")

#Breve spiegazione
text=("In questa attività, verrà condotta una serie di verifiche della configurazione delle regole definite sull'infrastruttura ACME.\n \
• Selezionare il requisito che si vuole testare in maniera singola.\n \
• Esaminare la configurazione del complesso di rete interamente nel suo insieme, e ottenere un report finale sull'Assignment.\n")
centered_text = text.center(terminal_width)
print(Style.BRIGHT + Fore.YELLOW + centered_text, Style.RESET_ALL )

#Crediti
text = "-Corso di 'Practical Network Defense: Dipartimento Informatica, Sapienza Università di Roma' "
right_aligned_text = text.rjust(terminal_width)
print(Style.BRIGHT + Fore.MAGENTA + right_aligned_text, Style.RESET_ALL , "\n")

print("---------------------------------------------------------------------")

json_file = [f for f in os.listdir() if f == "devices.json"]
#pubblicKey_file = [f for f in os.listdir() if f == "SSHKey.pub"]
privateKey_file = [f for f in os.listdir() if f == "SSHKey"]

#SE Device.JSON (non modificabile ricordiamo) non dovesse essere presente fermiamo subito il tutto, ancor prima di arrivare al controllo sull'XML
if not json_file:
    print(Fore.RED+ "-->Il File 'devices.json' NON è presente, si prega di ripristinarlo per avviare il verificatore.", Style.RESET_ALL)
    sys.exit(1)
elif not privateKey_file:
    print(Fore.RED+ "-->La chiave privata per le connessioni SSH passwordless all'ACME, NON è presente, si prega di generarla per avviare il verificatore.", Style.RESET_ALL)


scelta_utente = None
check=False 


cartella_di_lavoro = os.getcwd()

# Ottenere la lista di tutti i file nella cartella di lavoro
files = os.listdir(cartella_di_lavoro)

# Definire il pattern per cercare i file con il formato desiderato
pattern = re.compile(r'^[a-zA-Z]+\.\d{7}\.ovpn$')

# Filtrare i file che corrispondono al pattern
#file_ovpn = [file for file in files if pattern.match(file)]
file_ovpn = [f for f in files if 'alice' not in f.lower() and 'bob' not in f.lower()]

openvpn_config_path = file_ovpn[0]
config_name = openvpn_config_path.split('.')[0]


if(start_vpn_connection(openvpn_config_path)!=None):
    #Ai nostri scopi (in realtà solo uno, ossia il NAT) è sufficente il backup file del Main-FW
    print("-->",Fore.GREEN+"Connessione VPN avvenuta con successo.",Style.RESET_ALL)
    check=inizialization_XML_file("100.100.0.2", "/main_firewall.xml")



if(check):
    
    import Requisito_1, Requisito_2, Requisito_3, Requisito_4, Requisito_5, Requisito_6, Requisito_7, Requisito_8, Requisito_9, Requisito_10, Requisito_11, Requisito_12, Requisito_13
    
    
    # Dizionario delle funzioni da eseguire
    menu = {
        '1': [Requisito_1.Main_code, "Risultato Requisito 1: 'All hosts must use the internal DNS Server as a DNS resolver'."],
        '2': [Requisito_2.Main_code, "Risultato Requisito 2: 'The webserver service provided in the DMZ has to be accessible from the Internet'."],
        '3': [Requisito_3.Main_code, "Risultato Requisito 3: 'The proxy service provided in the DMZ has to be accessible only from the hosts of the Acme network'."],
        '4': [Requisito_4.Main_code, "Risultato Requisito 4: 'Beside the DNS resolver, the other services in the Internal server network have to be accessible only by hosts of Client and DMZ networks.'"],
        '5': [Requisito_5.Main_code, "Risultato Requisito 5: 'All the hosts (but the Client network hosts) have to use the syslog and the log collector services on the Log server (syslog) and on Graylog server.'"],
        '6': [Requisito_6.Main_code, "Risultato Requisito 6: 'The Greenbone server has to access all the hosts of the network.'"],
        '7': [Requisito_7.Main_code, "Risultato Requisito 7: 'All network hosts have to be managed via ssh only from hosts within the Client network.'"],
        '8': [Requisito_8.Main_code, "Risultato Requisito 8: 'All the Client network hosts have only access to external web services.'"],
        '9': [Requisito_9.Main_code, "Risultato Requisito 9: 'Any packet received by the Main Firewall on port 65432 should be redirected to port 80 of the Proxy host.'"],
        '10': [Requisito_10.Main_code, "Risultato Requisito 10: 'All the hosts of the ACME network should be able to ping (and receive replies of) the other hosts and the Internet hosts.'"],
        '11': [Requisito_11.Main_code, "Risultato Requisito 11: 'All the internal hosts should use the public IP address of the Main Firewall to exit towards the Internet.'"],
        '12': [Requisito_12.Main_code, "Risultato Requisito 12: 'The rate of ICMP echo request packets should be limited.'"],
        '13': [Requisito_13.Main_code, "Risultato Requisito 13: 'Only hosts in the DMZ should be reachable using the ping and traceroute tools.'"]
    }


#Prova_Requisito_3.Main_code()


  
check_req1 = check_req2 = check_req3 = check_req4 = check_req5 = check_req6 = check_req7 = check_req8 = check_req9 = check_req10 = check_req11 = check_req12 = check_req13 = ''
launch_all= False


# Verifica se sono stati passati argomenti (lanciamo tutti i controlli a catena senza il menù)
if (len(sys.argv) > 1):
    # Converti gli argomenti a stringhe minuscole
    lowercase_argv = [arg.lower() for arg in sys.argv]
    
    if any('all' in x for x in lowercase_argv):
        if not any('launcher' in x for x in lowercase_argv):

            launch_all = True

        #Verifica se è stato lanciato dal "launcher"
        else:
  
            # Ottieni l'argomento JSON dal comando di lancio
            parametri_json = sys.argv[1]
            
            # Decodifica la stringa JSON in un dizionario
            parametri = json.loads(parametri_json)
            
            output_filename = parametri.get("Nome_File", "")
            
            # Verifica se il valore di "All" è True nel dizionario
            if parametri.get("All", False):
    

                launch_all = True

# Ottieni il percorso completo del file di output
output_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), output_filename)

#print(output_path, "\n")

# Apri il file di output in modalità "write" ("w")
with open(output_path, "w") as file:
    # Salva il riferimento a sys.stdout originale
    original_stdout = sys.stdout
    
    # Redirect dell'output dei print verso il file
    sys.stdout = file
    
    # Stampa nel file
    print("|| REPORT-GRADER 'ASSIGNMENT 2: Firewall Configuration' || \n")
    
    # Ripristina sys.stdout alla sua condizione originale
    sys.stdout = original_stdout    
    

if(check):
    if(launch_all == False):
        while True:
            
            print(Style.BRIGHT + Fore.MAGENTA +"REQUISITI DA TESTARE: \n",Style.RESET_ALL)
            print(Style.BRIGHT + Fore.YELLOW+"1) "+Style.RESET_ALL+"'Tutti gli host devono utilizzare l'internal DNS Server come risolutore DNS'", Fore.YELLOW + check_req1, Style.RESET_ALL)
            print(Style.BRIGHT + Fore.YELLOW+"2) "+Style.RESET_ALL+"'Il servizio web del DMZ deve essere accessibile da Internet'", Fore.YELLOW + check_req2, Style.RESET_ALL)
            print(Style.BRIGHT + Fore.YELLOW+"3) "+Style.RESET_ALL+"'Il servizio proxy nel DMZ, deve essere accessibile dagli host della rete ACME'", Fore.YELLOW + check_req3, Style.RESET_ALL)
            print(Style.BRIGHT + Fore.YELLOW+"4) "+Style.RESET_ALL+"'A parte il DNS, i servizi nella rete interna devono essere accessibili solo dagli host delle reti Client e DMZ'", Fore.YELLOW + check_req4, Style.RESET_ALL)
            print(Style.BRIGHT + Fore.YELLOW+"5) "+Style.RESET_ALL+"'Gli host dell'ACME', meno quelli della rete client, devono utilizzare i servizi sul Log Server e Graylog Server'", Fore.YELLOW + check_req5, Style.RESET_ALL)
            print(Style.BRIGHT + Fore.YELLOW+"6) "+Style.RESET_ALL+"'Il server Greenbone deve avere accesso a tutti gli host dell'ACME'", Fore.YELLOW + check_req6, Style.RESET_ALL)
            print(Style.BRIGHT + Fore.YELLOW+"7) "+Style.RESET_ALL+"'Tutti gli host di rete devono essere gestiti tramite SSH, solo dagli host nella rete Client'", Fore.YELLOW + check_req7, Style.RESET_ALL)
            print(Style.BRIGHT + Fore.YELLOW+"8) "+Style.RESET_ALL+"'Gli host nella rete Client possono accedere solo ai servizi web esterni (HTTP)'", Fore.YELLOW + check_req8, Style.RESET_ALL)
            print(Style.BRIGHT + Fore.YELLOW+"9) "+Style.RESET_ALL+"'I pacchetti ricevuti dal Main Firewall sulla porta 65432, devono essere reindirizzati alla porta 80 del Proxy.'", Fore.YELLOW + check_req9, Style.RESET_ALL)
            print(Style.BRIGHT + Fore.YELLOW+"10) "+Style.RESET_ALL+"'Gli Host della rete ACME, devono riuscire a contattarsi tramite Ping.'", Fore.YELLOW + check_req10, Style.RESET_ALL)
            print(Style.BRIGHT + Fore.YELLOW+"11) "+Style.RESET_ALL+"'Tutti gli host interni, devono utilizzare l'indirizzo IP pubblico del Main Firewall per accedere a Internet'", Fore.YELLOW + check_req11, Style.RESET_ALL)
            print(Style.BRIGHT + Fore.YELLOW+"12) "+Style.RESET_ALL+"'Il Redirect dei pacchetti ICMP deve essere limitato.'", Fore.YELLOW + check_req12, Style.RESET_ALL)
            print(Style.BRIGHT + Fore.YELLOW+"13) "+Style.RESET_ALL+"'Solo la rete DMZ deve essere raggiungibile dall'esterno tramite Ping.'", Fore.YELLOW + check_req13, Style.RESET_ALL)
            
            print("")
            print(Style.BRIGHT + Fore.CYAN+ "-- report (ottieni un responso finale sull'Assignment')", Style.RESET_ALL)
            print(Style.BRIGHT + Fore.CYAN+ "-- all (lancia tutti i test non ancora verificati)", Style.RESET_ALL)
            print(Style.BRIGHT + Fore.CYAN+ "-- esc (esci dal programma)  \n", Style.RESET_ALL)
        
            scelta_utente = input("*) Seleziona un'opzione: ")
            
            if scelta_utente in menu.keys():
                clear_console()
                if scelta_utente == '1':
                    # Esegue la funzione associata all'opzione selezionata
                    check_req1= menu['1'][0]()
                    messaggio= menu['1'][1]
                    del menu['1']
                    success_array.append(check_req1)
                    update_result_log(messaggio, check_req1)
                    
                elif scelta_utente == '2':
                    # Esegue la funzione associata all'opzione selezionata
                    check_req2= menu['2'][0]()
                    messaggio= menu['2'][1]
                    del menu['2']
                    success_array.append(check_req2)
                    update_result_log(messaggio, check_req2)
    
                elif scelta_utente == '3':
                    # Esegue la funzione associata all'opzione selezionata
                    check_req3= menu['3'][0]()
                    messaggio= menu['3'][1]
                    del menu['3']
                    success_array.append(check_req3)
                    update_result_log(messaggio, check_req3)
                
                elif scelta_utente == '4':
                    # Esegue la funzione associata all'opzione selezionata
                    check_req4= menu['4'][0]()
                    messaggio= menu['4'][1]
                    del menu['4']
                    success_array.append(check_req4)
                    update_result_log(messaggio, check_req4)
                
                elif scelta_utente == '5':
                    # Esegue la funzione associata all'opzione selezionata
                    check_req5= menu['5'][0]()
                    messaggio= menu['5'][1]
                    del menu['5']
                    success_array.append(check_req5)
                    update_result_log(messaggio, check_req5)
                
                elif scelta_utente == '6':
                    # Esegue la funzione associata all'opzione selezionata
                    check_req6= menu['6'][0]()
                    messaggio= menu['6'][1]
                    del menu['6']
                    success_array.append(check_req6)
                    update_result_log(messaggio, check_req6)
                    
                elif scelta_utente == '7':
                    # Esegue la funzione associata all'opzione selezionata
                    check_req7= menu['7'][0]()
                    messaggio= menu['7'][1]
                    del menu['7']
                    success_array.append(check_req7)
                    update_result_log(messaggio, check_req7)
                
                elif scelta_utente == '8':
                    # Esegue la funzione associata all'opzione selezionata
                    check_req8= menu['8'][0]()
                    messaggio= menu['8'][1]
                    del menu['8']
                    success_array.append(check_req8)
                    update_result_log(messaggio, check_req8)
                
                elif scelta_utente == '9':
                    # Esegue la funzione associata all'opzione selezionata
                    check_req9= menu['9'][0]()
                    messaggio= menu['9'][1]
                    del menu['9']
                    success_array.append(check_req9)
                    update_result_log(messaggio, check_req9)
                
                elif scelta_utente == '10':
                    # Esegue la funzione associata all'opzione selezionata
                    check_req10= menu['10'][0]()
                    messaggio= menu['10'][1]
                    del menu['10']
                    success_array.append(check_req10)
                    update_result_log(messaggio, check_req10)
                
                elif scelta_utente == '11':
                    # Esegue la funzione associata all'opzione selezionata
                    check_req11= menu['11'][0]()
                    messaggio= menu['11'][1]
                    del menu['11']
                    success_array.append(check_req11)
                    update_result_log(messaggio, check_req11)
                
                elif scelta_utente == '12':
                    # Esegue la funzione associata all'opzione selezionata
                    check_req12= menu['12'][0]()
                    messaggio= menu['12'][1]
                    del menu['12']
                    success_array.append(check_req12)
                    update_result_log(messaggio, check_req12)
                
                elif scelta_utente == '13':
                    # Esegue la funzione associata all'opzione selezionata
                    check_req13= menu['13'][0]()
                    messaggio= menu['13'][1]
                    del menu['13']
                    success_array.append(check_req13)
                    update_result_log(messaggio, check_req13)
                    
                
                print("")
                input("Premi INVIO, per continuare...\n")
                clear_console()
                print("---------------------------------------------------------------------")
                
            elif 'esc' in scelta_utente:
                print("")
                break
            
            elif 'all' in scelta_utente:
                execute_all()
                final_report()
                break
            
            elif 'report' in scelta_utente:
                if(len(menu)==0):
                    final_report()
                    break
                else:
                    messagebox.showinfo("Attenzione!", "Opzione non ancora selezionabile, verificare prima tutti i requisiti.", icon='warning')
                    clear_console()
                    print("---------------------------------------------------------------------")
            else:
                
                messagebox.showinfo("Attenzione!", "Opzione non valida, o requisito scelto già verificato.", icon='warning')
                clear_console()
                print("---------------------------------------------------------------------")
    
    else:
        
        print(Style.BRIGHT + Fore.MAGENTA +"PROCEDIAMO SUBITO CON TUTTI I TEST A CATENA...",Style.RESET_ALL)
        time.sleep(3)
        
        #Puliamo la console
        if os.name == 'nt':  # Windows
            os.system('cls')

        else:  # Unix-based systems (Linux, macOS)
            os.system('clear')
        
        execute_all()
        final_report()

else:
    with open(output_filename, "a") as file:
        file.write("- Errore durante la connessione SSH al Firewall principale, chiave errata o non configurata sul Firewall o accesso disabilitato per la connessione SSH")
          
clear_process()
time.sleep(1)
[os.remove(file) for file in os.listdir() if file.endswith('.txt') and 'result' not in file]
