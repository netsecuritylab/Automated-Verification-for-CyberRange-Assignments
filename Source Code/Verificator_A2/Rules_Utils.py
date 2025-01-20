import xml.etree.ElementTree as ET
import re
import ipaddress
import paramiko
import json
import random
from colorama import Fore, Style


def make_interface_dict(name_XML):
    interfaces_ip_dict = {}
    
    # Parsing del file XML
    tree = ET.parse(name_XML)
    #tree = ET.parse("internal_firewall.xml")
    root = tree.getroot()
    
    # Iterazione attraverso gli elementi di tipo interfaccia nel file XML
    for interface in root.findall(".//interfaces/*"):
  
        parola_match = re.search(r"'([^']+)'", str(interface))
        interfaccia = parola_match.group(1)
        
        if(interface.find("ipaddr") is not None and interface.find("subnet") is not None):
            prefisso_subnet = interface.find("subnet").text
            
            #Indirizzo IP dell'interfaccia di riferimento
            indirizzo_ip= interface.find("ipaddr").text
            indirizzo_network = ipaddress.IPv4Network(f"{indirizzo_ip}/{prefisso_subnet}", strict=False)
            indirizzo_interfacia = (f"{indirizzo_ip}/{prefisso_subnet}")
            
            # Aggiunta della subnet IP al dizionario
            interfaces_ip_dict[interfaccia] = [str(indirizzo_network), interface.find("descr").text]
            interfaces_ip_dict[interfaccia+"ip"] = [indirizzo_interfacia, interface.find("descr").text]
    return interfaces_ip_dict


def make_alias_dict(name_XML):
    alias_dict = {}
    # Parsing del file XML
    tree = ET.parse(name_XML)
    #tree = ET.parse("internal_firewall.xml")
    root = tree.getroot()
    
    
    # Itera su tutti gli alias nel file XML e ti costruisci un dizionario: [Alias, Subnet/IP]
    for alias in root.findall('.//alias'):
        alias_name = alias.find('name')
        alias_content = alias.find('content')
        if alias_name is not None and alias_content is not None:
            alias_name_text = alias_name.text
            alias_content_text = alias_content.text.split('\n')  # Prendi sia gli indirizzi IPv4 che IPv6 se definiti
            
            for input_str in alias_content_text:
                    try:
                        ipaddress.IPv4Network(input_str, strict=False) #Qui invece ci prendiamo solo l'indirizzo IPv4
                        alias_dict[alias_name_text] = input_str
                        break
                    except ValueError:
                        pass
    
    return alias_dict




def print_Dict_FW(MFW_interfaces_ip_dict, alias_dict_MFW, IFW_interfaces_ip_dict, alias_dict_IFW):
    # Stampa dei dizionari delle Interfacce e degli Alias configurati sui due FW
    for interface, values in MFW_interfaces_ip_dict.items():
        print(f"{interface} -> {values}")

    print("----------------------------------------")

    # Stampa del risultato
    for interface, values in alias_dict_MFW.items():
        print(f"{interface} -> {values}")

    print("----------------------------------------")


    for interface, values in IFW_interfaces_ip_dict.items():
        print(f"{interface} -> {values}")

    print("----------------------------------------")


    # Stampa del risultato
    for interface, values in alias_dict_IFW.items():
        print(f"{interface} -> {values}")

    print("----------------------------------------")
    
    




