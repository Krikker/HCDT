from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from app.config import APP_DESCRIPTION, APP_TITLE, STATIC_DIR
from app.models import ToolSelectionRequest
from app.services.twin_service import TwinService


app = FastAPI(title=APP_TITLE, description=APP_DESCRIPTION, version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

service = TwinService()


@app.get("/")
def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/operators")
def operators():
    return service.list_operators()


@app.get("/api/stations")
def stations():
    return service.list_stations()


@app.get("/api/evaluate/{operator_id}/{station_id}")
def evaluate(operator_id: str, station_id: str):
    return service.evaluate(operator_id, station_id)


@app.post("/api/session/{operator_id}/{station_id}/tool")
def choose_tool(operator_id: str, station_id: str, payload: ToolSelectionRequest):
    return service.set_selected_tool(operator_id, station_id, payload.tool_name)


@app.post("/api/session/{operator_id}/{station_id}/complete")
def complete_step(operator_id: str, station_id: str):
    return service.complete_current_step(operator_id, station_id)


@app.post("/api/session/{operator_id}/{station_id}/incident/{incident_code}")
def register_incident(operator_id: str, station_id: str, incident_code: str):
    return service.register_incident(operator_id, station_id, incident_code)


@app.post("/api/session/{operator_id}/{station_id}/close-shift")
def close_shift(operator_id: str, station_id: str):
    return service.close_shift(operator_id, station_id)


@app.get("/api/session/{operator_id}/{station_id}/report.csv")
def download_shift_csv(operator_id: str, station_id: str):
    csv_content = service.build_shift_report_csv(operator_id, station_id)
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="shift_report_{operator_id}_{station_id}.csv"'
        },
    )
