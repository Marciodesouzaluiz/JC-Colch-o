"""
Ponto de entrada WSGI para servidores de produção (Gunicorn).
Usado pelo Render e Railway para iniciar a aplicação.
"""
import os
from app import app, db, criar_admin_padrao

# Garante que o banco de dados e o admin padrão existem ao subir
with app.app_context():
    db.create_all()
    criar_admin_padrao()

# Gunicorn busca este objeto: gunicorn wsgi:app
application = app