def check_FW_Rules(FW, excepted_interface, source_subnet, destination_subnet, DizionarioFW, alias_dict):
    
    # Parsing del file XML
    tree = ET.parse(FW)
    #tree = ET.parse("internal_firewall.xml")
    root = tree.getroot()
    Test_check=0
    
    # Itera su tutte le regole nel file XML
    for rule in root.findall('.//rule'):
        # Trova l'elemento source in ogni regola
        source = rule.find('.//source')
        interface = rule.find('.//interface')
        floating = rule.find('.//floating')
        
        if (source is not None):
            source_value = source.text
            controllo=False
            
            negate_source= source.find('.//not')
            
                
            
            #Se la regola trovata, è configurata sulla floating interface...allora continuiamo coi controlli
            if (floating is not None):
                floating_values= floating.text
                if(floating_values == 'yes'):
                    controllo=True
            
            #Di base può essere tutto implementato tutto nella floating interface, ma laddove ciò non avvenisse ha senso controllare
                #nelle interfacce in cui ha senso che quella eventuale specifica regola che stiamo cercando, debba stare
         
            
            #Se la regola trovata, è configurata su un interfaccia su cui abbia senso trovarla...allora continuiamo coi controlli
            elif(interface is not None):
                interface_value= interface.text
                if(interface_value == excepted_interface):
                    #print(interface_value,excepted_interface)
                    controllo=True
            
            if(("!" in source_subnet)):
                if((negate_source is None)):
                    controllo=False
                else:
                    check_source_subnet=source_subnet[1:]
            else:
                if((negate_source is not None)):
                    controllo=False
                else:
                    check_source_subnet=source_subnet
            
            
            #Se nessuno dei due controlli precedenti passa, scartiamo la regola
            if (controllo):
                #Se abbiamo già un IP settato come parametro sorgente, ed è proprio quello che stiamo cercando lancia il check sulla destinazione (ELSE)
                if source_value != check_source_subnet:
                    #Controlliamo le tipologie di source che può avere questa regola
                    address_alias = source.find('address')
                    address_interface = source.find('network')
                    
                    #print(address_alias, address_interface)
                   
              
                    if(address_alias is not None):
                        #print(address_alias.text, address_alias.text in alias_dict.keys())
                        if (address_alias.text in alias_dict.keys()):
                            #print(address_alias.text, alias_dict[address_alias.text], source_subnet)
                            if (alias_dict[address_alias.text]) == check_source_subnet:
                                 
                                 Test_check+=check_Destination_FW_Rules(FW, rule, destination_subnet, DizionarioFW, alias_dict)
                    
                    elif(address_interface is not None):
                        #print(address_interface.text)
                        chiave= str(address_interface.text)
                        
                        if chiave in DizionarioFW.keys():
                            #print(chiave, DizionarioFW[chiave])
                            if(check_source_subnet in DizionarioFW[chiave]):
                                #print(chiave, "FIEROOOH")
                                Test_check+=check_Destination_FW_Rules(FW, rule, destination_subnet, DizionarioFW, alias_dict)
                else:
                    Test_check=check_Destination_FW_Rules(FW, rule, destination_subnet, DizionarioFW, alias_dict)
    return Test_check



def check_Destination_FW_Rules(FW, rule, destination_subnet, DizionarioFW, alias_dict):
    # Trova l'elemento source in ogni regola
    check=False
    Test_check=0
    source = rule.find('.//destination')
    if source is not None:
        
        source_value = source.text
        
        any_interface = source.find('any')
        
        #Configurata una destinazione come "Any"
        if((any_interface is not None) and (destination_subnet)=="any"):
            check=True 
        
        #Se abbiamo già un IP settato come parametro sorgente, ed è proprio quello che stiamo cercando usciamo diretti (ELSE)
        elif (source_value != destination_subnet):
            #Controlliamo le tipologie di source che può avere questa regola
            address_alias = source.find('address')
            address_interface = source.find('network')
            
            
            #print(address_alias, address_interface)
           
            #Noi ricadiamo necessariamente in uno di questi 3 casi:
            #Configurata una destinazione come Alias
            if(address_alias is not None):
                if (address_alias.text in alias_dict.keys()) and (alias_dict[address_alias.text])== destination_subnet:
                    #print(f'Rule trovata: {rule.find("descr").text}')
                    check=True
            
            #Configurata una destinazione come Interfaccia
            elif(address_interface is not None):
                #print(address_interface.text)
                chiave= str(address_interface.text)
                
                if chiave in DizionarioFW.keys():
                    if(destination_subnet in DizionarioFW[chiave]):
                        #print(f'Rule trovata: {rule.find("descr").text}')
                        check=True

        
        else:
            check=True
    
    if(check):
        rule_type = rule.find('type')
        disabled = rule.find('disabled')
        
        #Ovviamente la regola deve essere di tipo "Pass" oppure NON essere disabilitata
        if(rule_type.text =='pass'):
            if (disabled is None or disabled.text == '0'):
                print(f'Rule trovata: {rule.find("descr").text} -->', FW)
                Test_check+=1
                
            else:
                print(f'Rule trovata: {rule.find("descr").text} -->', FW, ": DISABILITATA!")
                
        else:
            print(f'Rule trovata: {rule.find("descr").text} -->', FW, ": PASSAGING DEI DATI NON CONSENTITO!")
            
    return Test_check



