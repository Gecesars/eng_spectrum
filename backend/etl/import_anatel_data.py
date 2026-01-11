
import os
import xml.dom.minidom
import math
from app import create_app
from app.extensions import db
from app.models import V4Station, Network, User
from sqlalchemy import func

ANATEL_DIR = os.path.join(os.getcwd(), 'anatel')
XML_FILE = os.path.join(ANATEL_DIR, 'plano_basicoTVFM.xml')

def kw_to_dbm(kw):
    if not kw or kw <= 0:
        return None
    return 10 * math.log10(kw * 1000)

def import_anatel():
    app = create_app()
    with app.app_context():
        # Ensure default network exists
        # We need a user to own the network. Use the first user or create a system user.
        # For MVP, let's assume user with email 'admin@example.com' exists or create one?
        # Or just pick the first user.
        user = User.query.first()
        if not user:
            print("No user found. Please create a user first (e.g. via CLI).")
            return

        network = Network.query.filter_by(name="Anatel Import").first()
        if not network:
            network = Network(name="Anatel Import", owner_user_id=user.id, description="Imported from Mosaico XML")
            db.session.add(network)
            db.session.commit()
            print("Created 'Anatel Import' network.")
        else:
            print("Using existing 'Anatel Import' network.")

        print(f"Parsing {XML_FILE}...")
        try:
            doc = xml.dom.minidom.parse(XML_FILE)
        except Exception as e:
            print(f"Failed to parse XML: {e}")
            return

        rows = doc.getElementsByTagName("row")
        print(f"Found {len(rows)} stations.")
        
        count_new = 0
        count_updated = 0
        
        for row in rows:
            mosaico_id = row.getAttribute("IdtPlanoBasico")
            if not mosaico_id:
                continue

            # Check if exists
            station = V4Station.query.filter_by(mosaico_id=mosaico_id).first()
            
            # Extract fields
            service = row.getAttribute("Servico")
            status = row.getAttribute("Status")
            uf = row.getAttribute("UF")
            municipio = row.getAttribute("Municipio")
            
            try:
                lat = float(row.getAttribute("Latitude").replace(',', '.'))
                lon = float(row.getAttribute("Longitude").replace(',', '.'))
            except ValueError:
                # print(f"Invalid coordinates for {mosaico_id}")
                continue
                
            # Channel/Freq
            canal_str = row.getAttribute("Canal")
            freq_str = row.getAttribute("Frequencia")
            
            canal = int(canal_str) if canal_str and canal_str.isdigit() else None
            freq_mhz = float(freq_str.replace(',', '.')) if freq_str else None
            
            # Start/stop freq logic? P.1546 uses center freq.
            
            # ERP/Height
            erp_kw_str = row.getAttribute("ERP")
            erp_kw = float(erp_kw_str.replace(',', '.')) if erp_kw_str else 0.0
            erp_dbm = kw_to_dbm(erp_kw)
            
            altura_str = row.getAttribute("Altura") # Height of antenna center? Or tower? Usually height of antenna center in Anatel data.
            htx = float(altura_str.replace(',', '.')) if altura_str else 0.0
            
            entidade = row.getAttribute("Entidade")
            
            # Geometry WKT
            # SRID 4674 (SIRGAS 2000) assumed for Anatel data (or SAD69? Usually SIRGAS 2000 nowadays).
            wkt = f"POINT({lon} {lat})"
            
            if not station:
                station = V4Station(
                    network_id=network.id,
                    service=service,
                    status=status,
                    canal=canal,
                    freq_mhz=freq_mhz,
                    uf=uf,
                    municipio=municipio,
                    mosaico_id=mosaico_id,
                    entidade=entidade,
                    erp_dbm=erp_dbm,
                    htx=htx,
                    geom=func.ST_GeomFromText(wkt, 4674)
                )
                db.session.add(station)
                count_new += 1
            else:
                # Update fields if needed
                station.service = service
                station.status = status
                station.canal = canal
                station.freq_mhz = freq_mhz
                station.uf = uf
                station.municipio = municipio
                station.entidade = entidade
                station.erp_dbm = erp_dbm
                station.htx = htx
                station.geom = func.ST_GeomFromText(wkt, 4674)
                count_updated += 1
                
            if (count_new + count_updated) % 1000 == 0:
                db.session.commit()
                print(f"Processed {count_new + count_updated}...")
        
        db.session.commit()
        print(f"Import complete. New: {count_new}, Updated: {count_updated}")

if __name__ == "__main__":
    import_anatel()
