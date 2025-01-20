import json
import paramiko
import Rules_Utils
from colorama import Fore, Style
import random
import os
import time

Test_check = 0



def launch_connectivity_check():
    
    # Carica i dati dal file JSON
    with open('devices.json', 'r') as file:
        config = json.load(file)
    
    # Mescola casualmente l'ordine degli elementi nel file JSON
    random.shuffle(config)
    
    # Ciclo su alcuni elementi nel file JSON
    for entry in config[:4]:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Connessione SSH
            ssh.connect(entry['IP'], username=entry['User'], key_filename='SSHKey', timeout=3)
            
            #Facciamo un ping al Proxy con tutti gli host dell'ACME, e nessuno deve fallire per requisito
            Test_check= Rules_Utils.launch_Ping_Command('100.100.6.3', entry['IP'], ssh)
            
            if(Test_check == False):
                print("")
                print("-->Primo test FALLITO...procediamo alla seconda verifica.")
                time.sleep(3)
                
                #Puliamo la console
                if os.name == 'nt':  # Windows
                    os.system('cls')

                else:  # Unix-based systems (Linux, macOS)
                    os.system('clear')
                
                print("---------------------------------------------------------------------")
                print(Style.BRIGHT + Fore.YELLOW + "Verifica del requisito 3: \n", Style.RESET_ALL)
                print(Style.BRIGHT +"[Test di raggiungibilità della rete da parte dei due client della rete ACME, attraverso il Proxy Server (100.100.6.3)] \n", Style.RESET_ALL)
                
                
                
                #Se il controllo col "Ping" ha fallito, lanciamo il secondo controllo sul Proxy Tunnel
                IPs= ["100.100.2.100", "100.100.4.100"]
                
                for ip in IPs:
                    ssh_2 = paramiko.SSHClient()
                    ssh_2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    try:
                        # Connessione SSH
                        ssh_2.connect(ip, username="tester", key_filename='SSHKey', timeout=3)
                        Test_check = Rules_Utils.check_proxy_server_tunnel(ssh_2,3128)
                        
                        #Se fallisce anche questo, usciamo diretti e diamo il test come fallito
                        if(Test_check == False):
                            Test_check = Rules_Utils.check_proxy_server_tunnel(ssh_2,80)
                            if(Test_check == False):
                                print(f"* SOURCE: {ip}: "+Fore.RED +"X", Style.RESET_ALL)
                                break
                            else:
                                print(f"* SOURCE: {ip}: "+Fore.GREEN +"V", Style.RESET_ALL)
                        else:
                            print(f"* SOURCE: {ip}: "+Fore.GREEN +"V", Style.RESET_ALL)
                            
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
                        ssh_2.close()
                
                break
            
        except paramiko.AuthenticationException:
            print(f"Errore di autenticazione per {entry['IP']}.")
            Test_check = False
            break
        except paramiko.SSHException:
            print(f"Errore durante la connessione SSH a {entry['IP']}.")
            Test_check = False
            break
        except Exception as e:
            print(f"Errore sconosciuto per {entry['IP']}: {str(e)}")
            Test_check = False
            break
        finally:
            ssh.close()
    
    print("")
    #Se ogni singolo test va a buon fine, allora abbiamo non solo verificato la presenza della o delle regole ma anche la connettività
    if(Test_check != False):
        print(Style.BRIGHT + Fore.GREEN +"--> REQUISITO SODDISFATTO!", Style.RESET_ALL)
        return True
    else:
        print(Style.BRIGHT + Fore.RED +"--> REQUISITO NON SODDISFATTO!", Style.RESET_ALL)
        return False
    


def Main_code():
    global Test_check
    check_req3=''
    print("---------------------------------------------------------------------")
    print(Style.BRIGHT + Fore.YELLOW + "Verifica del requisito 3: \n", Style.RESET_ALL)
    print(Style.BRIGHT +"[Test di raggiungibilità da parte di un campionato della rete ACME (100.100.0.0/16), verso il Proxy Server (100.100.6.3)] \n", Style.RESET_ALL)
    
    if(launch_connectivity_check()):
       check_req3="-->SUCCESS!"
    
    else:
        print("")
        testo = """
        *Possibili cause:
            -Regola assente nella configurazione dei Firewall. 
            -Regola configurata in un interfaccia del Firewall non idonea al requisito.
            -Regola mal configurate rispetto ai criteri richiesti dal requisito.
            -Errore generici di rete o connettività VPN (magari host non abilitati o spenti).
            -ICMP disabilitato o Proxy Server irraggiungibile su tale protocollo.
            -Proxy Server non in ascolto su nessuna porta all'infuori di quella della 'telnet' (22).
                ->Oppure: nessuna porta aperta per instradare connessioni verso la rete pubblica (es: porta 3128 o 80 non abilitata sul Proxy).
            -Accesso alla rete da parte del Proxy Server chiuso. \n
        """
        print(testo)
        check_req3="-->FAILURE!"
    print("---------------------------------------------------------------------")
    return check_req3


