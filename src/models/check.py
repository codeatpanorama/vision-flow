from pydantic import BaseModel, Field
from typing import Optional

class CheckDetails(BaseModel):
    payee_name: str = Field(..., description="Name of the service provider or individual receiving the check")
    amount: str = Field(..., description="Check amount in currency format (e.g., $1,145.29)")
    date: str = Field(..., description="Check date in DD/MM/YYYY format")
    check_number: str = Field(..., description="Check number from the MICR line or top of check")
    check_transit_number: str = Field(..., description="Bank transit/routing number (usually 5 digits)")
    check_institution_number: str = Field(..., description="Bank institution number (usually 3 digits)")
    check_bank_account_number: str = Field(..., description="Bank account number (format: XXX-XXX-X)")
    bank: str = Field(..., description="Complete bank name including branch information")
    company_name_address: Optional[str] = Field(None, description="Company name, address and contact information if available")
    raw_text: str = Field(..., description="Raw text from the check")