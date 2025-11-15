from django.core.exceptions import ValidationError

def validate_not_whitespace(value:str):
    if value.strip() == "":
        raise ValidationError("This field cannot be an empty string.", code='invalid')