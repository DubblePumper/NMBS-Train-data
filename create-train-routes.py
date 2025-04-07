import json
import datetime
import random
from rich.console import Console
from rich.table import Table

def laad_data(bestandspad):
    """Laad de GTFS data van het opgegeven JSON bestand."""
    with open(bestandspad, 'r', encoding='utf-8') as bestand:
        return json.load(bestand)

def decodeer_trip_id(trip_id):
    """Decodeer het trip ID om informatie eruit te extraheren."""
    # Format: "88____:007::8896008:8896735:8:647:20250408"
    # Bevat: vervoerder:lijn::beginpunt:eindpunt:onbekend:reisnummer:datum
    delen = trip_id.split(':')
    if len(delen) >= 7:
        return {
            'vervoerder': delen[0],
            'lijn': delen[1],
            'beginpunt': delen[3],
            'eindpunt': delen[4],
            'reisnummer': delen[6],
            'datum': delen[7] if len(delen) > 7 else None
        }
    return None

def vind_stops_voor_trip(trip_id, stops_data, platform_mapping):
    """Zoek alle haltes voor een trip uit de data."""
    trip_info = decodeer_trip_id(trip_id)
    if not trip_info:
        return []

    # In echte implementatie zou je hier stop_times gebruiken, maar we simuleren dit
    # door de begin- en eindstations te gebruiken uit het ID
    begin_id = trip_info['beginpunt']
    eind_id = trip_info['eindpunt']
    
    # Vind de stationsnamen op basis van IDs
    begin_naam = vind_station_naam(begin_id, stops_data)
    eind_naam = vind_station_naam(eind_id, stops_data)
    
    # Genereer tussenliggende haltes (gesimuleerd voor demo)
    aantal_tussenstops = random.randint(2, 5)
    stops = []
    
    # Begin station
    platform = vind_platform(begin_id, platform_mapping)
    stops.append({
        'stop_id': begin_id,
        'stop_naam': begin_naam,
        'platform': platform,
        'aankomst_tijd': None,
        'vertrek_tijd': "08:00",
        'vertraging': 0
    })
    
    # Tussenliggende stations (willekeurig gegenereerd voor demo)
    tussenstation_ids = [
        "8821006", "8831005", "8841004", "8872009", "8883006", 
        "8891405", "8891702", "8892007", "8895505", "8896008"
    ]
    
    gekozen_tussenstations = random.sample(tussenstation_ids, min(aantal_tussenstops, len(tussenstation_ids)))
    for i, station_id in enumerate(gekozen_tussenstations):
        station_naam = vind_station_naam(station_id, stops_data)
        platform = vind_platform(station_id, platform_mapping)
        vertrek_min = 8 + (i+1) * 10
        aankomst_min = vertrek_min - 1
        vertraging = random.randint(0, 3) if random.random() < 0.3 else 0
        
        stops.append({
            'stop_id': station_id,
            'stop_naam': station_naam,
            'platform': platform,
            'aankomst_tijd': f"08:{aankomst_min:02d}",
            'vertrek_tijd': f"08:{vertrek_min:02d}",
            'vertraging': vertraging
        })
    
    # Eind station
    platform = vind_platform(eind_id, platform_mapping)
    aankomst_tijd = 8 + (aantal_tussenstops + 1) * 10
    vertraging = random.randint(0, 5) if random.random() < 0.2 else 0
    
    stops.append({
        'stop_id': eind_id,
        'stop_naam': eind_naam,
        'platform': platform,
        'aankomst_tijd': f"08:{aankomst_tijd:02d}",
        'vertrek_tijd': None,
        'vertraging': vertraging
    })
    
    return stops

def vind_station_naam(station_id, stops_data):
    """Vind een stationsnaam op basis van het station ID."""
    # In echte implementatie zou je de stops tabel gebruiken
    # We gebruiken hier een mapping van bekende stations voor de demo
    station_mapping = {
        "8811007": "Gent-Sint-Pieters",
        "8821006": "Brussel-Zuid",
        "8831005": "Leuven",
        "8831310": "Antwerpen-Centraal",
        "8841004": "Oostende",
        "8841608": "Brugge",
        "8844628": "Kortrijk",
        "8863008": "Hasselt",
        "8865003": "Genk",
        "8866001": "Luik-Guillemins",
        "8872009": "Charleroi-Zuid",
        "8883006": "Namen",
        "8884335": "Doornik",
        "8891405": "Mechelen",
        "8891660": "Blankenberge",
        "8891702": "Gent-Dampoort",
        "8892007": "Denderleeuw",
        "8893401": "Aalst",
        "8895505": "Dendermonde",
        "8896008": "Poperinge",
        "8896735": "Ieper"
    }
    
    if station_id in station_mapping:
        return station_mapping[station_id]
    
    # Zoek in stops_data indien nodig
    for stop in stops_data.get('stops', {}).get('data', []):
        if stop.get('stop_id') == station_id:
            return stop.get('stop_name', f"Station {station_id}")
    
    # Zoek in stoppoints indien nodig (gesimplificeerd voor demo)
    for stoppoint_mapping in stops_data.get('stoppoints', {}).get('data', []):
        for key in stoppoint_mapping:
            if station_id in key:
                # Parse de naam uit de mapping key (vereenvoudigd)
                return key.split(';')[-1] if ';' in key else f"Station {station_id}"
    
    return f"Station {station_id}"

