from ninja import Schema
from datetime import datetime
from typing import List,Optional
from enum import Enum

class WorkerSchema(Schema):
    employee_id : str
    first_name : str
    last_name : str
    username : str

class ProductSchema(Schema):
    item_code: str
    part_no: str
    process: List[dict]  
    customer: str
    product_family: str

class WorkerOutputSchema(Schema):
    lot_no : int
    current_status : str
    output_data : list[dict]
    current_process_index: int

# For Partname creation
class PartnameSchema(Schema):
    part_name: str
    maker: str

# For Item creation
class ItemSchema(Schema):
    item: str
    partnames: Optional[List[PartnameSchema]] = []

# For Customer creation
class CustomerSchema(Schema):
    customer_name: str
    items: Optional[List[ItemSchema]] = []

class ItemUpdateSchema(Schema):
    item: str
    partnames: Optional[List[PartnameSchema]] = []

class CustomerUpdateSchema(Schema):
    items: Optional[List[ItemUpdateSchema]] = []

class SingleItemUpdateSchema(Schema):
    new_item_name: Optional[str] = None
    partnames: Optional[List[PartnameSchema]] = None

# Schema for appending items (without requiring old item name in URL)
class AppendItemSchema(Schema):
    item: str
    partnames: Optional[List[PartnameSchema]] = []

class AppendItemsSchema(Schema):
    items: List[AppendItemSchema]  
class QRStatus(str, Enum):
    GOOD = 'GOOD'
    NO_GOOD = 'NO_GOOD'


# ==================== SELECTION SCHEMAS ====================

class PartSelectionSchema(Schema):
    """Schema for part selection dropdown"""
    part_name: str
    maker: str

class ItemSelectionSchema(Schema):
    """Schema for item selection dropdown"""
    item: str
    partnames: List[PartSelectionSchema]

class CustomerSelectionSchema(Schema):
    """Schema for customer selection dropdown"""
    customer_name: str
    items: List[ItemSelectionSchema]


# ==================== QR GENERATION SCHEMAS ====================

class QRCreateSchema(Schema):
    """Schema for creating a new QR code"""
    item_name: str
    part_name: str
    part_maker: str
    lot_no: str

class QRGenerateResponseSchema(Schema):
    """Response schema after QR generation"""
    message: str
    qr_record: dict


# ==================== VERIFICATION SCHEMAS ====================

class DataVerificationSchema(Schema):
    """Schema for first verification step - checking data exists"""
    item_name: str
    part_name: str
    part_maker: str
    lot_no: str

class QRScanVerificationSchema(Schema):
    """Schema for second verification step - scanning QR"""
    qr_uuid: str
    scanned_data: dict

class DataVerificationResponseSchema(Schema):
    """Response for data verification step"""
    verified: bool
    message: str
    data: Optional[dict] = None

class QRScanResponseSchema(Schema):
    """Response for QR scan verification step"""
    verified: bool
    status: Optional[str] = None
    message: str
    qr_data: Optional[dict] = None
    mismatches: Optional[List[str]] = None


# ==================== QR RETRIEVAL SCHEMAS ====================

class PartInfoSchema(Schema):
    """Schema for part information in QR responses"""
    name: str
    maker: str

class QRCodeResponseSchema(Schema):
    """Schema for single QR code response"""
    qr_uuid: str
    item_name: str
    part: PartInfoSchema
    lot_no: str
    status: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    created_by: Optional[str] = None
    qr_image_url: Optional[str] = None
    qr_data: Optional[dict] = None

class QRCodeListResponseSchema(Schema):
    """Schema for list of QR codes response"""
    count: int
    status_filter: Optional[str] = None
    qr_codes: List[QRCodeResponseSchema]


# ==================== SEARCH SCHEMAS ====================

class QRSearchResultSchema(Schema):
    """Schema for search result item"""
    qr_uuid: str
    item_name: str
    part_name: str
    lot_no: str
    status: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime

class QRSearchResponseSchema(Schema):
    """Schema for search response"""
    query: str
    count: int
    results: List[QRSearchResultSchema]


# ==================== STATISTICS SCHEMAS ====================

class StatusCountSchema(Schema):
    """Schema for status counts"""
    GOOD: int
    NO_GOOD: int

class QRStatisticsSchema(Schema):
    """Schema for QR statistics response"""
    total_qr_codes: int
    verified: int
    unverified: int
    by_status: StatusCountSchema
    verification_rate: float
    good_percentage: float


# ==================== BATCH VERIFICATION SCHEMAS ====================

class BatchVerifyItemSchema(Schema):
    """Schema for individual item in batch verification"""
    qr_uuid: str
    status: QRStatus
    rejection_reason: Optional[str] = None

class BatchVerifyRequestSchema(Schema):
    """Schema for batch verification request"""
    verifications: List[BatchVerifyItemSchema]

class BatchVerifyResultSchema(Schema):
    """Schema for individual batch verification result"""
    qr_uuid: str
    status: str
    success: bool
    message: Optional[str] = None

class BatchVerifyResponseSchema(Schema):
    """Schema for batch verification response"""
    success_count: int
    error_count: int
    results: List[BatchVerifyResultSchema]
    errors: Optional[List[dict]] = None


# ==================== ERROR RESPONSE SCHEMA ====================

class ErrorResponseSchema(Schema):
    """Schema for error responses"""
    error: str
    details: Optional[str] = None


# ==================== DELETE RESPONSE SCHEMA ====================

class DeleteResponseSchema(Schema):
    """Schema for delete response"""
    message: str