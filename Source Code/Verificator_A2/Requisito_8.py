import json
import paramiko
import requests
from colorama import Fore, Style
import subprocess

# Dizionario per memorizzare gli indirizzi IP associati a ciascuna interfaccia dei 2 FW
MFW_interfaces_ip_dict = {}
IFW_interfaces_ip_dict = {}

alias_dict_MFW = {}  # Dizionario per memorizzare gli alias del Main FW
alias_dict_IFW = {}  # Dizionario per memorizzare gli alias dell'internal FW

Test_check = 0


def check_HTTP_Connection():
    Test_check=True    
    # Carica i dati dal file JSON
    with open('devices.json', 'r') as file:
        config = json.load(file)
    
    # Ciclo su ciascun elemento nel file JSON
    for entry in config:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        #Filtriamo sulla Clients Network
        if((entry['IP']).startswith('100.100.2.')):
            try:
                # Connessione SSH
                ssh.connect(entry['IP'], username=entry['User'], key_filename='SSHKey')
                
                # Avvia il server HTTP (ai nostri scopi andrà bene, essendo di base un 'OR' tra le scelte, HTTP/HTTPS, ne basta anche uno)
                http_server_process = subprocess.Popen(["python", "-m", "http.server", "80"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Impostare i dettagli del server HTTP locale
                local_server_url = 'http://localhost:80'
                
                response = requests.get(local_server_url)
                
                if response.status_code == 200:
                    print(f"* La connessione SSH su {entry['IP']}, ha avuto successo e la macchina remota può raggiungere il server HTTP LOCALE. \n")
                else:
                    print(f"* La connessione SSH su {entry['IP']}, è riuscita, ma il server HTTP locale ha restituito una risposta diversa da 200. \n")
                    Test_check = False
                    break
                # Termina il processo del server HTTP
                http_server_process.terminate()
                
                # Attendere che il processo termini completamente
                http_server_process.wait()
                
                
            except paramiko.AuthenticationException:
                print(f"Errore di autenticazione per {entry['IP']}. \n")
                Test_check = False
                break
            except paramiko.SSHException:
                print(f"Errore durante la connessione SSH a {entry['IP']}. \n")
                Test_check = False
                break
            except Exception as e:
                print(f"Errore sconosciuto per {entry['IP']}: {str(e)} \n")
                Test_check = False
                break
            finally:
                ssh.close()
    
    #Se ogni singolo test va a buon fine, allora abbiamo non solo verificato la presenza della o delle regole ma anche la connettività
    if(Test_check != False):
        print(Style.BRIGHT + Fore.GREEN +"--> REQUISITO SODDISFATTO!", Style.RESET_ALL)
        return True
    else:
        print(Style.BRIGHT + Fore.RED +"--> REQUISITO NON SODDISFATTO!", Style.RESET_ALL)
        return False



def Main_code():

    check_req8=''
    print("---------------------------------------------------------------------")
    print(Style.BRIGHT + Fore.YELLOW + "Verifica del requisito 8: \n", Style.RESET_ALL)   
    print(Style.BRIGHT +"[Test di accesso al servizio HTTP della macchina locale, da parte degli host della rete client (100.100.2.0/24)'] \n", Style.RESET_ALL)

    if(check_HTTP_Connection()):
        check_req8="-->SUCCESS!"  
       
        
    else:
        testo = """
        *Possibili cause:
            -Regola assente nella configurazione del o di uno dei due Firewall. 
            -Regola configurata in un interfaccia del Firewall, non idonea al requisito.
            -Regola mal configurate rispetto ai criteri richiesti dal requisito.
            -Errore generici di rete o connettività VPN.
        """
        print(testo)
        check_req8="-->FAILURE!"
    print("---------------------------------------------------------------------")
    return check_req8