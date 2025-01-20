import socket
from colorama import Fore, Style
import xml.etree.ElementTree as ET
import paramiko
import re
import telnetlib

host = "100.100.0.2"
port = 65432

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(2)  # Imposta un timeout per la connessione, in secondi

#Verifica del redirect sfruttando il contenuto della web page raggiunta dal Main-FW con quella esposta da Fantastic-Coffee
def testing():
    file_path = 'main_firewall.xml'
    
    # Carica e analizza il file XML
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Trova la sezione <nat>
    nat_section = root.find('nat')
    if nat_section is None:
        return False

    # Scandaglia le <rule> nella sezione <nat>
    for rule in nat_section.findall('rule'):
        # Cerca il <target> e il <destination> all'interno di ogni <rule>
        target = rule.find('target')
        destination = rule.find('destination')

        if target is None or destination is None:
            continue
        
        target_text = target.text if target.text else ""
        port = destination.find('port')
        
        
        # Verifica le condizioni specificate
        if (port is not None and port.text == '65432'):
            if ('proxy' in target_text.lower() or target_text == '100.100.6.3'): 
                print(Style.BRIGHT + Fore.GREEN +"*) " +Style.RESET_ALL+ "REGOLA DI NAT: TROVATA E CONFIGURATA!", "\n")
                return True
            else:
                print(Style.BRIGHT + Fore.YELLOW +"*) " +Style.RESET_ALL+ f"REGOLA DI NAT: IMPOSTATA SULLA PORTA 65432 MA TARGET SBAGLIATO--> {target_text}!", "\n")
            


#Verifica delle Porte in ascolto su Proxy...
def check_ssh_and_ss():
    # Connessione SSH
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect('100.100.6.3', username='root', key_filename='SSHKey', timeout=3)
    except paramiko.AuthenticationException as e:
        return
    except paramiko.SSHException as e:
        return
    except socket.timeout:
        return
    except Exception as e:
        return

    # Connessione SSH stabilita, esegui comando ss -tuln
    stdin, stdout, stderr = client.exec_command("ss -tuln")

    # Leggi l'output del comando
    ss_output = stdout.read().decode('utf-8')

    # Chiudi la connessione SSH
    client.close()

    # Verifica se c'è un servizio TCP in LISTEN sulla porta 80
    pattern = r"^tcp\s+LISTEN\s+\d+\s+\d+\s+(?:\*|0.0.0.0|::):80\s+.*$"
    match = re.search(pattern, ss_output, re.MULTILINE)
    if match:
        print("- Servizio TCP in LISTEN sulla porta 80 del Proxy Server.")
        check_telnet()
    else:
        print(Style.BRIGHT + Fore.YELLOW +"- ATTENZIONE: "+Style.RESET_ALL+"Nessun Servizio TCP in LISTEN sulla porta 80 del Proxy Server trovato.")


#...e ORA sul MFW tramite Telnet
def check_telnet():
    
    
    # Impostazioni per la connessione telnet
    host = '100.100.0.2'
    port = 65432
    timeout = 3  # timeout in secondi
    
    try:
        tn = telnetlib.Telnet(host, port, timeout=timeout)
        print("- Servizio TCP in LISTEN sulla porta 65432 del Main-Firewall.", "\n")
        tn.close()
    except ConnectionRefusedError:
       print(Style.BRIGHT + Fore.YELLOW +"- ATTENZIONE: "+Style.RESET_ALL+"Nessun Servizio TCP in LISTEN sulla porta 65432 del Main-Firewall.", "\n")
    except OSError as e:
        print(Style.BRIGHT + Fore.YELLOW +"- ATTENZIONE: "+Style.RESET_ALL+"Nessun Servizio TCP in LISTEN sulla porta 65432 del Main-Firewall.", "\n")






def Main_code():
    #Verifichiamo che la porta 65432 sia effettivamente in ascolto, utilizziamo il Main-FW come host dato che si suppone essere acceso.
    TestCheck=False
    check_req9=''
    
    print("---------------------------------------------------------------------")
    print(Style.BRIGHT + Fore.YELLOW + "Verifica del requisito 9: \n", Style.RESET_ALL)  
    print(Style.BRIGHT +"[Controllo della regola di NAT, e del corretto redirect impostato su essa] \n", Style.RESET_ALL)
    
    TestCheck=testing()
    
    if(TestCheck):
        #Check delle Porte (come controllo aggiuntivo)
        check_ssh_and_ss()
        print("")
        print(Style.BRIGHT + Fore.GREEN +"--> REQUISITO SODDISFATTO!", Style.RESET_ALL)
        check_req9="-->SUCCESS!"   
    else:
        print(Style.BRIGHT + Fore.RED +"*) " +Style.RESET_ALL+ "NESSUNA REGOLA CONGRUA AL REQUISITO!", "\n")
        print(Style.BRIGHT + Fore.RED +"--> REQUISITO NON SODDISFATTO!", Style.RESET_ALL)

    print("---------------------------------------------------------------------")
    return check_req9


    


