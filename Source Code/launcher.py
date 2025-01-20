import os
import shutil
import sys
import subprocess
import platform
import re
import json
import time

def trova_cartella_acme(nome_cartella_cercata):
    
    finded_path=[]
    
    # Ottieni il percorso della cartella corrente
    percorso_corrente = os.path.dirname(os.path.realpath(__file__))

    # Normalizza il nome della cartella cercata
    nome_cartella_cercata_norm = os.path.normcase(nome_cartella_cercata)

    # Itera attraverso tutte le cartelle nel percorso corrente
    for cartella in os.listdir(percorso_corrente):
        # Normalizza il nome della cartella corrente
        cartella_norm = os.path.normcase(cartella)

        # Verifica se la stringa cercata è presente nel nome della cartella
        if nome_cartella_cercata_norm in cartella_norm:
            # Costruisci il percorso completo della cartella trovata
            percorso_trovato = os.path.join(percorso_corrente, cartella)

            # Restituisci il percorso della cartella trovata
            finded_path.append(percorso_trovato)
            break
        
        elif nome_cartella_cercata_norm == "acme_all":
            if (("acme" in cartella_norm) or ("ACME" in cartella_norm)):
                # Costruisci il percorso completo della cartella trovata
                percorso_trovato = os.path.join(percorso_corrente, cartella)

                if os.path.isdir(percorso_trovato):
                    # Restituisci il percorso della cartella trovata
                    finded_path.append(percorso_trovato)

    
    return finded_path




# Verifica che almeno due argomenti siano stati passati (nome dello script + almeno un argomento)
if len(sys.argv) < 3:
    print("Usage: python launcher.py <ACME_number>/<ACME_ALL> <Assignment_choice>")
    sys.exit(1)

# Il secondo argomento (indice 1) è il numero ACME
acme = sys.argv[1]


testing_folders = trova_cartella_acme(acme)

if len(testing_folders) == 0:
    print(f"La cartella che contiene il nome '{acme}' non esiste.")
    sys.exit(1)



