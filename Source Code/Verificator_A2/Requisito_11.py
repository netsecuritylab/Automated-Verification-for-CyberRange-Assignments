import xml.etree.ElementTree as ET
import Rules_Utils
import paramiko
from colorama import Fore, Style


# Carica il file XML
tree = ET.parse("main_firewall.xml")
root = tree.getroot()

MFW_interfaces_ip_dict = {} # Dizionario per memorizzare le interfacce del Main FW
alias_dict_MFW = {}  # Dizionario per memorizzare gli alias del Main FW




# Funzione ricorsiva per trovare le regole
def find_rules(element):
    rules = []
    for child in element:
        if child.tag == 'rule' and 'interface' in [sub.tag for sub in child]:
            interface_element = child.find('interface')
            
            #Cerchiamo tutte le regole che contattano l'intercaiia WAN dentro <nat> e che hanno sorgente e destinazione qualsiasi
            #Anche Destination deve essere un 'any' altrimenti limiteremo la regola e il "natting" solo a parti specifiche.
            if 'wan' in interface_element.text:
                
                source_elements = child.findall('.//source')
                for source_element in source_elements:
                    if 'any' in ET.tostring(source_element).decode():
                        
                        destination_elements = child.findall('.//destination')
                        for destination_element in destination_elements:
                            if 'any' in ET.tostring(destination_element).decode():
                                rules.append(child)
                                break
                    
        rules += find_rules(child)  # Richiama la funzione ricorsivamente
    return rules




check=False

interfaces_ip_dict = Rules_Utils.make_interface_dict("main_firewall.xml")
alias_dict = Rules_Utils.make_alias_dict("main_firewall.xml")
regola=''


# Trova le regole sotto il tag <nat> in modo ricorsivo
nat_rules = find_rules(root.find('nat'))

# Stampa le regole trovate sulle NAT con source e destination ANY definite sull'interfaccia WAN del MFW
for rule in nat_rules:
    #ET.dump(rule)
    targetip_subnet_element = rule.find('.//targetip_subnet')
    target_subnet_element = rule.find('.//target')
    
    #Analisi tag <targetip_subnet>
    if targetip_subnet_element is not None:
        targetip = targetip_subnet_element.text
        if(targetip == ('0')): #vuol dire che è stato selezionato come "indirizzo di target" la network associata all'interfaccia...ossia la network di wan.
            if('100.100.0.0/24' in interfaces_ip_dict.get('wan')):
                regola=rule
                check=True
                break
    
    #Analisi tag <target>
    elif target_subnet_element is not None:
        target=target_subnet_element.text
        
        #Se abbiamo già un IP settato come parametro sorgente, ed è proprio quello che stiamo cercando lancia il break
        if(target == '100.100.0.0/24'):
            regola=rule
            check=True
            break
        
        #Controlliamo sugli Alias il NAT effettuato
        elif (target in alias_dict.keys()):
            
            if (alias_dict[target]) == '100.100.0.0/24':
                regola=rule
                check=True
                break
         
            #Controlliamo sulle interfacce il NAT effettuato
        elif (target in interfaces_ip_dict.keys()):
            
            #if (interfaces_ip_dict[target.text]) == '100.100.0.0/24':
            if (interfaces_ip_dict[target]) == '100.100.0.0/24':
                regola=rule
                check=True
                break


def Main_code():
    # Creazione dell'oggetto per la connessione SSH
    ssh_client = paramiko.SSHClient()
    ssh_client.load_system_host_keys()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    check_req11=''
    
    print("---------------------------------------------------------------------")
    print(Style.BRIGHT + Fore.YELLOW + "Verifica del requisito 11: \n", Style.RESET_ALL)  
    print(Style.BRIGHT +"[Verifica preliminare della regola di NAT che redirige il traffico verso Internet con il Public IP del Main-Firewall, ed effettivo test di connettività verso la rete pubblica] \n", Style.RESET_ALL)

        
    ssh_client.connect(hostname='100.100.6.3', username="root", key_filename="SSHKey")
    
    
    # Comando da eseguire sul server remoto selezionato nel comando
    #comando = "wget -O /dev/null 2>&1 http://github.com"
    comando = "wget -T 3 --tries=1 -O /dev/null 2>&1 http://100.100.4.10"
    
    # Eseguire la richiesta HTTPS utilizzando il modulo requests
    stdin, stdout, stderr = ssh_client.exec_command(comando)
    
    # Lettura dell'output del comando
    output = stdout.read().decode('utf-8')
    
    # Chiusura della connessione SSH
    ssh_client.close()
    
    #IF di appoggio nel caso non ci sia nessuna regola che rispetta il requisito o che sia disabilitata
    if (check == True):
       
        disabled = regola.find('disabled')
        
        #Ovviamente la regola deve NON essere disabilitata (qui le rule è solo enable o disable quando si parla di NAT)
        if (disabled is None or disabled == -1):
            print(Style.BRIGHT + Fore.GREEN +'* NAT rule trovata e abilitata.', Style.RESET_ALL)
            check_req11="-->SUCCESS!"
            
            
            # Verifica se la richiesta verso internet (dal Proxy) ha avuto successo
            if "connected" in output:
                print("- Inoltre la richiesta verso la rete pubblica, ha avuto "+Style.BRIGHT + Fore.GREEN +"successo. \n", Style.RESET_ALL)
                print(Style.BRIGHT + Fore.GREEN +"--> REQUISITO SODDISFATTO!", Style.RESET_ALL)
                  
            else:
                print("- Ma la richiesta verso la rete pubblica, "+Style.BRIGHT + Fore.YELLOW +"non ha avuto successo. \n",Style.RESET_ALL)
                print(Style.BRIGHT + Fore.GREEN +"--> REQUISITO (DI BASE) COMUNQUE SODDISFATTO!", Style.RESET_ALL)
                
    
        else:
            print("* NAT rule trovata...MA DISABILITATA! \n")
            print(Style.BRIGHT + Fore.RED +"--> REQUISITO NON SODDISFATTO!", Style.RESET_ALL)
            check_req11="-->FAILURE!"
             
    else: 
        print("* RULE NON TROVATA! \n")
        print(Style.BRIGHT + Fore.RED +"--> REQUISITO NON SODDISFATTO!", Style.RESET_ALL)
        check_req11="-->FAILURE!"
    
    print("---------------------------------------------------------------------")
    return check_req11