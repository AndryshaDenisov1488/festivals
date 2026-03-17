from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    first_name: str
    last_name: str
    function: str
    category: str


class UserOut(UserBase):
    user_id: int
    email: EmailStr | None = None
    is_admin: bool = False

    class Config:
        from_attributes = True


class UserUpdateIn(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    function: str | None = None
    category: str | None = None


class UserEmailUpdateIn(BaseModel):
    email: EmailStr

