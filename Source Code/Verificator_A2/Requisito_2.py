import requests
from colorama import Fore, Style


def Main_code():
    # Definisci l'URL del server DMZ
    dmz_server_url = "http://100.100.6.2"
    check=False
    check_req2=''
    
    print("---------------------------------------------------------------------")
    print(Style.BRIGHT + Fore.YELLOW + "Verifica del requisito 2: \n", Style.RESET_ALL)
    print(Style.BRIGHT +"[Controllo mediante 'request' dalla rete pubblica, se il Web-Service esposto dalla DMZ è raggiungibile] \n", Style.RESET_ALL)

    # Prova a fare una richiesta HTTP al server DMZ
    try:
        response = requests.get(dmz_server_url)
        if response.status_code == 200:
            print("* Il server DMZ è accessibile da internet. \n")
            check=True
        else:
            print("* Il server DMZ è accessibile da internet, ma ha restituito un codice di stato diverso da 200. \n")
    except requests.ConnectionError:
        print("* Impossibile connettersi al server DMZ. Potrebbe essere protetto dalle connessioni Internet esterne! \n")
    except Exception as e:
        print(f"* Si è verificato un errore: {str(e)} \n")

    if(check):
        print(Style.BRIGHT + Fore.GREEN +"--> REQUISITO SODDISFATTO!", Style.RESET_ALL)
        check_req2="-->SUCCESS!"
    else:
        print(Style.BRIGHT + Fore.RED +"--> REQUISITO NON SODDISFATTO!", Style.RESET_ALL)
        check_req2="-->FAILURE!"

    print("---------------------------------------------------------------------")
    
    return check_req2
