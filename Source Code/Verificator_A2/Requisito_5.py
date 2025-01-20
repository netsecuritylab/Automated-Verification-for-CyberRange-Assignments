import paramiko
import json
import Rules_Utils
from colorama import Fore, Style
import random
import time
import os 

check = False
Test_check = 0


def check_logserver():
    print("---------------------------------------------------------------------")
    print(Style.BRIGHT + Fore.YELLOW + "Verifica del requisito 5: \n", Style.RESET_ALL)
    print(Style.BRIGHT +"[Test di utilizzo del servizio di Log da parte della rete ACME (100.100.0.0/16), verso il LogServer (100.100.1.3)] \n", Style.RESET_ALL)
    final_check=True
    
    # Carica i dati dal file JSON
    with open('devices.json', 'r') as file:
        config = json.load(file)
    
    # Mescola casualmente l'ordine degli elementi nel file JSON
    random_entries = random.sample(config, 4)
    
    # Ciclo su alcuni elementi/host nel file JSON
    for entry in random_entries:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Connessione SSH
            ssh.connect(entry['IP'], username=entry['User'], key_filename='SSHKey', timeout=3)
            comando_remoto = f"echo -n {entry['Name']} | nc -u -w1 100.100.1.3 514"
            ssh.exec_command(comando_remoto)

        except paramiko.AuthenticationException:
            print(f"Errore di autenticazione per {entry['IP']}. \n")
            final_check = False
            break
        except paramiko.SSHException:
            print(f"Errore durante la connessione SSH a {entry['IP']}. \n")
            final_check = False
            break
        except Exception as e:
            print(f"Errore sconosciuto per {entry['IP']}: {str(e)}. \n")
            final_check = False
            break
        finally:
            ssh.close()
        
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Connessione SSH al logserver, su ROOT in quanto è lì che c'è il file coi log da leggere.
            ssh.connect("100.100.1.3", username="root", key_filename='SSHKey', timeout=3)
            comando_remoto = f"cat /var/log/user.log | grep '{entry['Name']}'"
            stdin, stdout, stderr = ssh.exec_command(comando_remoto)
            
            # Si prende l'output comando remoto
            output = stdout.read().decode()
            #print(output)
            
            if((entry['IP'].startswith('100.100.2.'))):
                #print(output)
                if((output != None) and (output != '')):
                    #print(entry['IP'], "BREAK")
                    #print(output)
                    print(Style.BRIGHT + Fore.BLUE+"-> APPENA ESEGUITA CONTRO PROVA PER UN HOST, DELLA RETE 'CLIENT' (100.100.2.0/24): "+ Style.BRIGHT + Fore.RED+"FALLITA", Style.RESET_ALL, "\n")
                    final_check=False
                    break
                else:
                    print(Style.BRIGHT + Fore.BLUE+"-> APPENA ESEGUITA CONTRO PROVA PER UN HOST, DELLA RETE 'CLIENT': "+ Style.BRIGHT + Fore.GREEN+"RIUSCITA", Style.RESET_ALL, "\n")
            
            else:
                if((output != None) and (output != '')):
                    print(Style.BRIGHT +"*) Test sull'host "+Fore.CYAN+ f"({entry['Name']}): "+ Style.BRIGHT + Fore.GREEN+"RIUSCITO", Style.RESET_ALL)

                else:
                    print(Style.BRIGHT +"*) Test sull'host "+Fore.CYAN+ f"({entry['Name']}): "+ Style.BRIGHT + Fore.RED+"FALLITO", Style.RESET_ALL)
                    final_check=False
                    break
                
            #print(stderr.read().decode())

        except paramiko.AuthenticationException:
            print(f"Errore di autenticazione per {entry['IP']}. \n")
            final_check = False
            break
        except paramiko.SSHException:
            print(f"Errore durante la connessione SSH a {entry['IP']}. \n")
            final_check = False
            break
        except Exception as e:
            print(f"Errore sconosciuto per {entry['IP']}: {str(e)}. \n")
            final_check = False
            break
        finally:
            ssh.close()
    
    return final_check
        
        

