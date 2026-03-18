from pydantic import BaseModel, field_validator


_NAME_RE = __import__("re").compile(r"^[A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё\-]{1,29}$")


class ProfileUpdateIn(BaseModel):
    first_name: str
    last_name: str
    function: str
    category: str

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip().replace("\t", " ").replace("\n", " ")
        while "  " in v:
            v = v.replace("  ", " ")
        if not _NAME_RE.match(v):
            raise ValueError(
                "Только буквы (рус/англ) и дефис, длина от 2 до 30 символов. "
                "Например: Андрей или Анна-Мария"
            )
        return v

    @field_validator("function")
    @classmethod
    def validate_function(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Функция должна быть не менее 2 символов")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Категория не может быть пустой")
        return v
