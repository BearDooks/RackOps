from sqlalchemy.orm import Session, joinedload
from . import models, schemas, services
import json
from fastapi import HTTPException
from .auth import get_password_hash

def log_audit(db: Session, username: str, action: str, resource_type: str, resource_id: int, details: dict):
    db_log = models.AuditLog(
        username=username,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=json.dumps(details)
    )
    db.add(db_log)
    # Note: We don't commit here, we rely on the parent transaction

def get_site(db: Session, site_id: int):
    return db.query(models.Site).filter(models.Site.id == site_id).first()

def get_sites(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Site).offset(skip).limit(limit).all()

def create_site(db: Session, site: schemas.SiteCreate, username: str = "system"):
    db_site = models.Site(**site.model_dump())
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    log_audit(db, username, "CREATE", "Site", db_site.id, site.model_dump())
    db.commit()
    return db_site

def get_rack(db: Session, rack_id: int):
    # Eager load devices to be efficient if needed, though get_rack usually just needs rack info
    # For full efficiency in rack view, we might want to join, but keeping it simple for now
    # unless specifically asked. The main N+1 issue was in get_racks (list view).
    return db.query(models.Rack).filter(models.Rack.id == rack_id).first()

def get_racks(db: Session, site_id: int):
    # N+1 Fix: Use joinedload to fetch devices with racks in a single query
    return db.query(models.Rack).options(joinedload(models.Rack.devices)).filter(models.Rack.site_id == site_id).all()

def create_rack(db: Session, rack: schemas.RackCreate, username: str = "system"):
    existing = db.query(models.Rack).filter(
        models.Rack.site_id == rack.site_id,
        models.Rack.row == rack.row,
        models.Rack.number == rack.number
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Rack '{rack.row}-{rack.number}' already exists in this site.")

    db_rack = models.Rack(**rack.model_dump())
    db.add(db_rack)
    db.commit()
    db.refresh(db_rack)
    log_audit(db, username, "CREATE", "Rack", db_rack.id, rack.model_dump())
    db.commit()
    return db_rack

def update_site(db: Session, site_id: int, site: schemas.SiteCreate, username: str = "system"):
    db_site = get_site(db, site_id)
    if not db_site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    update_data = site.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_site, key, value)
        
    db.commit()
    db.refresh(db_site)
    log_audit(db, username, "UPDATE", "Site", site_id, update_data)
    db.commit()
    return db_site

def delete_site(db: Session, site_id: int, username: str = "system"):
    db_site = get_site(db, site_id)
    if not db_site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    det = {"name": db_site.name}
    db.delete(db_site)
    db.commit()
    log_audit(db, username, "DELETE", "Site", site_id, det)
    db.commit()
    return db_site

def update_rack(db: Session, rack_id: int, rack: schemas.RackCreate, username: str = "system"):
    db_rack = get_rack(db, rack_id)
    if not db_rack:
        raise HTTPException(status_code=404, detail="Rack not found")
        
    existing = db.query(models.Rack).filter(
        models.Rack.site_id == rack.site_id,
        models.Rack.row == rack.row,
        models.Rack.number == rack.number,
        models.Rack.id != rack_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Rack '{rack.row}-{rack.number}' already exists in this site.")

    if hasattr(rack, 'total_units') and rack.total_units is not None:
        max_device_u = 0
        if db_rack.devices:
            max_device_u = max(device.end_u for device in db_rack.devices)
        if rack.total_units < max_device_u:
            raise HTTPException(status_code=400, detail=f"Cannot shrink rack to {rack.total_units}U. There is a device occupying U{max_device_u}.")

    update_data = rack.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_rack, key, value)
        
    db.commit()
    db.refresh(db_rack)
    log_audit(db, username, "UPDATE", "Rack", rack_id, update_data)
    db.commit()
    return db_rack

def delete_rack(db: Session, rack_id: int, username: str = "system"):
    db_rack = get_rack(db, rack_id)
    if not db_rack:
        raise HTTPException(status_code=404, detail="Rack not found")
    
    det = {"row": db_rack.row, "number": db_rack.number}
    db.delete(db_rack)
    db.commit()
    log_audit(db, username, "DELETE", "Rack", rack_id, det)
    db.commit()
    return db_rack

