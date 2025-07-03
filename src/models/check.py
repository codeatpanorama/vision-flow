from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CheckDetails(BaseModel):
    # Making id and documentId optional so that CheckDetails can be instantiated
    # before these values are known. They will be populated later in the flow.
    id: Optional[str] = Field(None, description="Check ID")
    documentId: Optional[str] = Field(None, description="Document ID")
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
    createdAt: Optional[datetime] = Field(default_factory=lambda: datetime.now(), description="Creation date")
    updatedAt: Optional[datetime] = Field(default_factory=lambda: datetime.now(), description="Last update date")
    front_path: Optional[str] = Field(None, description="Path to the check front image")
    back_path: Optional[str] = Field(None, description="Path to the check back image")