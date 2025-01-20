import subprocess
import json
import random
from ipaddress import IPv4Network, IPv4Address
from colorama import Fore, Style


def ping_ip(ip_address):
    # Esegui il ping verso l'indirizzo IP e restituisci True se ha successo, False altrimenti
    result = subprocess.run(['ping', '-n', '1', '-w', '1000', ip_address],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.returncode == 0

def check_subnet_ping(devices, subnet):
    # Filtra gli IP nella subnet specificata
    subnet_ips = [device['IP'] for device in devices if IPv4Address(device['IP']) in subnet]
    
    # Esegui il ping per ogni IP nella subnet
    subnet_results = [ping_ip(ip) for ip in subnet_ips]
    
    # Restituisci True se tutti i ping hanno avuto successo, False altrimenti
    subnet_success = all(subnet_results)
    
    if(subnet_success):
        print(Style.BRIGHT + Fore.GREEN +"*)Check: "+Style.RESET_ALL+"Gli Host della rete DMZ, sono stati raggiunti tramite Ping con successo!", "\n")
    
    return subnet_success

def check_non_subnet_ping(devices, subnet):
    # Filtra gli IP che non sono nella subnet specificata
    non_subnet_ips = [device['IP'] for device in devices if IPv4Address(device['IP']) not in subnet]
    
    # Seleziona un IP randomico dalla lista degli IP non subnet
    random_ip = random.choice(non_subnet_ips)
    
    # Esegui il ping verso l'IP randomico selezionato
    result = ping_ip(random_ip)
    
    if(result):
        print(Style.BRIGHT + Fore.YELLOW +"*)Contro-Check: "+Style.RESET_ALL+"Altri Host fuori dalla rete DMZ, sono stati raggiunti tramite Ping con successo!", "\n")
    else:
        print(Style.BRIGHT + Fore.CYAN +"*)Contro-Check: "+Style.RESET_ALL+"Nessun Host fuori dalla DMZ, è stato raggiunti tramite Ping con successo!", "\n")
    
    # Restituisci True se il ping ha fallito, False se ha avuto successo
    return not result




def Main_code():
    
    print("---------------------------------------------------------------------")
    print(Style.BRIGHT + Fore.YELLOW + "Verifica del requisito 13: \n", Style.RESET_ALL)  
    print(Style.BRIGHT +"[Controllo del Raggiungimento tramite Ping, dall'esterno dell'ACME, della sola rete DMZ] \n", Style.RESET_ALL)
    
    # Definizione della subnet da controllare
    subnet_to_check = IPv4Network('100.100.6.0/24')
    
    # Caricamento dei dati dal file JSON
    with open('devices.json', 'r') as f:
        devices = json.load(f)
    
    # Verifica dei ping per la subnet specificata
    subnet_ping_result = check_subnet_ping(devices, subnet_to_check)
    
    # Verifica dei ping per un IP randomico fuori dalla subnet
    non_subnet_ping_result = check_non_subnet_ping(devices, subnet_to_check)
    
    check_req13=''
    
    # Stampare il risultato
    if subnet_ping_result and non_subnet_ping_result:
        print(Style.BRIGHT + Fore.GREEN +"--> REQUISITO SODDISFATTO!", Style.RESET_ALL)
        check_req13="-->SUCCESS!"
    else:
        print(Style.BRIGHT + Fore.RED +"--> REQUISITO NON SODDISFATTO!", Style.RESET_ALL)
        check_req13="-->FAILURE!"
    
    print("---------------------------------------------------------------------")
    return check_req13