def get_device(db: Session, device_id: int):
    return db.query(models.Device).filter(models.Device.id == device_id).first()

def get_overlapping_devices(db: Session, rack_id: int, start_u: int, end_u: int, exclude_device_id: int = None):
    query = db.query(models.Device).filter(
        models.Device.rack_id == rack_id,
        models.Device.start_u <= end_u,
        models.Device.end_u >= start_u
    )

    if exclude_device_id:
        query = query.filter(models.Device.id != exclude_device_id)

    return query.all()

def check_overlap(db: Session, rack_id: int, start_u: int, end_u: int, exclude_device_id: int = None):
    # Backward compatibility, though we should transition to services.validate_device_placement
    # which now handles half-rack logic.
    query = db.query(models.Device).filter(
        models.Device.rack_id == rack_id,
        models.Device.start_u <= end_u,
        models.Device.end_u >= start_u
    )

    if exclude_device_id:
        query = query.filter(models.Device.id != exclude_device_id)

    return query.first()

def create_device(db: Session, device: schemas.DeviceCreate, username: str = "system"):
    # Business logic moved to service layer
    actual_start, actual_end = services.validate_device_placement(
        db, device.rack_id, device.start_u, device.end_u, device.depth, device.position
    )
    device.start_u = actual_start
    device.end_u = actual_end

    db_device = models.Device(**device.model_dump())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    log_audit(db, username, "CREATE", "Device", db_device.id, device.model_dump())
    db.commit()
    return db_device

def update_device(db: Session, device_id: int, device_update: schemas.DeviceUpdate, username: str = "system"):
    db_device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not db_device:
        return None

    # Business logic moved to service layer
    actual_start, actual_end = services.validate_device_placement(
        db, device_update.rack_id, device_update.start_u, device_update.end_u, device_update.depth, device_update.position, exclude_device_id=device_id
    )
    device_update.start_u = actual_start
    device_update.end_u = actual_end

    # Update fields
    update_data = device_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_device, key, value)

    db.commit()
    db.refresh(db_device)
    log_audit(db, username, "UPDATE", "Device", device_id, update_data)
    db.commit()
    return db_device

def delete_device(db: Session, device_id: int, username: str = "system"):
    device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if device:
        det = {"hostname": device.hostname, "serial": device.serial_number}
        db.delete(device)
        db.commit()
        log_audit(db, username, "DELETE", "Device", device_id, det)
        db.commit()
        return device
    return None

def get_audit_logs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

def search_devices(db: Session, query: str):
    if not query:
        return []
    
    search_pattern = f"%{query}%"
    results = db.query(models.Device, models.Rack, models.Site)\
        .join(models.Rack, models.Device.rack_id == models.Rack.id)\
        .join(models.Site, models.Rack.site_id == models.Site.id)\
        .filter(
            (models.Device.hostname.ilike(search_pattern)) |
            (models.Device.serial_number.ilike(search_pattern)) |
            (models.Device.asset_tag.ilike(search_pattern)) |
            (models.Device.ip_address.ilike(search_pattern)) |
            (models.Device.oob_ip.ilike(search_pattern)) |
            (models.Device.owner.ilike(search_pattern)) |
            (models.Device.notes.ilike(search_pattern))
        ).limit(10).all()
        
    response = []
    for device, rack, site in results:
        response.append({
            "id": device.id,
            "hostname": device.hostname,
            "make": device.make,
            "model": device.model,
            "type": device.type,
            "owner": device.owner,
            "ip_address": device.ip_address,
            "serial_number": device.serial_number,
            "start_u": device.start_u,
            "end_u": device.end_u,
            "depth": device.depth,
            "position": device.position,
            "rack_id": rack.id,
            "rack_name": f"{rack.row}-{rack.number}",
            "site_id": site.id,
            "site_name": site.name
        })
    return response

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        hashed_password=hashed_password,
        role=user.role,
        is_active=user.is_active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
