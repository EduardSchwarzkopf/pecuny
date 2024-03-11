from decimal import Decimal


class RoundedDecimal(Decimal):
    """
    A subclass of Decimal that rounds all instances to
    two decimal places upon instantiation.

    This class is designed to ensure that all decimal values are
    automatically rounded to two decimal places, making it particularly useful
    for financial calculations where precision is crucial but only to a certain extent.

    Example:
        price = RoundedDecimal('3.14159')
        print(price)  # Output: 3.14
    """

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
        Validates and rounds a value to two decimal places.

        This method is particularly useful for Pydantic models or other validation frameworks
        where custom validation logic is required.

        Args:
            cls: The class itself, allowing this method to be called on
            the class rather than an instance.

            v: The value to be validated and rounded.

        Returns:
            RoundedDecimal: The validated and rounded value.

        Raises:
            TypeError: If the input value cannot be converted to a Decimal.
        """
        try:
            rounded_value = Decimal(v).quantize(Decimal("0.00"))
        except TypeError as e:
            raise TypeError(f"Invalid input for RoundedDecimal: {v}") from e

        return cls(rounded_value)
