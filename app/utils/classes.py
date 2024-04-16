from decimal import Decimal
from typing import List, Tuple


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

    def __str__(self):
        return str(self.quantize(Decimal("0.00")))

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: str | float | int | Decimal, _):
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


class TransactionCSV:
    def __init__(self, transactions: List[Tuple[str, int, str, str, float, int]]):
        self.transactions = transactions

    def calculate_total_amount(self) -> float:
        """
        Calculate the sum of all transaction amounts.

        Returns:
            float: The total amount of all transactions.
        """
        return sum(transaction[4] for transaction in self.transactions)

    def generate_csv_content(self) -> str:
        """
        Generate the CSV content from the transactions.

        Returns:
            str: The CSV content as a string.
        """
        csv_content = "date;account_id;offset_account_id;reference;amount;category_id\n"
        for transaction in self.transactions:
            csv_content += f"{transaction[0]};{transaction[1]};{transaction[2]};{transaction[3]};{transaction[4]};{transaction[5]}\n"
        return csv_content

    def save_to_file(self, file_path: str):
        """
        Save the CSV content to a file.

        Args:
            file_path (str): The path to the file where the CSV content will be saved.
        """
        with open(file_path, "w") as file:
            file.write(self.generate_csv_content())
