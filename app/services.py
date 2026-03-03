from sqlalchemy.orm import Session
from fastapi import HTTPException
from . import models, crud

def validate_device_placement(db: Session, rack_id: int, start_u: int, end_u: int, depth="full", position="both", exclude_device_id: int = None):
    """
    Validates that a device can be placed in a rack at the specified U-range.
    Checks for rack boundaries and overlapping devices.
    """
    # Normalize start_u and end_u
    actual_start = min(start_u, end_u)
    actual_end = max(start_u, end_u)

    # Validate range within rack limits
    rack = crud.get_rack(db, rack_id)
    if not rack:
        raise HTTPException(status_code=404, detail="Rack not found")

    if actual_start < 1 or actual_end > rack.total_units:
        raise HTTPException(
            status_code=400, 
            detail=f"Device range U{actual_start}-U{actual_end} is outside rack limits (1-{rack.total_units})"
        )

    # Check for overlaps
    # A device overlaps if:
    # 1. Any existing device is in the same U-range AND
    # 2. (Existing device is "full" depth OR New device is "full" depth OR they are on the SAME position)
    
    overlapping_devices = crud.get_overlapping_devices(db, rack_id, actual_start, actual_end, exclude_device_id=exclude_device_id)
    
    for other in overlapping_devices:
        is_overlap = False
        if depth == "full" or other.depth == "full":
            is_overlap = True
        elif position == other.position:
            is_overlap = True
        
        if is_overlap:
             raise HTTPException(
                 status_code=400, 
                 detail=f"Device overlaps with existing device '{other.hostname}' at U{other.start_u}-U{other.end_u} ({other.depth}/{other.position})"
             )
    
    return actual_start, actual_end
