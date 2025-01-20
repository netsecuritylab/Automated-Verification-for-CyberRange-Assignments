import requests

def get_web_content(ip_address):
    url = f"http://{ip_address}/"  # Costruisci l'URL per la porta 80
    try:
        response = requests.get(url, timeout=5)  # Fai una richiesta GET con timeout di 5 secondi
        if response.status_code == 200:
            return response.text  # Restituisci il contenuto della risposta se la richiesta ha avuto successo
        else:
            return f"Errore: Risposta HTTP {response.status_code}"
    except requests.RequestException as e:
        return f"Errore di connessione: {str(e)}"

# IP dell'host web da controllare
web_host_ip = '100.100.6.3'

# Esegui la funzione per ottenere il contenuto della pagina web
web_content = get_web_content(web_host_ip)

# Stampa il contenuto della pagina web o un messaggio di errore se la connessione fallisce
print(web_content)
