from ninja import Schema
from datetime import datetime
from typing import List,Optional
from enum import Enum

class WorkerSchema(Schema):
    employee_id: str
    first_name: str
    last_name: str
    username: str

class ProductSchema(Schema):
    item_code: str
    part_no: str
    process: List[dict]  
    customer: str
    product_family: str

class WorkerOutputSchema(Schema):
    lot_no: int
    current_status: str
    output_data: List[dict]
    current_process_index: int

# ==================== PARTNAME SCHEMAS ====================

class PartnameSchema(Schema):
    part_name: str
    maker: str

# ==================== ITEM SCHEMAS ====================

class ItemSchema(Schema):
    item: str
    partnames: Optional[List[PartnameSchema]] = []

class ItemUpdateSchema(Schema):
    item: str
    partnames: Optional[List[PartnameSchema]] = []

class SingleItemUpdateSchema(Schema):
    new_item_name: Optional[str] = None
    partnames: Optional[List[PartnameSchema]] = None

# ==================== CUSTOMER SCHEMAS ====================

class CustomerSchema(Schema):
    customer_name: str
    items: Optional[List[ItemSchema]] = []

class CustomerUpdateSchema(Schema):
    items: Optional[List[ItemUpdateSchema]] = []

# ==================== APPEND SCHEMAS ====================

class AppendItemSchema(Schema):
    item: str
    partnames: Optional[List[PartnameSchema]] = []

class AppendItemsSchema(Schema):
    items: List[AppendItemSchema]

# ==================== QR STATUS ENUM ====================

class QRStatus(str, Enum):
    GOOD = 'GOOD'
    NO_GOOD = 'NO_GOOD'
    PENDING = 'PENDING'

# ==================== SELECTION SCHEMAS ====================

class PartSelectionSchema(Schema):
    part_name: str
    maker: str

class ItemSelectionSchema(Schema):
    item: str
    partnames: List[PartSelectionSchema]

class CustomerSelectionSchema(Schema):
    customer_name: str
    items: List[ItemSelectionSchema]

# ==================== QR GENERATION SCHEMAS ====================

class QRCreateSchema(Schema):
    item_name: str
    part_name: str
    part_maker: str
    lot_no: str

class QRGenerateResponseSchema(Schema):
    message: str
    qr_record: dict

# ==================== VERIFICATION SCHEMAS - FIXED ====================

class DataVerificationSchema(Schema):
    """Schema for first verification step - checking data exists"""
    item_name: str
    part_name: str
    part_maker: str
    lot_no: str

# NEW: ScannedDataSchema for proper validation
class ScannedPartSchema(Schema):
    """Schema for part in scanned data"""
    name: str
    maker: str

class ScannedDataSchema(Schema):
    """Schema for scanned QR data - THIS FIXES THE ISSUE"""
    item: str
    part: ScannedPartSchema  # Using your PartnameSchema structure
    lot_no: str

class QRScanVerificationSchema(Schema):
    """Schema for second verification step - scanning QR"""
    qr_uuid: str
    scanned_data: ScannedDataSchema  # CHANGED from dict to proper schema

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
    name: str
    maker: str

class QRCodeResponseSchema(Schema):
    qr_uuid: str
    item_name: str
    part: PartInfoSchema
    lot_no: str
    status: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    qr_image_url: Optional[str] = None
    qr_data: Optional[dict] = None

class QRCodeListResponseSchema(Schema):
    count: int
    status_filter: Optional[str] = None
    qr_codes: List[QRCodeResponseSchema]

# ==================== SEARCH SCHEMAS ====================

class QRSearchResultSchema(Schema):
    qr_uuid: str
    item_name: str
    part_name: str
    lot_no: str
    status: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime

class QRSearchResponseSchema(Schema):
    query: str
    count: int
    results: List[QRSearchResultSchema]

# ==================== STATISTICS SCHEMAS ====================

class StatusCountSchema(Schema):
    GOOD: int
    NO_GOOD: int

class QRStatisticsSchema(Schema):
    total_qr_codes: int
    verified: int
    unverified: int
    by_status: StatusCountSchema
    verification_rate: float
    good_percentage: float

# ==================== BATCH VERIFICATION SCHEMAS ====================

class BatchVerifyItemSchema(Schema):
    qr_uuid: str
    status: QRStatus
    rejection_reason: Optional[str] = None

class BatchVerifyRequestSchema(Schema):
    verifications: List[BatchVerifyItemSchema]

class BatchVerifyResultSchema(Schema):
    qr_uuid: str
    status: str
    success: bool
    message: Optional[str] = None

class BatchVerifyResponseSchema(Schema):
    success_count: int
    error_count: int
    results: List[BatchVerifyResultSchema]
    errors: Optional[List[dict]] = None

# ==================== ERROR RESPONSE SCHEMA ====================

class ErrorResponseSchema(Schema):
    error: str
    details: Optional[str] = None

# ==================== DELETE RESPONSE SCHEMA ====================

class DeleteResponseSchema(Schema):
    message: str

class DirectQRScanSchema(Schema):
    """Schema for direct QR scan where the QR contains all data"""
    qr_uuid: str
    item: str
    part: ScannedPartSchema  # Reuse existing ScannedPartSchema
    lot_no: str
    status: Optional[str] = None  # Optional since it might be null initially