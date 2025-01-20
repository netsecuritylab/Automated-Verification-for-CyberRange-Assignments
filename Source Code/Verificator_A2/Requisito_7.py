import Rules_Utils
from colorama import Fore, Style


def Main_code():

    check_req7=''
    print("---------------------------------------------------------------------")
    print(Style.BRIGHT + Fore.YELLOW + "Verifica del requisito 7: \n", Style.RESET_ALL)  
    print(Style.BRIGHT +"[Si esegue un test di raggiungibilità SSH dalla rete Client (100.100.2.0/24) verso un gruppo di host dell'ACME, verificando soprattutto l'accesso SSH limitato esclusivamente alla suddetta sottorete] \n", Style.RESET_ALL)

    
    if(Rules_Utils.check_Clients_nested_SSH_connection()):
       print(Style.BRIGHT + Fore.GREEN +"--> REQUISITO SODDISFATTO!", Style.RESET_ALL)
       check_req7="-->SUCCESS!"   
    
    
    else:
        
        print(Style.BRIGHT + Fore.RED +"--> REQUISITO NON SODDISFATTO!", Style.RESET_ALL)
        testo = """
        *Possibili cause:
            -Regola configurata in un interfaccia del Firewall, non idonea al requisito.
            -Regola mal configurata, o assente, rispetto ai criteri richiesti dal requisito.
                ->Con la possibilità che un Host non facente parte della rete 'Client', si connetta in SSH con un altro Host dell'ACME'.
            -Errore generici di rete o connettività SSH.
                ->Con la possibilità che buona parte degli host dell'ACME non siano accessibili dalla rete client.
            
            """
        print(testo)
        check_req7="-->FAILURE!"
    print("---------------------------------------------------------------------")
    return check_req7
