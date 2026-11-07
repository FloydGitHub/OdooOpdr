# OdooOpdr
Odoo-opdracht voor de stage­sollicitatie bij Codeforward.

## 1. Vereisten

Voor het installeren en gebruiken van deze Odoo-module zijn de volgende dingen nodig op u computer:

- Odoo 20.0 (inclusief een werkende PostgreSQL-database). 
- Python.

## 2. Installatie

Volg de onderstaande stappen om de module aan Odoo toe te voegen:

- Download of clone deze GitHub-repository.
- Plaats de map System_b in een map die Odoo gebruikt voor modules (addons).
- Controleer of het pad naar deze map is opgenomen in addons_path in het configuratiebestand odoo.conf. Als dit niet het geval is, voeg dan het pad toe. Indien nodig kun je hier ook het pad naar het logbestand (logfile aanpassen.
- Herstart de Odoo-server zodat de nieuwe module wordt ingelezen.
- Open Odoo in de browser en ga naar Apps.
- Werk de lijst met beschikbare apps bij.
- Zoek naar System B en installeer de module.
- Na het installeren is de module beschikbaar in Odoo.

## 3. Configuratie

Na de installatie moeten de instellingen voor de CSV-import worden ingevuld.
Ga hiervoor naar de algemene instellingen van Odoo en zoek naar de instellingen van System B.
Hier kunnen de volgende dingen worden ingevoerd:

- CSV Folder Path: het volledige pad naar de map waarin de CSV-bestanden van een delivery staan. Deze map moet zowel devices.csv als content.csv bevatten.
- CSV Delimiter: het scheidingsteken dat in de CSV-bestanden wordt gebruikt. Standaard is dit een komma (,).

