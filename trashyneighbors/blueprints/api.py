from flask import Blueprint, jsonify

from ..extensions import db
from ..models import ZipCodeLocation

bp = Blueprint("api", __name__)


@bp.get("/api/zip/<zip_code>")
def zip_lookup(zip_code):
    zip_code = (zip_code or "").strip().zfill(5)[:5]

    rows = (
        db.session.query(ZipCodeLocation)
        .filter(ZipCodeLocation.zip_code == zip_code)
        .order_by(ZipCodeLocation.state.asc(), ZipCodeLocation.city.asc())
        .all()
    )

    return jsonify(
        {
            "zip_code": zip_code,
            "results": [
                {
                    "city": r.city,
                    "state": r.state,
                    "county": r.county,
                    "latitude": (
                        float(r.latitude) if r.latitude is not None else None
                    ),
                    "longitude": (
                        float(r.longitude) if r.longitude is not None else None
                    ),
                }
                for r in rows
            ],
        }
    )