def launch_Ping_Command(IP_to_Ping, host, ssh):
    # Esegui il comando di ping
    ping_command = f'ping -c 1 -W 1 {IP_to_Ping}'
    #process = subprocess.Popen(ping_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    stdin, stdout, stderr = ssh.exec_command(ping_command)
    # Verifica il codice di uscita del comando
    exit_status = stdout.channel.recv_exit_status()
    
    
    if exit_status == 0:
        print(f"* SOURCE: {host} / DESTINATION: {IP_to_Ping}: "+Fore.GREEN +"V", Style.RESET_ALL)
        return True
    else:
        print(f"* SOURCE: {host} / DESTINATION: {IP_to_Ping}: "+Fore.RED +"X", Style.RESET_ALL)
        return False


def check_proxy_server_tunnel(ssh,port):
    # Esegui il comando di curl col Proxy
    command = f'curl -v -k https://github.com --proxy-anyauth -m 3 --proxy 100.100.6.3:{port}'
    
    stdin, stdout, stderr = ssh.exec_command(command)
    
    # Verifica l'output del comando
    output = stderr.read().decode('utf-8')
    
    # Recupera il codice di uscita del comando
    exit_status = stdout.channel.recv_exit_status()
    
    if("200" in output or exit_status==0):
        return True
    
    #Comunque ritorniamo "true" in caso, dato che comunque il proxy ha accolto la richiesta e l'ha inoltrata al webserver interpellato
        #403 è comunque un "errore" lato server.
    elif("403" in output.lower()):
        return True
    else:
        return False


def check_greenbone_connectivity(ssh):
    # Esegui il comando di wget alla pagina esposta dal Greenbone
    command = 'timeout -v 5 wget 100.100.1.4 --connect-timeout=3 --tries=1'
    
    stdin, stdout, stderr = ssh.exec_command(command)
    
    # Verifica l'output del comando
    output = stderr.read().decode('utf-8')
    
    
    if("Connection timed out" in output):
        return False
    else:
        return True

   


def check_Clients_nested_SSH_connection():
    
    count_fail=0
    
    # Caricamento dei dati dal file JSON
    with open('devices.json') as json_file:
        data = json.load(json_file)
    
    # Filtraggio degli host con indirizzo IP che inizia con '100.100.2.'
    filtered_hosts = [host for host in data if host['IP'].startswith('100.100.2.')]
    
    # Connessione SSH ai vari host
    for host in filtered_hosts:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
        try:
            
            ssh.connect(hostname=host['IP'], username=host['User'], key_filename='SSHKey')
            print(Style.BRIGHT +Fore.CYAN +f"*Connesso a {host['Name']} ({host['IP']})", Style.RESET_ALL)
    
            # Selezione casuale di un host diverso per la connessione SSH annidata
            other_hosts = [h for h in data if h['IP'] != host['IP'] and not h['IP'].startswith('100.100.2.')]
            random_hosts = random.sample(other_hosts, 4)
    
            for random_host in random_hosts:
                #print(f'{random_host["User"]}@{random_host["IP"]}')
                
                #Se il comando va a buon fine (e quindi l'SSH annidato non raggiunge il timeout), si stampa un echo di Successo e si raccoglie nella variabile di output
                command = f'timeout 1 ssh -o StrictHostKeyChecking=no -i /home/{host["User"]}/.ssh/SSHKey {random_host["User"]}@{random_host["IP"]} echo "Success"'
                
                stdin, stdout, stderr = ssh.exec_command(command)
                output = stdout.read().decode('utf-8')
                
                #Se il comando va a buon fine e quindi 'Success' è presente nell'output, l'SSH annidato è avvenuto senza problemi.
                if("Success" in output):
                    print("Connessione SSH annidata "+ Style.BRIGHT + Fore.GREEN +"riuscita "+Style.RESET_ALL+f"da {host['Name']} a {random_host['Name']} ({random_host['IP']})")
                else:
                    #print("OUTPUT:",output)
                    #print("ERRORE:",stderr.read().decode('utf-8'), "\n")
                    print("Connessione SSH annidata "+ Style.BRIGHT + Fore.YELLOW +"NON riuscita "+Style.RESET_ALL+f"da {host['Name']} a {random_host['Name']} ({random_host['IP']})")
                    count_fail+=1
                
                
            print("")
        except paramiko.AuthenticationException:
            print(f"Errore di autenticazione per {host['Name']} ({host['IP']}) \n")
            return False
        
        except paramiko.SSHException as e:
            print(f"Errore nella connessione a {host['Name']} ({host['IP']}): {str(e)} \n")
            return False
        
        except Exception as e:
            print(f"Errore sconosciuto nella connessione a {host['Name']} ({host['IP']}): {str(e)} \n")
            return False
        
        finally:
            ssh.close()
    
    
    if(check_Others_SSH_nested_connection("100.100.4.100",3)):
        
        
        #Se non ci siamo connessi a nessuno degli host selezionati randomicamente prima...non è un buon segno.
        if(count_fail==len(random_hosts)):
            print("* Ma la rete client "+ Style.BRIGHT + Fore.RED +"NON è riuscita "+Style.RESET_ALL+"a raggiungere l'intera serie di host selezionati, non possiamo accettare l'esito del test. \n")
            return False
        #Anche fosse uno, lo segnaliamo.
        elif(count_fail>0):
            print(Style.BRIGHT +"* Obbiettivo principale verificato e SUPERATO!" +Style.RESET_ALL , "\n")
            print("* Ma la rete client "+ Style.BRIGHT + Fore.YELLOW +"NON è riuscita "+Style.RESET_ALL+"a raggiungere parte della serie di host selezionati, fare un controllo per sicurezza. \n")
            return True
        else:
            #print(Style.BRIGHT +"* Obbiettivo principale verificato e SUPERATO!" +Style.RESET_ALL , "\n")
            return True
    
    


