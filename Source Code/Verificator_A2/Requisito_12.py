from colorama import Fore, Style
import xml.etree.ElementTree as ET


def check_rule(rule):
    # Trova i tag <type>, <protocol> e <icmptype> all'interno della regola
    type_tag = rule.find('type')
    protocol_tag = rule.find('protocol')
    icmptype_tag = rule.find('icmptype')
   
    # Controlla se i tag esistono e hanno i valori specificati      
    if ((type_tag is not None and type_tag.text == 'block') or (type_tag is not None and type_tag.text == 'reject')):
        if(protocol_tag is not None and protocol_tag.text == 'icmp' and
           icmptype_tag is not None and icmptype_tag.text == 'redir'):
            return True
    
    return False


def analyze_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    check_req12=""
    
    # Cerca ricorsivamente tra tutti i tag <rule> e <rule uuid="x">
    for rule in root.iter('rule'):
        if check_rule(rule):
            
            disabled = rule.find('disabled')
            
            #Ovviamente la regola deve NON essere disabilitata 
            if (disabled is None or disabled == -1):
                print(Style.BRIGHT + Fore.GREEN +'*)' + Style.RESET_ALL + Style.BRIGHT+"Rule trovata e abilitata.", Style.RESET_ALL, "\n")
                print(Style.BRIGHT + Fore.GREEN +"--> REQUISITO SODDISFATTO!", Style.RESET_ALL)
                check_req12="-->SUCCESS!"
                return check_req12
            else:
                print(Style.BRIGHT + Fore.RED +'*)' + Style.RESET_ALL + Style.BRIGHT+"Rule trovata MA Disabilitata.", Style.RESET_ALL , "\n")
                print(Style.BRIGHT + Fore.RED +"--> REQUISITO NON SODDISFATTO!", Style.RESET_ALL)
                check_req12="-->FAILURE!"
                return check_req12
    
    if(check_req12==""):
       print(Style.BRIGHT + Fore.RED +'*)' + Style.RESET_ALL + Style.BRIGHT+"Nessuna Regola Trovata per Soddisfare il Requisito!", Style.RESET_ALL , "\n")
       print(Style.BRIGHT + Fore.RED +"--> REQUISITO NON SODDISFATTO!", Style.RESET_ALL)
       check_req12="-->FAILURE!"
    
    return check_req12


def Main_code():
    check_req12=''
    
    print("---------------------------------------------------------------------")
    print(Style.BRIGHT + Fore.YELLOW + "Verifica del requisito 12: \n", Style.RESET_ALL)  
    print(Style.BRIGHT +"[Verifichiamo il blocco del Redirect ICMP nella rete] \n", Style.RESET_ALL)
    
    check_req12=analyze_xml("main_firewall.xml")
    
    print("---------------------------------------------------------------------")
    return check_req12















