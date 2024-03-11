from decimal import Decimal


class RoundedDecimal(Decimal):
    def __new__(cls, value):
        rounded_value = Decimal(value).quantize(Decimal("0.00"))
        return Decimal.__new__(cls, rounded_value)

    def __str__(self):
        return str(self.quantize(Decimal("0.00")))

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, _):
        """
        Validates a value by rounding it to two decimal places.

        Args:
            cls: The class.
            v: The value to be rounded.

        Returns:
            Decimal: The rounded value.
        """
        try:
            rounded_value = Decimal(v).quantize(Decimal("0.00"))
        except TypeError:
            rounded_value = None

        return rounded_value
