"""
HubSpot service module - handles all contact, company, deal, and file operations.

This module provides a reusable HubSpotService class that orchestrates:
  - Contact creation/lookup by email
  - Company creation/lookup by registration number
  - Deal creation with all properties
  - File upload to HubSpot cloud
  - Object association (contact->company, deal->company)

Can run in dry-run mode (no actual HubSpot API calls) for testing.
"""
from __future__ import annotations

import json
import mimetypes
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, NamedTuple
import logging

logger = logging.getLogger(__name__)


class HubSpotConfig(NamedTuple):
    """HubSpot API credentials and settings."""
    token: str
    base_url: str = "https://api.hubapi.com"
    portal_id: str = "145268660"
    deal_pipeline: str = "default"
    deal_stage: str = "appointmentscheduled"
    deal_owner_id: str = "29362124"
    file_folder_path: str = "/hubpush"
    dry_run: bool = False


class HubSpotResult(NamedTuple):
    """Result of a HubSpot operation."""
    ok: bool
    contact_id: str | None = None
    company_id: str | None = None
    deal_id: str | None = None
    error: str | None = None
    details: dict[str, Any] | None = None


class HubSpotService:
    """
    Reusable HubSpot integration service.
    
    Usage:
        config = HubSpotConfig(token="pat-eu1-...")
        hs = HubSpotService(config)
        result = hs.push_row(row_dict, file_root_path, dry_run=False)
    """

    MANDATE_KEYS = ("mandate", "debit", "order")
    BANK_KEYS = ("bank", "account", "confirmation", "proof", "statement")
    SUPPORTED_DOC_EXTS = {".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}

    # Standard HubSpot v4 association type IDs (HUBSPOT_DEFINED)
    ASSOC_CONTACT_TO_COMPANY = 279   # contact primary company
    ASSOC_DEAL_TO_COMPANY = 341      # deal primary company

    BRAND_MAP: dict[str, str] = {
        "wimpy":           "Wimpy",
        "steers":          "Steers",
        "debonairs":       "Debonairs Pizza",
        "debonairs pizza": "Debonairs Pizza",
        "fishaways":       "Fishaways",
        "milky lane":      "Milky Lane",
        "mugg & bean":     "Mugg & Bean",
        "mugg and bean":   "Mugg & Bean",
        "netcafe":         "Netcafé",
        "netcafé":         "Netcafé",
        "paul":            "PAUL",
        "vovo telo":       "Vovo Telo",
        "fego caffe":      "Fego Caffé",
        "fego caffé":      "Fego Caffé",
        "turn 'n tender":  "Turn 'n Tender",
        "turn n tender":   "Turn 'n Tender",
        "mythos":          "Mythos",
        "salsa mexican grill": "Salsa Mexican Grill",
        "salsa":           "Salsa Mexican Grill",
        "lupa osteria":    "Lupa Osteria",
        "lupa":            "Lupa Osteria",
        "coffee couture":  "Coffee Couture",
        "famous brands multi": "Famous brands Multi",
    }

    def __init__(self, config: HubSpotConfig):
        self.config = config
        self.auth_headers = {
            "Authorization": f"Bearer {config.token}",
            "Content-Type": "application/json",
        }

    def _log_request(self, method: str, path: str) -> None:
        logger.debug(f"   --> {method} {self.config.base_url}{path}")

    def api_get(self, path: str) -> dict[str, Any]:
        """GET request to HubSpot API."""
        if self.config.dry_run:
            logger.info(f"   [DRY-RUN] GET {path}")
            return {}

        self._log_request("GET", path)
        req = urllib.request.Request(
            f"{self.config.base_url}{path}", headers=self.auth_headers
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            logger.error(f"       HTTP {e.code}: {e.read().decode()[:600]}")
            return {}

    def api_post(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        """POST request to HubSpot API."""
        if self.config.dry_run:
            logger.info(f"   [DRY-RUN] POST {path} with {len(str(data))} bytes")
            # Return mock ID for dry-run
            if "/contacts" in path and "/search" not in path:
                return {"id": "DRY_RUN_CONTACT_ID"}
            elif "/companies" in path and "/search" not in path:
                return {"id": "DRY_RUN_COMPANY_ID"}
            elif "/deals" in path and "/search" not in path:
                return {"id": "DRY_RUN_DEAL_ID"}
            return {}

        self._log_request("POST", path)
        body = json.dumps(data).encode()
        req = urllib.request.Request(
            f"{self.config.base_url}{path}",
            data=body,
            headers=self.auth_headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            logger.error(f"       HTTP {e.code}: {e.read().decode()[:600]}")
            return {}

    def api_put(
        self, path: str, data: list[Any] | dict[str, Any] | None = None
    ) -> bool:
        """PUT request to HubSpot API."""
        if self.config.dry_run:
            logger.info(f"   [DRY-RUN] PUT {path}")
            return True

        self._log_request("PUT", path)
        body = json.dumps(data).encode() if data is not None else b"[]"
        req = urllib.request.Request(
            f"{self.config.base_url}{path}",
            data=body,
            headers=self.auth_headers,
            method="PUT",
        )
        try:
            with urllib.request.urlopen(req) as _:
                return True
        except urllib.error.HTTPError as e:
            logger.error(f"       HTTP {e.code}: {e.read().decode()[:600]}")
            return False

    def upload_file(self, file_path: Path) -> str | None:
        """
        Upload a file to HubSpot Files v3 API.
        Returns the public URL of the uploaded file, or None on failure.
        """
        if self.config.dry_run:
            logger.info(f"   [DRY-RUN] Upload file {file_path.name}")
            return f"https://hubspot.dry-run/{file_path.name}"

        logger.info(f"   --> POST {self.config.base_url}/files/v3/files  [{file_path.name}]")
        mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        file_bytes = file_path.read_bytes()

        boundary = "HubPushBoundary7MA4YWxkTrZu0gW"
        CRLF = b"\r\n"

        def part_text(name: str, value: str) -> bytes:
            return (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                f"{value}"
            ).encode() + CRLF

        options = json.dumps({
            "access": "PUBLIC_INDEXABLE",
            "overwrite": False,
            "duplicateValidationStrategy": "NONE",
            "duplicateValidationScope": "ENTIRE_PORTAL",
        })

        body = (
            part_text("folderPath", self.config.file_folder_path)
            + part_text("options", options)
            + (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
                f"Content-Type: {mime_type}\r\n\r\n"
            ).encode()
            + file_bytes
            + CRLF
            + f"--{boundary}--\r\n".encode()
        )

        upload_headers = {
            "Authorization": f"Bearer {self.config.token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }

        req = urllib.request.Request(
            f"{self.config.base_url}/files/v3/files",
            data=body,
            headers=upload_headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read())
                file_url = result.get("url") or result.get("id")
                logger.info(f"       Uploaded OK -> {file_url}")
                return str(file_url) if file_url else None
        except urllib.error.HTTPError as e:
            logger.error(f"       HTTP {e.code}: {e.read().decode()[:600]}")
            return None

    def find_contact_by_email(self, email: str) -> str | None:
        """Search for existing contact by email. Returns contact ID or None."""
        resp = self.api_post("/crm/v3/objects/contacts/search", {
            "filterGroups": [{"filters": [
                {"propertyName": "email", "operator": "EQ", "value": email}
            ]}],
            "properties": ["email", "firstname"],
            "limit": 1,
        })
        results = resp.get("results", [])
        if results:
            logger.info(f"       Found existing contact: id={results[0]['id']}")
            return results[0]["id"]
        return None

    def find_company_by_registration(self, reg_no: str) -> str | None:
        """Search for existing company by registration number. Returns company ID or None."""
        resp = self.api_post("/crm/v3/objects/companies/search", {
            "filterGroups": [{"filters": [
                {"propertyName": "company_registration_no_", "operator": "EQ", "value": reg_no}
            ]}],
            "properties": ["name", "company_registration_no_"],
            "limit": 1,
        })
        results = resp.get("results", [])
        if results:
            logger.info(f"       Found existing company: id={results[0]['id']}")
            return results[0]["id"]
        return None

    def create_contact(self, email: str, first_name: str, mobile: str = "") -> str | None:
        """Create a new contact. Returns contact ID or None on failure."""
        resp = self.api_post("/crm/v3/objects/contacts", {"properties": {
            "firstname": first_name or "Undefined",
            "lastname": "Undefined",
            "email": email,
            "mobilephone": mobile,
        }})
        contact_id = resp.get("id")
        if contact_id:
            logger.info(f"       Created contact: id={contact_id}")
        return contact_id

    def create_company(
        self,
        name: str,
        reg_no: str,
        brand: str = "",
        domain: str = "",
        vat: str = "",
        phone: str = ""
    ) -> str | None:
        """Create a new company. Returns company ID or None on failure."""
        resp = self.api_post("/crm/v3/objects/companies", {"properties": {
            "name": name or "Undefined",
            "domain": domain,
            "company_registration_no_": reg_no,
            "vat_number": vat,
            "brand__famous_brands_": brand,
            "phone": phone,
        }})
        company_id = resp.get("id")
        if company_id:
            logger.info(f"       Created company: id={company_id}")
        return company_id

    def create_deal(
        self,
        restaurant_name: str,
        properties: dict[str, str] | None = None,
    ) -> str | None:
        """Create a new deal. Returns deal ID or None on failure."""
        deal_props = {
            "dealname": restaurant_name or "Undefined",
            "pipeline": self.config.deal_pipeline,
            "dealstage": self.config.deal_stage,
            "hubspot_owner_id": self.config.deal_owner_id,
        }
        if properties:
            deal_props.update(properties)

        resp = self.api_post("/crm/v3/objects/deals", {"properties": deal_props})
        deal_id = resp.get("id")
        if deal_id:
            logger.info(f"       Created deal: id={deal_id}")
        return deal_id

    def associate_objects(
        self,
        from_type: str,
        from_id: str,
        to_type: str,
        to_id: str,
        assoc_type_id: int,
    ) -> bool:
        """Associate two HubSpot objects."""
        path = f"/crm/v4/objects/{from_type}/{from_id}/associations/{to_type}/{to_id}"
        payload = [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": assoc_type_id}]
        return self.api_put(path, payload)

    def normalize_brand(self, brand: str) -> str:
        """Convert spreadsheet brand value to exact HubSpot enum label."""
        key = brand.strip().lower() if brand else ""
        return self.BRAND_MAP.get(key, brand.strip() if brand else "")

    @staticmethod
    def brand_to_domain(brand: str) -> str:
        """Convert brand name to domain."""
        slug = brand.lower().replace(" ", "").strip() if brand else ""
        return f"www.{slug}.co.za" if slug else ""

    @staticmethod
    def safe(val: object, fallback: str = "Undefined") -> str:
        """Convert value to string safely."""
        s = str(val).strip() if val is not None else ""
        return s if s else fallback

    @staticmethod
    def classify_folder_docs(folder: Path) -> tuple[Path | None, Path | None]:
        """
        Classify documents in a folder as mandate and bank proof.
        Returns (mandate_path, bank_proof_path).
        """
        docs = sorted(
            [
                p
                for p in folder.iterdir()
                if p.is_file() and p.suffix.lower() in HubSpotService.SUPPORTED_DOC_EXTS
            ],
            key=lambda p: p.name.lower(),
        )

        mandate = next(
            (d for d in docs if any(k in d.name.lower() for k in HubSpotService.MANDATE_KEYS)),
            None,
        )
        bank = next(
            (d for d in docs if any(k in d.name.lower() for k in HubSpotService.BANK_KEYS)),
            None,
        )

        # Fallback for mandate: prefer PDFs that do NOT match bank keywords
        if not mandate:
            non_bank = [d for d in docs if not any(k in d.name.lower() for k in HubSpotService.BANK_KEYS)]
            mandate = next((d for d in non_bank if d.suffix.lower() == ".pdf"), None)
            # Last resort: any PDF that isn't already chosen as bank
            if not mandate:
                mandate = next(
                    (d for d in docs if d.suffix.lower() == ".pdf" and d != bank), None
                )

        if not bank:
            bank = next((d for d in docs if d != mandate and d.is_file()), None)

        return mandate, bank

    def push_row(
        self,
        row: dict[str, Any],
        file_root: Path | str,
        dry_run: bool | None = None,
    ) -> HubSpotResult:
        """
        Push a single spreadsheet row to HubSpot.
        
        Steps:
          1. Extract data from row
          2. Resolve document files from subfolder
          3. Find or create Contact
          4. Find or create Company
          5. Optionally associate Contact -> Company
          6. Upload documents
          7. Create Deal with all properties
          8. Associate Deal -> Company
        
        Args:
            row: spreadsheet row as dict
            file_root: root folder containing subfolders with documents
            dry_run: override config dry_run setting (if provided)
        
        Returns:
            HubSpotResult with contact/company/deal IDs or error message
        """
        cfg = self.config
        if dry_run is not None:
            # Temporarily override for this call
            orig_dry_run = cfg.dry_run
            cfg = cfg._replace(dry_run=dry_run)
        else:
            dry_run = cfg.dry_run

        try:
            # Extract row data
            subfolder = self.safe(row.get("source subfolder"))
            company_name = self.safe(row.get("company reg name"))
            reg_no = self.safe(row.get("company registration number"))
            contact_email = self.safe(row.get("primary franchisee email address"))
            first_name = self.safe(row.get("Contact Name"))
            mobile = self.safe(row.get("Contact Number") or row.get("Mobile Number"), "")
            fis_number = self.safe(row.get("FIS Number"), "")
            restaurant_name = self.safe(row.get("Restaurant Name") or row.get("company reg name"))
            brand = self.safe(row.get("Brand"), "")
            vat = self.safe(row.get("VAT Number"), "")
            hs_brand = self.normalize_brand(brand)

            logger.info(f"Pushing: {restaurant_name} ({reg_no})")

            # Resolve files
            file_root_path = Path(file_root)
            folder_path = file_root_path / subfolder
            if not folder_path.is_dir():
                return HubSpotResult(
                    ok=False,
                    error=f"Subfolder not found: {folder_path}",
                )

            mandate_file, bank_file = self.classify_folder_docs(folder_path)
            logger.info(
                f"  Files: mandate={mandate_file.name if mandate_file else 'N/A'}, "
                f"bank={bank_file.name if bank_file else 'N/A'}"
            )

            # Contact
            contact_id = self.find_contact_by_email(contact_email)
            if not contact_id:
                contact_id = self.create_contact(contact_email, first_name, mobile)
                if not contact_id:
                    return HubSpotResult(
                        ok=False,
                        error="Failed to create contact",
                    )

            # Company
            company_id = self.find_company_by_registration(reg_no)
            if not company_id:
                company_id = self.create_company(
                    company_name, reg_no, hs_brand,
                    self.brand_to_domain(brand), vat, mobile
                )
                if not company_id:
                    return HubSpotResult(
                        ok=False,
                        contact_id=contact_id,
                        error="Failed to create company",
                    )

            # Associate contact -> company
            ok = self.associate_objects(
                "contacts", contact_id, "companies", company_id,
                self.ASSOC_CONTACT_TO_COMPANY
            )
            if not ok:
                logger.warning("Failed to associate contact->company (non-fatal)")

            # Upload files
            mandate_url = None
            if mandate_file:
                mandate_url = self.upload_file(mandate_file)
                if not mandate_url and not dry_run:
                    logger.warning("Mandate file upload failed (missing 'files' scope?)")

            bank_url = None
            if bank_file:
                bank_url = self.upload_file(bank_file)
                if not bank_url and not dry_run:
                    logger.warning("Bank file upload failed (missing 'files' scope?)")

            # Create deal
            deal_props = {
                "fis_number": fis_number,
                "fis__restaurant__number": fis_number,
                "nazmeys_store": "true",
                "solution_required": "eComm",
                "primary_acquiring_bank": "Nedbank",
                "request_type_new": "New Store",
                "store_name": restaurant_name,
                "brand__famous_brands_": hs_brand,
                "vat_number": vat,
            }
            if mandate_url:
                deal_props["debit_order_mandate"] = mandate_url
            if bank_url:
                deal_props["bank_letter"] = bank_url

            deal_id = self.create_deal(restaurant_name, deal_props)
            if not deal_id:
                return HubSpotResult(
                    ok=False,
                    contact_id=contact_id,
                    company_id=company_id,
                    error="Failed to create deal",
                )

            # Associate deal -> company
            ok = self.associate_objects(
                "deals", deal_id, "companies", company_id,
                self.ASSOC_DEAL_TO_COMPANY
            )
            if not ok:
                logger.warning("Failed to associate deal->company (non-fatal)")

            return HubSpotResult(
                ok=True,
                contact_id=contact_id,
                company_id=company_id,
                deal_id=deal_id,
            )

        finally:
            if dry_run is not None:
                # Restore original config
                self.config = cfg._replace(dry_run=orig_dry_run)