for testing_folder in testing_folders:

    #Ci prendiamo il nome della ACME analizzata
    acme = os.path.basename(testing_folder)
    acme= re.search(r'acme.*', acme, re.IGNORECASE).group()

    # Imposta la cartella di destinazione come cartella corrente (directory dello script)
    destination_folder = os.path.dirname(os.path.realpath(__file__))
    
    # Crea la lista dei file nella cartella di testing
    files_to_copy = [f for f in os.listdir(testing_folder) if f.endswith('.ovpn') and os.path.isfile(os.path.join(testing_folder, f))]
    
    # Copia i file nella cartella di destinazione
    for file_name in files_to_copy:
        source_path = os.path.join(testing_folder, file_name)
        destination_path = os.path.join(destination_folder, file_name)
        shutil.copy2(source_path, destination_path)
    
    #print(f"File dalla cartella '{testing_folder}' copiati con successo nella cartella dello script.")
    
    # Verifica il terzo argomento (indice 2) per il numero di scelta dell'Assignment
    assignment_choice = sys.argv[2]
    
    number_assignment = re.search(r'\d+', assignment_choice)
    number_assignment = int(number_assignment.group())
    
    if ((number_assignment == 1) == False) and ((number_assignment == 2) == False):
        print("Selezionare su quale Assignment testare l'ACME SCELTA (1 o 2).")
        sys.exit(1)
    
    # Determina la destinazione in base alla scelta dell'Assignment
    if (number_assignment == 1):
        
        # Definisci il percorso del tuo script da lanciare
        #script_da_lanciare = r'C:\Users\Paul\Desktop\Progetto di Tesi 2023-24\Verificatore Python\Progetto 1\Codice_Ultimato_A1_Project\Version 6 (ping)\Grader_Main.py'
        #destination_assignment_folder = r"C:\Users\Paul\Desktop\Progetto di Tesi 2023-24\Verificatore Python\Progetto 1\Codice_Ultimato_A1_Project\Version 6 (ping)"
        
        script_da_lanciare = os.getcwd() + r'\Verificator_A1\Grader_Main.py'
        destination_assignment_folder = os.getcwd() + r'\Verificator_A1'
        
    elif (number_assignment == 2):
        #script_da_lanciare = r'C:\Users\Paul\Desktop\Progetto di Tesi 2023-24\Verificatore Python\Progetto 2\Main_Page.py'
        #destination_assignment_folder = r"C:\Users\Paul\Desktop\Progetto di Tesi 2023-24\Verificatore Python\Progetto 2"
        
        script_da_lanciare = os.getcwd() + r'\Verificator_A2\Main_Page.py'
        destination_assignment_folder = os.getcwd() + r'\Verificator_A2'
    
    # Sposta i file nella destinazione dell'Assignment scelto
    for file_name in files_to_copy:
        source_path = os.path.join(destination_folder, file_name)
        destination_path = os.path.join(destination_assignment_folder, file_name)
        shutil.move(source_path, destination_path)
    
    #print(f"I file sono stati spostati in '{destination_assignment_folder}'.")
    
    #argomenti_da_passare = []
    
    # Definisci il dizionario da passare
    parametri = {"All": False, "Nome_File": f"{acme}_result_log_{assignment_choice}.txt", "launcher": True}
    
    
    # Termine da cercare
    termine_cercato = "test_all"
    
    # Confronto ignorando maiuscole/minuscole
    presente = any(termine_cercato.lower() in elemento.lower() for elemento in sys.argv)
    
    if(presente):
        parametri = {"All": True, "Nome_File": f"{acme}_result_log_{assignment_choice}.txt","launcher": True}
    
       
    #argomenti_da_passare.append(f"{acme}_result_log.txt")
    
    # Converti il dizionario in una stringa JSON
    parametri_json = json.dumps(parametri)
    
    # Imposta stdout su subprocess.PIPE solo se non è Windows
    stdout_option = subprocess.PIPE if platform.system() != 'Windows' else None
    
    
    ACME_Testing_Folder = os.path.join(os.getcwd(), testing_folder)
    
    vecchio_path=os.getcwd()
    
    # Imposta la nuova directory di lavoro
    os.chdir(destination_assignment_folder)
    
    # Utilizza subprocess per eseguire lo script con gli argomenti e catturare l'output
    result = subprocess.run(['python', script_da_lanciare, parametri_json], stdout=stdout_option, text=True)
    
    
    
    # Definisci il percorso del file da spostare (nome del file incluso)
    file_di_report = f"{acme}_result_log_{assignment_choice}.txt"
    
    with open(file_di_report, "r") as file:
        file_content = file.read()

    if "Errore" in file_content:
        time.sleep(2)
        # Utilizza subprocess per eseguire lo script con gli argomenti una seconda volta per sicurezza laddove ci fossero errori di connessione.
        result = subprocess.run(['python', script_da_lanciare, parametri_json], stdout=stdout_option, text=True)
   
    
    # Definisci il percorso di destinazione
    percorso_di_destinazione = ACME_Testing_Folder
    
    # Sposta il file nel percorso di destinazione
    shutil.move(file_di_report, os.path.join(percorso_di_destinazione, file_di_report))
    
    #Si eliminano il file di backup (.xml) e quelli di configurazione dalla directory dello script, dell'Assignment, lanciato.
    [os.remove(file) for file in os.listdir() if file.endswith('.xml')]
    [os.remove(file) for file in os.listdir() if file.endswith('.ovpn')]
    
    
    # Imposta la vecchia directory di lavoro ed eliminiamo eventuali file ".ovpn" se qualcosa va storto.
    os.chdir(vecchio_path)
    [os.remove(file) for file in os.listdir() if file.endswith('.ovpn')]
    
    time.sleep(2)