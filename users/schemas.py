from datetime import datetime

from pydantic import BaseModel

from users.choices import UserType


class UserRequest(BaseModel):
    first_name: str
    last_name: str
    username: str
    password: str
    email: str
    phone: str
    gender: str
    user_type: UserType = UserType.REGULAR
    date_of_birth: datetime


class UserItem(BaseModel):
    id: str
    first_name: str
    last_name: str
    username: str
    email: str
    phone: str
    gender: str
    user_type: UserType
    date_of_birth: datetime


class UsersListResponse(BaseModel):
    users: list[UserItem]
    total: int
    message: str
