from flask import Flask, request, render_template, jsonify
from datetime import datetime
import mysql.connector
import logging
import os

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)

# Database configuration
db_config = {
    'host': 'my-database.cdw8oggq85o3.us-east-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'Admin123',
    'database': 'ATTENDANCE'
}

def get_db_connection():
    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as err:
        logging.error(f"Database connection failed: {err}")
        return None

@app.route('/', methods=['GET', 'POST'])
def attendance():
    if request.method == 'POST':
        conn = None
        cursor = None
        try:
            logging.info("Received form data: %s", request.form)
            logging.info("Received files: %s", request.files)

            employee_name = request.form.get('name')
            employee_city = request.form.get('city')
            latitude = request.form.get('latitude')
            longitude = request.form.get('longitude')
            location_name = request.form.get('location_name')
            image = request.files.get('image')
            
            # Input validation
            if not all([employee_name, employee_city, latitude, longitude, image]):
                missing = [field for field in ['name', 'city', 'latitude', 'longitude'] 
                           if not request.form.get(field)]
                if 'image' not in request.files:
                    missing.append('image')
                return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

            image_data = image.read()
            
            now = datetime.now()
            attendance_date = now.date()
            attendance_time = now.time()
            
            conn = get_db_connection()
            if not conn:
                return jsonify({"error": "Database connection failed"}), 500

            cursor = conn.cursor()

            # Check if employee has already punched in today
            query = """SELECT ATTENDANCE_PUNCHIN FROM ATTENDANCE 
                       WHERE EMPLOYEE_NAME = %s AND ATTENDANCE_DATE = %s"""
            cursor.execute(query, (employee_name, attendance_date))
            result = cursor.fetchone()
            
            if result is None:
                # Punch In
                query = """INSERT INTO ATTENDANCE 
                           (EMPLOYEE_NAME, EMPLOYEE_CITY, EMPLOYEE_IMAGE, ATTENDANCE_DATE, 
                            ATTENDANCE_PUNCHIN, LATITUDE, LONGITUDE, LOCATION_NAME) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                cursor.execute(query, (employee_name, employee_city, image_data, attendance_date, 
                                       attendance_time, latitude, longitude, location_name))
                message = "Punched In successfully"
            else:
                # Punch Out
                query = """UPDATE ATTENDANCE SET ATTENDANCE_PUNCHOUT = %s 
                           WHERE EMPLOYEE_NAME = %s AND ATTENDANCE_DATE = %s"""
                cursor.execute(query, (attendance_time, employee_name, attendance_date))
                message = "Punched Out successfully"
            
            conn.commit()
            return jsonify({"message": message})
        
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            return jsonify({"error": f"An internal error occurred: {str(e)}"}), 500
        
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)