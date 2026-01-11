
from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        print("Dropping artifacts from failed migration...")
        conn.execute(text('DROP TABLE IF EXISTS gis.rasters CASCADE'))
        conn.execute(text('DROP TABLE IF EXISTS core.stations_v4 CASCADE'))
        conn.execute(text('DROP TABLE IF EXISTS core.antennas_v4 CASCADE'))
        conn.execute(text('DROP TABLE IF EXISTS core.networks CASCADE'))
        conn.execute(text('DROP TABLE IF EXISTS core.jobs CASCADE'))
        conn.commit()
        print("Done dropping tables.")
