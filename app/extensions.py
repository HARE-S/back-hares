from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_smorest import Api
from flask_session import Session

db = SQLAlchemy()
migrate = Migrate()
openapi_api = Api()
session = Session()
