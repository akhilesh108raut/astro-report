from flask_sqlalchemy import SQLAlchemy

# Kept in one module so all standalone models share the same metadata/session.
db = SQLAlchemy()
