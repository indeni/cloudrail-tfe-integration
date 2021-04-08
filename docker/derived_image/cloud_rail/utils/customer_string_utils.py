import hashlib


class CustomerStringUtils:
    salt: str = None

    @classmethod
    def set_hashcode_salt(cls, salt):
        cls.salt = salt

    @classmethod
    def to_hashcode(cls, value) -> str:
        if not cls.salt:
            raise Exception(f'cannot run to_hashcode on {value} before init salt')
        return hashlib.sha512(str.encode(str(cls.salt) + str(value))).hexdigest()
