import logging
import os
import csv

from datetime import datetime, timezone

from odoo import api, models, fields
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class CsvImport(models.AbstractModel):
    _name = "system_b.csv.import"
    _description = "System B CSV Import Service"


    # functie om het ingevoerde pad naar de map waar de CSV's in staan en de 
    # ingevoerde delimiter/scheidingsteken (indien niks ingevoerd ,) in settings op te halen
    @api.model
    def _get_import_settings(self):
        """Read the CSV import settings from Odoo."""

        parameters = self.env["ir.config_parameter"].sudo()

        folder_path = parameters.get_str(
            "system_b.csv_folder_path"
        )

        delimiter = parameters.get_str(
            "system_b.csv_delimiter",
            default=",",
        )

        if not folder_path:
            raise UserError(
                "Please enter the CSV import folder path in Settings."
            )

        if not os.path.isdir(folder_path):
            raise UserError(
                "The CSV folder you entered does not exist: %s"
                % folder_path
            )

        if not delimiter or len(delimiter) != 1:
            raise UserError(
                "The CSV delimiter must contain exactly one character."
            )

        return folder_path, delimiter


    # Deze methode zorgt dat de paden naar CSV bestanden worden klaargemaakt
    @api.model
    def _get_delivery_files(self):

        folder_path, delimiter = self._get_import_settings()

        devices_path = os.path.join(
            folder_path,
            "devices.csv",
        )

        content_path = os.path.join(
            folder_path,
            "content.csv",
        )


        for file_path in (devices_path, content_path):
            if not os.path.isfile(file_path):
                raise UserError(
                    "CSV file not found: %s"
                    % file_path
                )

        _logger.info(
            "CSV files found in %s.",
            folder_path,
        )

        return {
            "devices": devices_path,
            "content": content_path,
            "delimiter": delimiter,
        }



    # Leest een CSV bestand en returned alle rows als een lijst
    @staticmethod
    def _read_csv_rows(file_path, delimiter):


        rows = []

        try:
            with open(
                file_path,
                mode="r",
                encoding="utf-8",
                newline="",
            ) as csv_file:

                reader = csv.reader(
                    csv_file,
                    delimiter=delimiter,
                    quotechar='"',
                    skipinitialspace=True,
                )

                for row_number, row in enumerate(reader, start=1):

                    row = [value.strip() for value in row]

                    if len(row) != 6:
                        _logger.error(
                            "Invalid row in %s at row %s: "
                            "expected 6 columns, found %s. Row skipped.",
                            file_path,
                            row_number,
                            len(row),
                        )
                        continue

                    rows.append((row_number, row))

        except (OSError, UnicodeError, csv.Error) as error:
            _logger.exception(
                "Could not read CSV file: %s",
                file_path,
            )
            raise UserError(
                "Could not read CSV file %s: %s"
                % (file_path, error)
            )
        # OSError: het bestand kan niet worden geopend.
        # UnicodeError: de tekstcodering kan niet worden verwerkt.
        # csv.Error: er is een fout in de CSV-structuur of opmaak

        _logger.info(
            "Read %s valid rows from %s.",
            len(rows),
            file_path,
        )

        return rows

    # Zet een string om naar een int.
    @staticmethod
    def _parse_integer(value):
        try:
            return int(value)
        except Exception:
            raise ValueError("Can't convert string to int")

    # Zet een string om naar een Odoo-DateTime.
    @api.model
    def _parse_datetime(self, value):

        try:
            parsed_date = datetime.fromisoformat(value)

            if parsed_date.tzinfo is not None:
                parsed_date = parsed_date.astimezone(
                    timezone.utc
                ).replace(tzinfo=None)

            return fields.Datetime.to_string(parsed_date)

        except Exception:
            raise ValueError(
                "Invalid datetime value: %s" % value
            )

    # Controleert of een string niet langer is dan toegestaan.
    @staticmethod
    def _validate_string_length(value, max_length):
        return len(value) <= max_length or not value

    # Controleert als de state niet deleted is, 
    # dan of de expire_date al is geweest en zet de state dan op disabled indien nodig
    @api.model
    def _get_effective_state(self, state, expire_date):

        allowed_states = [
            "enabled",
            "disabled",
            "deleted",
        ]

        state = state.strip().lower()

        if state not in allowed_states:
            raise ValueError(
                "Invalid state value: %s" % state
            )

        if state != "deleted":

            expiration = fields.Datetime.to_datetime(
                expire_date
            )

            now = fields.Datetime.to_datetime(
                fields.Datetime.now()
            )

            if expiration < now:
                _logger.info(
                    "State changed to disabled because the expiration date has passed. "
                    "expiration date was: %s.",
                    expiration,
                    )
                return "disabled"

        return state


    # Maakt de nieuwe Device-gegevens aan in Odoo en werkt bestaande Devices bij indien nodig.
    @api.model
    def _import_devices(self, rows):

        Device = self.env["system_b.device"]

        created = 0
        updated = 0
        skipped = 0

        for row_number, row in rows:

            try:
                with self.env.cr.savepoint():

                    device_id = self._parse_integer(row[0])

                    values = {
                        "device_id": device_id,
                        "name": row[1],
                        "description": row[2],
                        "code": row[3],
                        "expire_date": self._parse_datetime(row[4]),
                    }

                    # Controleert de naam van device niet te lang is.
                    if not self._validate_string_length(values["name"], 32):
                        skipped += 1
                        _logger.error(
                            "Device name exceeds maximum length of 32 characters. "
                            "CSV row %s was skipped.",
                            row_number,
                        )
                        continue

                    # Controleert of de beschrijving van device niet te lang is.
                    if not self._validate_string_length(values["description"], 128):
                        skipped += 1
                        _logger.error(
                            "Device description exceeds maximum length of 128 characters. "
                            "CSV row %s was skipped.",
                            row_number,
                        )
                        continue

                    # Controleert of de code van device niet te lang is.
                    if not self._validate_string_length(values["code"], 30):
                        skipped += 1
                        _logger.error(
                            "Device code exceeds maximum length of 30 characters. "
                            "CSV row %s was skipped.",
                            row_number,
                        )
                        continue

                    values["state"] = self._get_effective_state(
                        row[5],
                        values["expire_date"],
                    )

                    #id staat al in odoo check
                    existing_device = Device.search(
                        [("device_id", "=", device_id)],
                    )

                    #dubbele code check
                    duplicate_code = Device.search([
                        ("code", "=", values["code"]),
                        ("device_id", "!=", device_id),
                    ])

                    if duplicate_code:
                        skipped += 1

                        _logger.error(
                            "Device code %s is already assigned to device %s. "
                            "Assign a new code to device %s. CSV row %s was skipped.",
                            values["code"],
                            duplicate_code.device_id,
                            device_id,
                            row_number,
                        )
                        
                        continue


                    if existing_device:
                        existing_device.write(values)
                        updated += 1

                        _logger.info(
                            "Device %s updated.",
                            device_id,
                        )

                    else:
                        Device.create(values)
                        created += 1

                        _logger.info(
                            "Device %s created.",
                            device_id,
                        )

            except (ValueError, TypeError) as error:
                skipped += 1

                _logger.error(
                    "Invalid Device data in row %s: %s. This row was skipped.",
                    row_number,
                    error,
                )

            except Exception:
                skipped += 1

                _logger.exception(
                    "Could not import Device from CSV row %s. This row was skipped.",
                    row_number,
                )

        _logger.info(
            "Device import completed. Created: %s, updated: %s, skipped: %s.",
            created,
            updated,
            skipped,
        )


    # Maakt de Content-gegevens aan in Odoo en werkt bestaande Content bij indien nodig.
    @api.model
    def _import_content(self, rows):

        Content = self.env["system_b.content"]
        Device = self.env["system_b.device"]

        created = 0
        updated = 0
        skipped = 0

        for row_number, row in rows:

            try:
                with self.env.cr.savepoint():

                    content_id = self._parse_integer(row[0])
                    device_id = self._parse_integer(row[3])

                    #Controleerd of het bijbehorende device bestaat
                    device = Device.search(
                        [("device_id", "=", device_id)],
                    )

                    if not device:
                        raise ValueError(
                            "Device %s does not exist." % device_id
                        )

                    values = {
                        "content_id": content_id,
                        "name": row[1],
                        "description": row[2],
                        "device_id": device.id,
                        "expire_date": self._parse_datetime(row[4]),
                    }

                    # Controleert of de naam van content niet te lang is.
                    if not self._validate_string_length(values["name"], 100):
                        _logger.error(
                            "Content name exceeds maximum length of 100 characters. CSV row %s was skipped.",
                            row_number,
                        )
                        skipped += 1
                        continue

                    # Controleert of de beschrijving van content niet te lang is.
                    if not self._validate_string_length(values["description"], 128):
                        _logger.error(
                            "Content description exceeds maximum length of 128 characters. CSV row %s was skipped.",
                            row_number,
                        )
                        skipped += 1
                        continue

                    values["state"] = self._get_effective_state(
                        row[5],
                        values["expire_date"],
                    )

                    #controleert of de content al bestaat
                    existing_content = Content.search(
                        [("content_id", "=", content_id)],
                    )

                    if existing_content:
                        existing_content.write(values)
                        updated += 1

                        _logger.info(
                            "Content %s updated.",
                            content_id,
                        )

                    else:
                        Content.create(values)
                        created += 1

                        _logger.info(
                            "Content %s created.",
                            content_id,
                        )

            except (ValueError, TypeError) as error:
                skipped += 1

                _logger.error(
                    "Invalid Content data in row %s: %s. This row was skipped.",
                    row_number,
                    error,
                )

            except Exception:
                skipped += 1

                _logger.exception(
                    "Could not import Content from CSV row %s. This row was skipped.",
                    row_number,
                )

        _logger.info(
            "Content import completed. Created: %s, updated: %s, skipped: %s.",
            created,
            updated,
            skipped,
        )


    # Importeert een delivery (devices en content).
    @api.model
    def _import_delivery(self):

        files = self._get_delivery_files()

        device_rows = self._read_csv_rows(
            files["devices"],
            files["delimiter"],
        )

        content_rows = self._read_csv_rows(
            files["content"],
            files["delimiter"],
        )


        _logger.info(
            "Starting CSV import. Device file: %s, Content file: %s.",
            files["devices"],
            files["content"],
        )

        self._import_devices(device_rows)
        self._import_content(content_rows)

        _logger.info(
            "CSV import completed. Device file: %s, Content file: %s.",
            files["devices"],
            files["content"],
        )



