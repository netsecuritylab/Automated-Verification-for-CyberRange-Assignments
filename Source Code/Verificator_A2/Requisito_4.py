import paramiko
import json
import Rules_Utils
from colorama import Fore, Style
import os
import time

# Dizionario per memorizzare gli indirizzi IP associati a ciascuna interfaccia dei 2 FW
MFW_interfaces_ip_dict = {}
IFW_interfaces_ip_dict = {}

alias_dict_MFW = {}  # Dizionario per memorizzare gli alias del Main FW
alias_dict_IFW = {}  # Dizionario per memorizzare gli alias dell'internal FW

check = False
Test_check = 0


def launch_connectivity_check():
    final_check=True
    
    # Carica i dati dal file JSON
    with open('devices.json', 'r') as file:
        config = json.load(file)
    
    # Ciclo su ciascun elemento nel file JSON
    for entry in config:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        #Testiamo la connettività con tutti gli host
        try:
            # Connessione SSH
            ssh.connect(entry['IP'], username=entry['User'], key_filename='SSHKey')
            
            #Gli host da pingare nell'internal service Network (i suoi service: DNS Server e Greenbone Server), solo da parte della rete Client e DMZ
            Internal_Server_Host = ['100.100.1.2', '100.100.1.4']
            
            for host in Internal_Server_Host:
                
                #Non effettuiamo test interni alla Internal e External Network, allo scopo del requisito non c'interessa
                if((entry['IP'].startswith('100.100.1.'))==False):
                
                    Test_check= Rules_Utils.launch_Ping_Command(host, entry['IP'], ssh)
                    
                    #Il DNS può essere raggiunto indiscrinamente (anche dagli Host dell'External service)
                    if(Test_check == True and host=='100.100.1.2'):
                        pass
                    
                    #Se a riuscire il ping sono Host fuori dalla rete client e DMZ (quindi rimane solo la "external service"), l'infrastruttura non è correttamente configurata
                    elif((entry['IP'].startswith('100.100.4.'))):
                        if(Test_check == True): 
                            #print(entry['IP'], "BREAK")
                            print(Style.BRIGHT + Fore.BLUE+"*) APPENA ESEGUITA CONTRO PROVA PER UN HOST, DELLA RETE 'EXTERNAL': "+ Style.BRIGHT + Fore.RED+"FALLITA", Style.RESET_ALL)
                            final_check=False
                            break
                        else:
                            print(Style.BRIGHT + Fore.BLUE+"*) APPENA ESEGUITA CONTRO PROVA PER UN HOST, DELLA RETE 'EXTERNAL': "+ Style.BRIGHT + Fore.GREEN+"RIUSCITA", Style.RESET_ALL)
                            print(Style.BRIGHT + "-->L'unico servizio raggiungibile da tutti gli Host, da requisito, è il risolutore DNS (100.100.1.2).", Style.RESET_ALL, "\n")
                    
                    #Se a fallire il ping sono Host della rete client e DMZ (quindi rimane solo la "external service"), l'infrastruttura non è correttamente configurata
                    elif(Test_check == False and ((entry['IP'].startswith('100.100.4.'))==False)):
                        #print(entry['IP'], "BREAK")
                        final_check=False
                        break
            
            print("")
            if(final_check==False):
               break
            
        except paramiko.AuthenticationException:
            print(f"Errore di autenticazione per {entry['IP']}. \n")
            final_check = False
            break
        except paramiko.SSHException:
            print(f"Errore durante la connessione SSH a {entry['IP']}. \n")
            final_check = False
            break
        except Exception as e:
            print(f"Errore sconosciuto per {entry['IP']}: {str(e)} \n")
            final_check = False
            break
        finally:
            ssh.close()
    
    
    
    #Se ogni singolo test va a buon fine, allora abbiamo non solo verificato la presenza della o delle regole ma anche la connettività
    if(final_check):
        print(Style.BRIGHT + Fore.GREEN +"--> REQUISITO SODDISFATTO!", Style.RESET_ALL)
        return True
    
    else:
        
        print("-->Primo test FALLITO...procediamo alla seconda verifica.")
        time.sleep(3)
        
        #Puliamo la console
        if os.name == 'nt':  # Windows
            os.system('cls')

        else:  # Unix-based systems (Linux, macOS)
            os.system('clear')
        
        print("---------------------------------------------------------------------")
        print(Style.BRIGHT + Fore.YELLOW + "Verifica del requisito 4: \n", Style.RESET_ALL)
        print(Style.BRIGHT +"[Test di raggiungibilità della rete interna (attraverso un check al service di un suo host, ossia il greenbone) usando un host della rete 'Client'] \n", Style.RESET_ALL)
        
        #Se il controllo col "Ping" ha fallito, lanciamo il secondo controllo sui due client della ACME (kali e client-ext1)
        IPs= ["100.100.2.100", "100.100.4.100"]
        
        
        for ip in IPs:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                # Connessione SSH
                ssh.connect(ip, username="tester", key_filename='SSHKey', timeout=5)
                Test_check = Rules_Utils.check_greenbone_connectivity(ssh)
                
                    
            except paramiko.AuthenticationException:
                print(f"Errore di autenticazione per {ip}.")
                Test_check = False
                break
            except paramiko.SSHException:
                print(f"Errore durante la connessione SSH a {ip}.")
                Test_check = False
                break
            except Exception as e:
                print(f"Errore sconosciuto per {ip}: {str(e)}")
                Test_check = False
                break
            finally:
                ssh.close()

        
            if((Test_check==True) and (ip == "100.100.2.100")): 
                print(f"* SOURCE (Clients-Network) {ip}: "+Fore.GREEN +"V"+Style.RESET_ALL+", destination: Greenbone.", "\n")
                final_check = True
                
            elif((Test_check==False) and (ip == "100.100.4.100")):
                print(f"* SOURCE (External-Service) {ip}: "+Fore.RED +"X"+Style.RESET_ALL+", destination: Greenbone.")
                print(Style.BRIGHT + Fore.BLUE+"*) APPENA ESEGUITA CONTRO PROVA PER UN HOST, DELLA RETE 'EXTERNAL': "+ Style.BRIGHT + Fore.GREEN+"RIUSCITA", Style.RESET_ALL, "\n")

                final_check = True
            
            elif((Test_check==True) and (ip == "100.100.4.100")):
                print(f"* SOURCE (External-Service) {ip}: "+Fore.RED +"X"+Style.RESET_ALL+", destination: Greenbone.")
                print(Style.BRIGHT + Fore.BLUE+"*) APPENA ESEGUITA CONTRO PROVA PER UN HOST, DELLA RETE 'EXTERNAL': "+ Style.BRIGHT + Fore.GREEN+"FALLITA", Style.RESET_ALL, "\n")

                final_check = False
                
            else:
                print(f"* SOURCE: {ip}: "+Fore.RED +"Connection Time-Out"+Style.RESET_ALL+" destination: Greenbone.")
                final_check = False
                break
        
        print("")
        if(final_check):
            print(Style.BRIGHT + Fore.GREEN +"--> REQUISITO SODDISFATTO!", Style.RESET_ALL)
            return True
        else:
            print(Style.BRIGHT + Fore.RED +"--> REQUISITO NON SODDISFATTO!", Style.RESET_ALL)
            return False


def Main_code():
    check_req4=''
    print("---------------------------------------------------------------------")
    print(Style.BRIGHT + Fore.YELLOW + "Verifica del requisito 4: \n", Style.RESET_ALL)
    print(Style.BRIGHT +"[Test di raggiungibilità della rete interna (100.100.1.0/16), da parte delle reti DMZ (100.100.6.0/24) e Client (100.100.2.0/24)] \n", Style.RESET_ALL)

    if(launch_connectivity_check()): 
        check_req4="-->SUCCESS!"    
    else:
        print("")
        testo = """
        *Possibili cause:
            -Regola assente nella configurazione dei Firewall. 
            -Regola configurata in un interfaccia del Firewall non idonea al requisito.
            -Regola mal configurate rispetto ai criteri richiesti dal requisito.
            -Errore generici di rete o connettività.
            -Il servizio esposto dal GreenBone non è raggiungibile.
        """
        print(testo)
        check_req4="-->FAILURE!"
    print("---------------------------------------------------------------------")
    return check_req4
