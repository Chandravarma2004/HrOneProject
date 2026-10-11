
from datetime import datetime, timezone, timedelta

from bson import ObjectId
from fastapi import FastAPI, Request, HTTPException
from pymongo import ReturnDocument
from pymongo.errors import PyMongoError

from .db import lifespan
from .requestModel import AttendanceRequest, AttendanceCorrectionRequest


app = FastAPI(
    title="HROne Attendance API",
    lifespan=lifespan
)

UTC = timezone.utc
IST = timezone(timedelta(hours=5, minutes=30))


# ---------------- HELPER FUNCTIONS ----------------

def to_utc_datetime(value):
    """Convert a datetime or ISO timestamp string to UTC."""

    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(422, "Invalid timestamp format")

    if not isinstance(value, datetime):
        raise HTTPException(422, "Timestamp is missing or invalid")

    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


def serialize_value(value):
    """Convert MongoDB values into JSON-compatible values."""

    if isinstance(value, ObjectId):
        return str(value)

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, dict):
        return {
            key: serialize_value(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [serialize_value(item) for item in value]

    return value


def serialize_attendance(record):
    return serialize_value(record)


# ---------------- HOME API ----------------

@app.get("/")
async def home():
    return {"message": "Attendance API is running"}


# ---------------- PUNCH-IN API ----------------

@app.post("/attendance/punch-in", status_code=201)
async def punch_in(data: AttendanceRequest, request: Request):
    db = request.app.state.db
    employee_id = data.employee_id.strip()

    if not employee_id:
        raise HTTPException(422, "Employee ID cannot be empty")

    existing = await db.attendance.find_one({
        "employee_id": employee_id,
        "status": "IN_PROGRESS"
    })

    if existing:
        raise HTTPException(409, "Employee has already punched in")

    now = datetime.now(UTC)

    attendance = {
        "employee_id": employee_id,
        "punch_in": now,
        "punch_out": None,
        "status": "IN_PROGRESS",
        "created_at": now,
        "updated_at": now
    }

    result = await db.attendance.insert_one(attendance)
    attendance["_id"] = result.inserted_id

    return {
        "message": "Punch-in successful",
        "data": serialize_attendance(attendance)
    }


# ---------------- PUNCH-OUT API ----------------

@app.post("/attendance/punch-out")
async def punch_out(data: AttendanceRequest, request: Request):
    db = request.app.state.db
    employee_id = data.employee_id.strip()

    if not employee_id:
        raise HTTPException(422, "Employee ID cannot be empty")

    attendance = await db.attendance.find_one({
        "employee_id": employee_id,
        "status": "IN_PROGRESS",
        "punch_out": None
    })

    if not attendance:
        raise HTTPException(
            404,
            "No active attendance session found. Please punch in first."
        )

    punch_in_time = to_utc_datetime(attendance.get("punch_in"))
    now = datetime.now(UTC)

    # Ensure punch-in belongs to today's IST date.
    if punch_in_time.astimezone(IST).date() != now.astimezone(IST).date():
        raise HTTPException(400, "Punch-in date is not today's date")

    if now < punch_in_time:
        raise HTTPException(
            400,
            "Punch-out cannot be earlier than punch-in"
        )

    updated = await db.attendance.find_one_and_update(
        {
            "_id": attendance["_id"],
            "status": "IN_PROGRESS",
            "punch_out": None,
            "punch_in": {"$lte": now}
        },
        {
            "$set": {
                "punch_out": now,
                "status": "COMPLETED",
                "updated_at": now
            }
        },
        return_document=ReturnDocument.AFTER
    )

    if not updated:
        raise HTTPException(409, "Attendance session has changed")

    punch_in_time = to_utc_datetime(updated["punch_in"])
    punch_out_time = to_utc_datetime(updated["punch_out"])

    total_seconds = int(
        (punch_out_time - punch_in_time).total_seconds()
    )

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    return {
        "message": "Punch-out successful",
        "employee_id": employee_id,
        "punch_in": punch_in_time.isoformat(),
        "punch_out": punch_out_time.isoformat(),
        "working_hours": round(total_seconds / 3600, 2),
        "working_duration": f"{hours} hours {minutes} minutes",
        "status": updated["status"]
    }


# ---------------- GET ALL ATTENDANCE ----------------

@app.get("/attendance")
async def get_all_attendance(request: Request):
    db = request.app.state.db

    records = await db.attendance.find({}).to_list(length=1000)

    return {
        "count": len(records),
        "data": [serialize_attendance(record) for record in records]
    }


# ---------------- MANUAL CORRECTION + AUDIT LOG ----------------

@app.patch("/attendance/{attendance_id}/correction")
async def correct_attendance(
    attendance_id: str,
    data: AttendanceCorrectionRequest,
    request: Request
):
    db = request.app.state.db

    if not ObjectId.is_valid(attendance_id):
        raise HTTPException(400, "Invalid attendance ID")

    record_id = ObjectId(attendance_id)

    record = await db.attendance.find_one({"_id": record_id})

    if not record:
        raise HTTPException(404, "Attendance not found")

    new_value = to_utc_datetime(data.new_timestamp)
    old_value = record.get(data.field)

    if old_value is not None:
        old_value = to_utc_datetime(old_value)

    punch_in = record.get("punch_in")
    punch_out = record.get("punch_out")

    if punch_in is not None:
        punch_in = to_utc_datetime(punch_in)

    if punch_out is not None:
        punch_out = to_utc_datetime(punch_out)

    if data.field == "punch_in":
        if punch_out is not None and new_value > punch_out:
            raise HTTPException(
                422,
                "Punch-in cannot be later than punch-out"
            )
    else:
        if punch_in is None or new_value < punch_in:
            raise HTTPException(
                422,
                "Invalid punch-out time"
            )

    now = datetime.now(UTC)

    update = {
        data.field: new_value,
        "updated_at": now
    }

    if data.field == "punch_out":
        update["status"] = "COMPLETED"

    await db.attendance.update_one(
        {"_id": record_id},
        {"$set": update}
    )

    try:
        await db.audit_logs.insert_one({
            "attendance_id": record_id,
            "employee_id": record["employee_id"],
            "action": "MANUAL_CORRECTION",
            "field": data.field,
            "old_value": old_value,
            "new_value": new_value,
            "reason": data.reason.strip(),
            "corrected_by": data.corrected_by.strip(),
            "corrected_at": now
        })
    except PyMongoError:
        # Report the failure; the attendance update may already have succeeded.
        raise HTTPException(
            500,
            "Attendance updated, but audit log could not be saved"
        )

    return {
        "message": "Attendance corrected successfully",
        "attendance_id": attendance_id,
        "field": data.field,
        "old_value": serialize_value(old_value),
        "new_value": serialize_value(new_value)
    }


# ---------------- OVERALL ANALYTICS ----------------

@app.get("/analytics/summary")
async def attendance_summary(request: Request):
    db = request.app.state.db

    pipeline = [
        {
            "$match": {
                "status": "COMPLETED",
                "punch_in": {"$type": "date"},
                "punch_out": {"$type": "date"}
            }
        },
        {
            "$project": {
                "hours": {
                    "$divide": [
                        {"$subtract": ["$punch_out", "$punch_in"]},
                        3600000
                    ]
                }
            }
        },
        {"$match": {"hours": {"$gte": 0}}},
        {
            "$group": {
                "_id": None,
                "total_sessions": {"$sum": 1},
                "total_working_hours": {"$sum": "$hours"},
                "average_working_hours": {"$avg": "$hours"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "total_sessions": 1,
                "total_working_hours": {
                    "$round": ["$total_working_hours", 2]
                },
                "average_working_hours": {
                    "$round": ["$average_working_hours", 2]
                }
            }
        }
    ]

    cursor = await db.attendance.aggregate(pipeline)
    result = await cursor.to_list(length=1)

    if not result:
        return {
            "total_sessions": 0,
            "total_working_hours": 0,
            "average_working_hours": 0
        }

    return result[0]


# ---------------- EMPLOYEE ANALYTICS ----------------

@app.get("/analytics/employee/{employee_id}")
async def employee_analytics(employee_id: str, request: Request):
    db = request.app.state.db

    pipeline = [
        {
            "$match": {
                "employee_id": employee_id,
                "status": "COMPLETED",
                "punch_in": {"$type": "date"},
                "punch_out": {"$type": "date"}
            }
        },
        {
            "$project": {
                "hours": {
                    "$divide": [
                        {"$subtract": ["$punch_out", "$punch_in"]},
                        3600000
                    ]
                }
            }
        },
        {"$match": {"hours": {"$gte": 0}}},
        {
            "$group": {
                "_id": None,
                "total_sessions": {"$sum": 1},
                "total_working_hours": {"$sum": "$hours"},
                "average_working_hours": {"$avg": "$hours"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "total_sessions": 1,
                "total_working_hours": {
                    "$round": ["$total_working_hours", 2]
                },
                "average_working_hours": {
                    "$round": ["$average_working_hours", 2]
                }
            }
        }
    ]

    cursor = await db.attendance.aggregate(pipeline)
    result = await cursor.to_list(length=1)

    if not result:
        return {
            "employee_id": employee_id,
            "total_sessions": 0,
            "total_working_hours": 0,
            "average_working_hours": 0
        }

    return {
        "employee_id": employee_id,
        **result[0]
    }


# ---------------- DAILY ANALYTICS ----------------

@app.get("/analytics/daily")
async def daily_analytics(request: Request):
    db = request.app.state.db

    pipeline = [
        {
            "$match": {
                "status": "COMPLETED",
                "punch_in": {"$type": "date"},
                "punch_out": {"$type": "date"}
            }
        },
        {
            "$project": {
                "date": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$punch_in",
                        "timezone": "Asia/Kolkata"
                    }
                },
                "hours": {
                    "$divide": [
                        {"$subtract": ["$punch_out", "$punch_in"]},
                        3600000
                    ]
                }
            }
        },
        {"$match": {"hours": {"$gte": 0}}},
        {
            "$group": {
                "_id": "$date",
                "total_sessions": {"$sum": 1},
                "total_working_hours": {"$sum": "$hours"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "date": "$_id",
                "total_sessions": 1,
                "total_working_hours": {
                    "$round": ["$total_working_hours", 2]
                }
            }
        },
        {"$sort": {"date": -1}}
    ]

    cursor = await db.attendance.aggregate(pipeline)
    result = await cursor.to_list(length=1)
    return result

# ---------------- DATABASE HEALTH ----------------

@app.get("/health/db")
async def database_health(request: Request):
    try:
        await request.app.state.mongo_client.admin.command("ping")
        return {"status": "connected"}
    except Exception:
        raise HTTPException(503, "MongoDB connection failed")
