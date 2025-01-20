import json
import paramiko
from colorama import Fore, Style
import xml.etree.ElementTree as ET

# Funzione per connettersi tramite SSH e eseguire il comando
def execute_ssh_command(ip, user, ssh_key_path, command):
    
    try:
		
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        private_key = paramiko.RSAKey(filename=ssh_key_path)
        client.connect(ip, username=user, pkey=private_key, timeout=3)

        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode()
        
        client.close()

        return output
    except Exception as e:
        return str(e)
    

#Controlliamo anche se il DNS è configurato sul FW, attraverso il file di configurazione
def check_DNS_in_FW_Configuration(dns_list):
    config_file = 'main_firewall.xml'
    tree = ET.parse(config_file)
    root = tree.getroot()

    for dns_server in root.iter('dnsserver'):
        if dns_server.text in dns_list:
            return True
    return False

    

def Main_code():
    
    check_req1=''
    print("---------------------------------------------------------------------")
    print(Style.BRIGHT + Fore.YELLOW + "Verifica del requisito 1: \n", Style.RESET_ALL)
    print(Style.BRIGHT +"[Controllo DNS risolutore per ogni Host] \n", Style.RESET_ALL)

    # Leggi il file JSON
    with open('devices.json', 'r') as json_file:
        data = json.load(json_file)
    
    count_success=0
    checker=False
    
    possible_DNS = ['100.100.1.2','151.100.4.2','151.100.4.13']
    ssh_key_path = "SSHKey"
    
    
    # Percorri ciascuna voce nel JSON con l'utente TESTER!
    for entry in data:
        ip = entry["IP"]
        user = entry["User"]
        
        
        
        for DNS in possible_DNS:
            #Comando per verificare se 100.100.1.2 è abilitato come risolutore DNS per tutti gli host dell'ACME verso un indirizzo generico
            command = f'host -W 1 -v github.com {DNS}'
            
            # Esegui il comando SSH e ottieni l'output
            output = execute_ssh_command(ip, user, ssh_key_path, command)
			
			
            # Verifica l'output per "Received bytes" e "from 100.100.1.2"
            if (("Received" in output) and (f"from {DNS}" in output)):
                print("* Verifica Internal DNS Server, come risolutore per "+Style.BRIGHT + Fore.CYAN +f"{entry['Name']}"+Style.RESET_ALL+f" / {ip}: "+Style.BRIGHT + Fore.GREEN +"Successo!", Style.RESET_ALL)
                count_success+=1
                checker=True
                break
            
        #Facciamo un ulteriore controllo, questa volta sul file di configurazione, laddove i comandi avessero dato delle problematiche
        if((checker==False)):
            if((check_DNS_in_FW_Configuration(possible_DNS))):
                print("* Verifica Internal DNS Server, come risolutore per "+Style.BRIGHT + Fore.CYAN +f"{entry['Name']}"+Style.RESET_ALL+f" / {ip}: "+Style.BRIGHT + Fore.GREEN +"Successo!", Style.RESET_ALL)
                count_success+=1
                checker=True
        
        if(checker==False):
            print("* Verifica Internal DNS Server, come risolutore per "+Style.BRIGHT + Fore.CYAN +f"{entry['Name']}"+Style.BRIGHT + Fore.RED +", non riuscita, o DNS definito non valido.", Style.RESET_ALL)
        
		#Resettiamo la variabile di controllo prima di passare al prossimo Host da controllare
        checker=False

        
    print("")
    
    if(count_success == len(data)):
        print(Style.BRIGHT + Fore.GREEN +"--> REQUISITO SODDISFATTO!", Style.RESET_ALL)
        check_req1="-->SUCCESS!"
        
    else:
        print(Style.BRIGHT + Fore.RED +"--> REQUISITO NON SODDISFATTO!", Style.RESET_ALL)
        check_req1="-->FAILURE!"

    print("---------------------------------------------------------------------")
    
    return check_req1