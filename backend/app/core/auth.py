from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db

DEMO_USER_EMAIL = "demo@p-insight.local"
DEMO_USER_DISPLAY_NAME = "Demo User"


def get_development_user(db: Annotated[Session, Depends(get_db)]) -> User:
    """Development auth placeholder.

    This deterministic user is intentionally temporary and will be replaced by
    Supabase Auth or Clerk in a later auth phase.
    """
    user = db.scalar(select(User).where(User.email == DEMO_USER_EMAIL))
    if user is not None:
        return user

    user = User(email=DEMO_USER_EMAIL, display_name=DEMO_USER_DISPLAY_NAME)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


CurrentUser = Annotated[User, Depends(get_development_user)]
