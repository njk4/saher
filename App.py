from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import cv2
import easyocr
import numpy as np
from PIL import Image
import io
import re
import os
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# ============================================================
# قاعدة البيانات المؤقتة (استبدلها لاحقاً بـ PostgreSQL)
# ============================================================
STOLEN_CARS = {
    "أ ب ج 1234": {
        "report_date": "2025-01-10",
        "region": "الرياض",
        "case_number": "BLG-2025-00123",
        "car_model": "تويوتا كامري",
        "color": "أبيض"
    },
    "د هـ و 5678": {
        "report_date": "2025-01-15",
        "region": "جدة",
        "case_number": "BLG-2025-00456",
        "car_model": "هوندا أكورد",
        "color": "رمادي"
    },
    "ز ح ط 9999": {
        "report_date": "2025-02-01",
        "region": "الدمام",
        "case_number": "BLG-2025-00789",
        "car_model": "نيسان باترول",
        "color": "أسود"
    },
    # أضف أرقام لوحات حقيقية هنا
}

# ============================================================
# تهيئة نموذج قراءة اللوحات
# ============================================================
print("⏳ جاري تحميل نموذج EasyOCR...")
reader = easyocr.Reader(['ar', 'en'], gpu=False)
print("✅ تم تحميل النموذج")


def clean_plate(text):
    """تنظيف نص اللوحة من الأحرف الزائدة"""
    text = text.strip().upper()
    text = re.sub(r'\s+', ' ', text)
    return text


def read_plate_from_image(image_bytes):
    """استخراج رقم اللوحة من الصورة"""
    img_array = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    if img is None:
        return None, "تعذّر قراءة الصورة"

    # تحسين الصورة لقراءة أفضل
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    results = reader.readtext(gray)

    if not results:
        # جرب الصورة الأصلية كاملة
        results = reader.readtext(img)

    # رتّب النتائج حسب الدقة
    results_sorted = sorted(results, key=lambda x: x[2], reverse=True)

    plates = []
    for (_, text, confidence) in results_sorted:
        if confidence > 0.3 and len(text.strip()) >= 3:
            plates.append({
                "text": clean_plate(text),
                "confidence": round(confidence * 100, 1)
            })

    return plates, None


def check_database(plate_text):
    """مطابقة اللوحة مع قاعدة البيانات"""
    # بحث مباشر
    if plate_text in STOLEN_CARS:
        return True, STOLEN_CARS[plate_text]

    # بحث مرن (بدون مسافات)
    plate_clean = plate_text.replace(" ", "")
    for key, val in STOLEN_CARS.items():
        if key.replace(" ", "") == plate_clean:
            return True, val

    return False, None


# ============================================================
# Routes
# ============================================================

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')


@app.route('/api/check', methods=['POST'])
def check_vehicle():
    """
    API الرئيسي: يستقبل صورة أو رقم لوحة ويرجع النتيجة
    """
    plate_number = request.form.get('plate_number', '').strip()
    image_file = request.files.get('image')

    extracted_plates = []
    error = None

    # ---- معالجة الصورة إن وُجدت ----
    if image_file:
        image_bytes = image_file.read()
        extracted_plates, error = read_plate_from_image(image_bytes)

        if error:
            return jsonify({"success": False, "error": error}), 400

    # ---- تجميع اللوحات للفحص ----
    plates_to_check = []

    if plate_number:
        plates_to_check.append(plate_number)

    if extracted_plates:
        plates_to_check.extend([p["text"] for p in extracted_plates])

    if not plates_to_check:
        return jsonify({
            "success": False,
            "error": "الرجاء إدخال رقم اللوحة أو رفع صورة"
        }), 400

    # ---- مطابقة قاعدة البيانات ----
    results = []
    any_stolen = False

    for plate in plates_to_check:
        is_stolen, data = check_database(plate)
        if is_stolen:
            any_stolen = True

        result = {
            "plate": plate,
            "is_stolen": is_stolen,
            "check_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        if is_stolen and data:
            result["details"] = data

        results.append(result)

    return jsonify({
        "success": True,
        "any_stolen": any_stolen,
        "results": results,
        "extracted_plates": extracted_plates,
        "checked_at": datetime.now().isoformat()
    })


@app.route('/api/add_stolen', methods=['POST'])
def add_stolen():
    """إضافة سيارة مسروقة لقاعدة البيانات (للاختبار)"""
    data = request.get_json()
    plate = data.get('plate', '').strip()
    info = data.get('info', {})

    if not plate:
        return jsonify({"success": False, "error": "رقم اللوحة مطلوب"}), 400

    STOLEN_CARS[plate] = {
        "report_date": datetime.now().strftime("%Y-%m-%d"),
        "region": info.get("region", "غير محدد"),
        "case_number": f"BLG-{datetime.now().year}-{len(STOLEN_CARS)+1:05d}",
        "car_model": info.get("car_model", "غير محدد"),
        "color": info.get("color", "غير محدد")
    }

    return jsonify({"success": True, "message": f"تمت إضافة اللوحة {plate}"})


@app.route('/api/stats', methods=['GET'])
def stats():
    return jsonify({
        "total_stolen": len(STOLEN_CARS),
        "plates": list(STOLEN_CARS.keys())
    })


if __name__ == '__main__':
    print("\n🚀 تشغيل نظام ساهر للمركبات المسروقة")
    print("📍 افتح المتصفح على: http://localhost:5000\n")
    app.run(debug=True, port=5000)