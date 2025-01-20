import json
import paramiko
import subprocess
from colorama import Fore, Style, init

# Inizializza colorama
init(autoreset=True)

# Funzione per eseguire il ping e verificare la connettività
def ping_from_host(client, src_host, dest_host_ip, dest_host_name):
    command = f"ping -c 1 -W 1 {dest_host_ip}"
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    
    if exit_status != 0:
        print(Style.BRIGHT +f"{Fore.YELLOW}  !! {src_host['Name']} ({src_host['IP']}) non può pingare {dest_host_name} ({dest_host_ip})")
    return exit_status == 0

# Funzione per connettersi via SSH e eseguire il ping
def ssh_and_ping(host, hosts):
    try:
        # Connessione SSH
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host['IP'], username=host['User'], key_filename='SSHKey', timeout=3)

        all_pings_successful = True

        # Esegui il ping agli altri host
        for dest_host in hosts:
            if host != dest_host:
                if not ping_from_host(client, host, dest_host['IP'], dest_host['Name']):
                    all_pings_successful = False

        # Chiudi la connessione SSH
        client.close()

        return all_pings_successful

    except paramiko.AuthenticationException as e:
        print(Style.BRIGHT +f"{Fore.RED}Errore di autenticazione SSH per {host['Name']} ({host['IP']}): {e}")
        return False
    except paramiko.SSHException as e:
        print(Style.BRIGHT +f"{Fore.RED}Errore SSH per {host['Name']} ({host['IP']}): {e}")
        return False
    except Exception as e:
        print(Style.BRIGHT +f"{Fore.RED}Errore durante la connessione SSH per {host['Name']} ({host['IP']}): {e}")
        return False


def Main_code():
    
    check_req10=''
    print("---------------------------------------------------------------------")
    print(Style.BRIGHT + Fore.YELLOW + "Verifica del requisito 10: \n", Style.RESET_ALL)  
    print(Style.BRIGHT +"[Procediamo con una verifica dell'effettiva connettività tra gli Host dell'ACME tramite Ping] \n", Style.RESET_ALL)
    
    # Carica i dati degli host dal file JSON
    try:
        with open('devices.json', 'r') as json_file:
            hosts = json.load(json_file)

        all_hosts_connected = True
        # Loop su ogni host e verifica connessione SSH e ping
        for host in hosts:
            print(Style.BRIGHT +f"{Fore.CYAN}*) Connessione SSH a {host['Name']} ({host['IP']})...{Style.RESET_ALL}")
            if ssh_and_ping(host, hosts):
                print(Style.BRIGHT +f"{Fore.WHITE}Connessione SSH e ping verso l'ACME da {host['Name']} ({host['IP']}) {Fore.GREEN}verificati{Fore.WHITE} con successo.{Style.RESET_ALL}", "\n")
            else:
                print(Fore.WHITE + Style.BRIGHT +"Errore durante la connessione SSH o al più un ping "+Fore.RED+"fallito"+Style.RESET_ALL+Style.BRIGHT+f" da {host['Name']} ({host['IP']}).{Style.RESET_ALL}","\n")
                all_hosts_connected = False
                break

        if all_hosts_connected:
            print(Style.BRIGHT + Fore.GREEN +"--> REQUISITO SODDISFATTO!", Style.RESET_ALL)
            check_req10="-->SUCCESS!" 
        else:
            print(Style.BRIGHT + Fore.RED +"--> REQUISITO NON SODDISFATTO!", Style.RESET_ALL)
            check_req10="-->FAILURE!"
        
    except FileNotFoundError:
        print(f"{Fore.RED}File devices.json non trovato.{Style.RESET_ALL}")
        check_req10="-->FAILURE!"
    except json.JSONDecodeError as e:
        print(f"{Fore.RED}Errore nel parsing del file JSON: {e}{Style.RESET_ALL}")
        check_req10="-->FAILURE!"
    
    print("---------------------------------------------------------------------")
    return check_req10