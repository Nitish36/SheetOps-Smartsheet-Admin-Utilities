from database import engine, Base
from models.user import User
from models.subscription import Subscription

Base.metadata.create_all(bind=engine)
