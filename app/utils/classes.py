import csv
from dataclasses import fields
from decimal import Decimal
from io import StringIO
from typing import List

from pydantic_core import core_schema

from app.utils.dataclasses_utils import ImportedTransaction


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

    def __new__(cls, value: str | float | int | Decimal):
        if isinstance(value, str):
            value = value.replace(",", "")
        rounded_value = Decimal(value).quantize(Decimal("0.00"))
        return Decimal.__new__(cls, rounded_value)

    def __str__(self) -> str:
        return str(self.quantize(Decimal("0.00")))

    @classmethod
    def __get_pydantic_core_schema__(cls, _source, _handler):
        return core_schema.no_info_after_validator_function(
            cls._validate, core_schema.decimal_schema()
        )

    @classmethod
    def _validate(cls, v: str | float | int | Decimal):
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
            if isinstance(v, str):
                v = v.replace(",", "")
            rounded_value = Decimal(v).quantize(Decimal("0.00"))
        except TypeError as e:
            raise TypeError(f"Invalid input for RoundedDecimal: {v}") from e

        return cls(rounded_value)

    @classmethod
    def _serialize(cls, value):
        """
        Class method to serialize a value.

        This class method serializes a given value.

        Args:
            value: The value to be serialized.

        Returns:
            The serialized value.
        """

        return value


class TransactionCSV:
    def __init__(self, transactions: List[ImportedTransaction]):
        self.transactions = transactions

    def calculate_total_amount(self) -> RoundedDecimal:
        """
        Calculate the sum of all transaction amounts.

        Returns:
            RoundedDecimal: The total amount of all transactions.
        """
        total_amount = sum(
            Decimal(transaction.amount)
            for transaction in self.transactions
            if transaction.amount is not None
        )
        return RoundedDecimal(total_amount)

    def generate_csv_content(self) -> str:
        """
        Generate the CSV content from the transactions.

        Returns:
            str: The CSV content as a string.
        """
        output = StringIO()
        writer = csv.writer(output, delimiter=";")

        field_names = [f.name for f in fields(ImportedTransaction)]

        writer.writerow(field_names)

        for transaction in self.transactions:
            writer.writerow(
                [getattr(transaction, field_name) for field_name in field_names]
            )

        return output.getvalue()

    def save_to_file(self, file_path: str):
        """
        Save the CSV content to a file.

        Args:
            file_path (str): The path to the file where the CSV content will be saved.
        """
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(self.generate_csv_content())
