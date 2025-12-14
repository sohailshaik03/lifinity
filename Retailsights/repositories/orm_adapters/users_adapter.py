from .. import users_repo as legacy_users
from Retailsights.db_orm import get_session
from Retailsights.models import User
from sqlalchemy.exc import NoResultFound
import bcrypt


def create_user(email, password, full_name=None, role="user"):
    session = get_session()
    try:
        pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(email=email, password_hash=pw_hash, full_name=full_name, role=role)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    finally:
        session.close()


def get_user_by_email(email):
    session = get_session()
    try:
        return session.query(User).filter(User.email == email).one_or_none()
    finally:
        session.close()
