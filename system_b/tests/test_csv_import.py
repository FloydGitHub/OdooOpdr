from odoo.tests.common import TransactionCase


class TestCsvImport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.csv_import = cls.env["system_b.csv.import"]

    def test_parse_integer(self):
        result = self.csv_import._parse_integer("123")

        self.assertEqual(result, 123)

    def test_validate_string_length(self):
        result = self.csv_import._validate_string_length(
            "Test Device",
            32,
        )

        self.assertTrue(result)

    def test_get_effective_state_expired(self):
        result = self.csv_import._get_effective_state(
            "enabled",
            "2020-01-01 12:00:00",
        )

        self.assertEqual(result, "disabled")