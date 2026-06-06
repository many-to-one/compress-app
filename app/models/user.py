from sqlalchemy import Column, Integer, String, Boolean
from db.session import Base
from sqlalchemy.dialects.postgresql import ARRAY

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    full_name = Column(String)
    reset_token = Column(String, nullable=True)

    google_access_token = Column(String, nullable=True)
    google_drive_access_token = Column(String, nullable=True)

    # wszystkie IP, z których user korzystał
    ips = Column(ARRAY(String), default=list)

    # zablokowane IP
    blocked_ips = Column(ARRAY(String), default=list)

    # flaga blokady użytkownika
    is_blocked = Column(Boolean, default=False)

    is_admin = Column(Boolean, default=False)