def check_Others_SSH_nested_connection(origin_host, num_connections):
    # Caricamento dei dati dal file JSON
    with open('devices.json') as json_file:
        data = json.load(json_file)
    
    # Filtraggio degli host con indirizzo IP che inizia con '100.100.2.'
    filtered_hosts = [host for host in data if host['IP'] == origin_host]

    # Connessione SSH ai vari host
    for host in filtered_hosts:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
        try:
            ssh.connect(hostname=host['IP'], username=host['User'], key_filename='SSHKey')
            print(Fore.CYAN +f"*Connesso a {host['Name']} ({host['IP']}) [CONTROPROVA]", Style.RESET_ALL)
    
            # Selezione casuale di un host diverso per la connessione SSH annidata
            other_hosts = [h for h in data if h['IP'] != host['IP']]
            random_hosts = random.sample(other_hosts, num_connections)
    
            for random_host in random_hosts:
                #print(f'{random_host["User"]}@{random_host["IP"]}')
                command = f'timeout 1 ssh -o StrictHostKeyChecking=no -i /home/{host["User"]}/.ssh/SSHKey {random_host["User"]}@{random_host["IP"]}'
                
                stdin, stdout, stderr = ssh.exec_command(command)
                output = stdout.read().decode('utf-8')
                
                #print(output)
                
                if(output):
                    print("Connessione SSH annidata "+ Style.BRIGHT + Fore.GREEN +"riuscita "+Style.RESET_ALL+f"da {host['Name']} a {random_host['Name']} ({random_host['IP']})")
                    return False
                else:
                    print("Connessione SSH annidata "+ Style.BRIGHT + Fore.RED +"NON riuscita "+Style.RESET_ALL+f"da {host['Name']} a {random_host['Name']} ({random_host['IP']})")

            print("")
        except paramiko.AuthenticationException:
            print(f"Errore di autenticazione per {host['Name']} ({host['IP']}) \n")
            return False
        
        except paramiko.SSHException as e:
            print(f"Errore nella connessione a {host['Name']} ({host['IP']}): {str(e)}")
            return False
        
        except Exception as e:
            print(f"Errore sconosciuto nella connessione a {host['Name']} ({host['IP']}): {str(e)}")
            return False
        
        finally:
            ssh.close()
    
    #Se arrivo fin qui vuol dire che tutte le connessioni SSH son "giustamente" fallite da 100.100.4.100.
    return True
    
    
    