def launch_connectivity_check():
    #print("Procediamo con una verifica dell'effettiva connettività coi servizi syslog (.1.10) e log collector (.1.3), da parte di tutti gli host TRANNE quelli della rete client (.2.0/24): ")
    final_check=True
    
    # Carica i dati dal file JSON
    with open('devices.json', 'r') as file:
        config = json.load(file)
    
    # Mescola casualmente l'ordine degli elementi nel file JSON
    random.shuffle(config)
    
    # Ciclo su ciascun elemento nel file JSON
    for entry in config[:4]:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        #Testiamo la connettività con tutti gli host
        try:
            # Connessione SSH
            ssh.connect(entry['IP'], username=entry['User'], key_filename='SSHKey', timeout=3)
            
            #Gli host da pingare nell'internal service Network (Log Server e Graylog Server)
            Internal_Server_Host = ['100.100.1.10', '100.100.1.3']
            
            for host in Internal_Server_Host:
   
                Test_check= Rules_Utils.launch_Ping_Command(host, entry['IP'], ssh)
                
                #Se a riuscire il ping sono Host della rete client, l'infrastruttura non è correttamente configurata
                if((entry['IP'].startswith('100.100.2.'))):
                    if(Test_check == True): 
                        #print(entry['IP'], "BREAK")
                        print(Style.BRIGHT + Fore.BLUE+"*) APPENA ESEGUITA CONTRO PROVA PER UN HOST, DELLA RETE 'CLIENT': "+ Style.BRIGHT + Fore.RED+"FALLITA", Style.RESET_ALL)
                        final_check=False
                        break
                    else:
                        print(Style.BRIGHT + Fore.BLUE+"*) APPENA ESEGUITA CONTRO PROVA PER UN HOST, DELLA RETE 'CLIENT': "+ Style.BRIGHT + Fore.GREEN+"RIUSCITA", Style.RESET_ALL)
                
                #Se a fallire il ping sono Host fuori dalla rete client, l'infrastruttura non è correttamente configurata
                elif(Test_check == False and ((entry['IP'].startswith('100.100.2.'))==False)):
                    #print(entry['IP'], "BREAK")
                    final_check=False
                    break
            
            print("")
            if(final_check == False):
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
            print(f"Errore sconosciuto per {entry['IP']}: {str(e)}. \n")
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
        
       
        return False




def Main_code():
    check_req5=''
    print("---------------------------------------------------------------------")
    print(Style.BRIGHT + Fore.YELLOW + "Verifica del requisito 5: \n", Style.RESET_ALL)
    print(Style.BRIGHT +"[Test di raggiungibilità di un campionato della rete ACME (100.100.0.0/16), verso il LogServer (100.100.1.3) e GrayLog (100.100.1.10) ] \n", Style.RESET_ALL)

    if(launch_connectivity_check()): 
        check_req5="-->SUCCESS!"    
    
    else:
        if(check_logserver()):
            print("")
            print(Style.BRIGHT + Fore.GREEN +"--> REQUISITO SODDISFATTO!", Style.RESET_ALL)
            check_req5="-->SUCCESS!"  
        else:
            
            print(Style.BRIGHT + Fore.RED +"--> REQUISITO NON SODDISFATTO!", Style.RESET_ALL)
            print("")
            testo = """
            *Possibili cause:
                -Regola assente nella configurazione dei Firewall. 
                -Regola configurata in un interfaccia del Firewall non idonea al requisito.
                -Regola mal configurate rispetto ai criteri richiesti dal requisito.
                    ->Magari con un host della rete client che raggiunge e usa i servizi di Log del Logserver, contrariamente alle specifiche.
                -Errore generici di rete o connettività VPN.
				-Servizio di Log inacessibile dagli Host.
            
            """
            print(testo)
            check_req5="-->FAILURE!"
    print("---------------------------------------------------------------------")
    return check_req5
