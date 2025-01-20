import subprocess
import json
from colorama import Fore, Style
import paramiko


def Main_code():
    Test_check = True
    
    check_req6=''
    print("---------------------------------------------------------------------")
    print(Style.BRIGHT + Fore.YELLOW + "Verifica del requisito 6: \n", Style.RESET_ALL)
    print(Style.BRIGHT +"[Controllo di accessibilità e gestione del server Greenbone, verso tutti gli host della rete ACME] \n", Style.RESET_ALL)

    # Leggi il file JSON dei dispositivi
    with open('devices.json') as file:
        devices = json.load(file)
    
    # Nuovi dizionari da aggiungere
    new_devices = [
        {'IP': '100.100.0.2', 'Name': 'Main-Firewall'},
        {'IP': '100.100.254.2', 'Name': 'Internal-Firewall'}
    ]
    
    # Aggiungi i nuovi dizionari al dizionario esistente
    devices.extend(new_devices)
 
    # Esegui il ping su ciascun indirizzo IP dei dispositivi
    for device in devices:
        ip = device.get('IP')
        name= device.get('Name')
        
        #Password per l'accesso in SSH al Greenbone
        password_greenbone = "Passw0rd.1"
        #password_greenbone = device.get('Password') #-->Tanto la password è uguale per tutti

        # Creazione di un oggetto SSHClient
        client = paramiko.SSHClient()

        # Impostazione della policy di default per accettare la chiave dell'host
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Connessione SSH con inserimento della password
            client.connect('100.100.1.4', username='root', key_filename='SSHKey', timeout=3)

            # Esecuzione del comando ping remoto
            stdin, stdout, stderr = client.exec_command(f'ping -c 2 -w 2 {ip}')

            # Leggi l'output del comando
            output = stdout.read().decode()

            if "0% packet loss" in output:
                print("* La connessione del "+Style.BRIGHT + Fore.CYAN+ "Greenbone," +Style.RESET_ALL+ " verso"+Style.BRIGHT + Fore.CYAN+ f" '{name}'"+Style.RESET_ALL+" ha avuto "+Style.BRIGHT + Fore.GREEN+"successo!"+Style.RESET_ALL)
                #print(output)
            else:
                print("* La connessione del "+Style.BRIGHT + Fore.CYAN+ "Greenbone," +Style.RESET_ALL+ " verso"+Style.BRIGHT + Fore.CYAN+ f" '{name}'" +Style.BRIGHT + Fore.RED +" NON ha avuto successo!" +Style.RESET_ALL)
                Test_check = False
                break
                #print(output)

        except Exception as e:
            print("Errore durante la connessione SSH:", str(e))
            Test_check = False
            break

        finally:
            # Chiudi la connessione SSH
            client.close()
            
                 
                
        
            
    
    print("")
    if(Test_check):
        print(Style.BRIGHT + Fore.GREEN +"--> REQUISITO SODDISFATTO!", Style.RESET_ALL)
        check_req6="-->SUCCESS!"
    else:
        print(Style.BRIGHT + Fore.RED +"--> REQUISITO NON SODDISFATTO!", Style.RESET_ALL)
        check_req6="-->FAILURE!"
    
    print("---------------------------------------------------------------------")
    return check_req6






