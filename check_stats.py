import os
import json
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "anton.db")}'
db = SQLAlchemy(app)

class GestionObra(db.Model):
    __tablename__ = 'gestion_obras'
    id = db.Column(db.Integer, primary_key=True)

class MapeoFiltro(db.Model):
    __tablename__ = 'mapeos_filtros'
    id = db.Column(db.Integer, primary_key=True)

class ConfiguracionFiltro(db.Model):
    __tablename__ = 'configuracion_filtros'
    id = db.Column(db.Integer, primary_key=True)

with app.app_context():
    print(f"Obras: {GestionObra.query.count()}")
    print(f"Mapeos: {MapeoFiltro.query.count()}")
    print(f"FiltroConfigs: {ConfiguracionFiltro.query.count()}")