def vind_platform(station_id, platform_mapping):
    """Vind het platform voor een station."""
    # Platform mapping heeft de vorm "station_id_platform;station_id;platform"
    for mapping in platform_mapping:
        parts = mapping.split(';')
        if len(parts) >= 2 and parts[1] == station_id and len(parts) >= 3:
            return parts[2]
    return None

def toon_trein_informatie(trein, stops):
    """Toon gedetailleerde informatie over een trein en zijn haltes."""
    console = Console()
    
    # Informatie over de trein
    trip_info = decodeer_trip_id(trein)
    if not trip_info:
        console.print(f"[bold red]Kan geen informatie vinden voor trein ID: {trein}[/bold red]")
        return
    
    # Tabel voor trein info
    trein_tabel = Table(title=f"Trein {trip_info['vervoerder']} lijn {trip_info['lijn']} - {trip_info['reisnummer']}")
    trein_tabel.add_column("Kenmerk", style="cyan")
    trein_tabel.add_column("Waarde", style="green")
    
    trein_tabel.add_row("Van", f"{vind_station_naam(trip_info['beginpunt'], {})} ({trip_info['beginpunt']})")
    trein_tabel.add_row("Naar", f"{vind_station_naam(trip_info['eindpunt'], {})} ({trip_info['eindpunt']})")
    trein_tabel.add_row("Datum", trip_info['datum'])
    trein_tabel.add_row("Lijn", trip_info['lijn'])
    trein_tabel.add_row("Reisnummer", trip_info['reisnummer'])
    
    console.print(trein_tabel)
    console.print("")
    
    # Tabel voor haltes
    haltes_tabel = Table(title="Route")
    haltes_tabel.add_column("Station", style="cyan")
    haltes_tabel.add_column("Platform", style="yellow")
    haltes_tabel.add_column("Aankomst", style="green")
    haltes_tabel.add_column("Vertrek", style="green")
    haltes_tabel.add_column("Vertraging", style="red")
    
    for stop in stops:
        vertraging_tekst = f"+{stop['vertraging']} min" if stop['vertraging'] > 0 else "-"
        haltes_tabel.add_row(
            stop['stop_naam'],
            stop['platform'] or "-",
            stop['aankomst_tijd'] or "-",
            stop['vertrek_tijd'] or "-",
            vertraging_tekst
        )
    
    console.print(haltes_tabel)
    console.print("\n" + "-" * 80 + "\n")

def main():
    print("NMBS/SNCB Trein Route Analyse - 7 april 2025\n")
    
    try:
        # Laad de data
        data = laad_data('data.json')
        
        # Haal platform mapping
        platform_mapping_text = data.get('planning_data', {}).get('matching_table_platforms', '')
        platform_mapping = platform_mapping_text.strip().split('\n')
        
        # Vind 5 verschillende trip_ids uit de realtime data
        trip_ids = []
        entities = data.get('realtime', {}).get('entity', [])
        
        # Filter op alleen maar vandaag (7 april 2025)
        vandaag = "20250407"
        
        for entity in entities:
            trip_id = entity.get('id', '')
            if vandaag in trip_id and len(trip_ids) < 5:
                trip_ids.append(trip_id)
        
        # Als er niet genoeg trips zijn, neem willekeurige
        if len(trip_ids) < 5:
            for entity in entities:
                trip_id = entity.get('id', '')
                if trip_id and trip_id not in trip_ids and len(trip_ids) < 5:
                    trip_ids.append(trip_id)
        
        # Toon informatie voor elke trein
        for trip_id in trip_ids:
            stops = vind_stops_voor_trip(trip_id, data.get('planning_data', {}), platform_mapping)
            toon_trein_informatie(trip_id, stops)
        
    except Exception as e:
        print(f"Er is een fout opgetreden: {e}")

if __name__ == "__main__":
    main()