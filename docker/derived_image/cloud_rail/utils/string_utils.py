from typing import Optional, List


class StringUtils:

    @staticmethod
    def convert_strs_to_bool(values: List[str]) -> Optional[bool]:
        if not values:
            return None
        found_true = False
        found_false = False
        for value in values:
            if value.lower() == 'true':
                found_true = True
            if value.lower() == 'false':
                found_false = True
        if found_false and found_true:
            return None
        if found_true:
            return True
        if found_false:
            return False
        return None

    @staticmethod
    def convert_to_bool(value: Optional[str]) -> Optional[bool]:
        if not value:
            return None
        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False
        return None

    @staticmethod
    def clean_markdown(value: str) -> Optional[str]:
        if not value:
            return None
        return value.replace('<', '').replace('>', '')
