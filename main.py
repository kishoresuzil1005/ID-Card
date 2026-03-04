import requests
import os
import shutil
import uuid
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from generator import generate_id_card

app = FastAPI()

APP_URL = "https://your-app-name.onrender.com/health"
def keep_alive():
    try:
        requests.get(APP_URL, timeout=10)
        print("Self ping successful")
    except Exception as e:
        print("Ping failed:", e)

scheduler = BackgroundScheduler()
scheduler.add_job(keep_alive, "interval", minutes=10)
scheuler.start()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
GEN_DIR = os.path.join(BASE_DIR, "generated")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(GEN_DIR, exist_ok=True)
@app.get("/")
def home():
    return FileResponse(os.path.join(BASE_DIR, "ui.html"))
@app.get("/health")
def health():
    return {"status": "running"}

# -----------------------------
# GENERATE ID
# -----------------------------
@app.post("/generate-id/")
async def generate_id(
    name: str = Form(None),
    emp_id: str = Form(None),
    designation: str = Form(None),
    phone: str = Form(None),
    address: str = Form(None),
    dob: str = Form(None),
    blood: str = Form(None),
    emergency_contact: str = Form(None),
    photo: UploadFile = File(None)
):

    # -----------------------------
    # VALIDATION
    # -----------------------------
    required_fields = {
        "Name": name,
        "Employee ID": emp_id,
        "Designation": designation,
        "Phone Number": phone,
        "Address": address,
        "Date of Birth": dob,
        "Blood Group": blood,
        "Emergency Contact": emergency_contact
    }

    missing_fields = [key for key, value in required_fields.items() if not value or value.strip() == ""]

    if missing_fields:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Please enter all the required details before generating the ID card.",
                "missing_fields": missing_fields
            }
        )

    if photo is None or photo.filename == "":
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Please upload a photo to generate the ID card."
            }
        )

    photo_path = None

    # -----------------------------
    # SAVE PHOTO
    # -----------------------------
    unique_photo_name = str(uuid.uuid4()) + "_" + photo.filename
    photo_path = os.path.join(UPLOAD_DIR, unique_photo_name)

    with open(photo_path, "wb") as buffer:
        shutil.copyfileobj(photo.file, buffer)

    # -----------------------------
    # GENERATE UNIQUE FILE
    # -----------------------------
    file_id = str(uuid.uuid4())
    output_file = os.path.join(GEN_DIR, f"{file_id}.pdf")

    try:

        generate_id_card(
            name=name,
            emp_id=emp_id,
            designation=designation,
            phone=phone,
            address=address,
            dob=dob,
            blood=blood,
            emergency_contact=emergency_contact,
            photo_path=photo_path,
            output_path=output_file
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Something went wrong while generating the ID card. Please try again.",
                "error": str(e)
            }
        )

    finally:
        if photo_path and os.path.exists(photo_path):
            os.remove(photo_path)

    return {
        "success": True,
        "message": "ID card generated successfully.",
        "file_id": file_id
    }


# -----------------------------
# PREVIEW PDF
# -----------------------------
@app.get(
    "/preview/{file_id}",
    response_class=FileResponse,
    responses={200: {"content": {"application/pdf": {}}}}
)
def preview_file(file_id: str):

    file_path = os.path.join(GEN_DIR, f"{file_id}.pdf")

    if not os.path.exists(file_path):
        return JSONResponse(
            status_code=404,
            content={"message": "Sorry, the requested ID card was not found."}
        )

    return FileResponse(
        file_path,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline"}
    )


# -----------------------------
# DOWNLOAD PDF
# -----------------------------
@app.get(
    "/download/{file_id}",
    response_class=FileResponse,
    responses={200: {"content": {"application/pdf": {}}}}
)
def download_file(file_id: str):

    file_path = os.path.join(GEN_DIR, f"{file_id}.pdf")

    if not os.path.exists(file_path):
        return JSONResponse(
            status_code=404,
            content={"message": "Sorry, the requested file could not be found."}
        )

    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename="id_card.pdf"
    )
