import json
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
# Không cần import check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_very_secret_key_for_this_app'

# Mật khẩu được lưu dưới dạng văn bản thuần túy
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"
ATTENDANCE_FILE = 'attendance.json'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Bạn cần đăng nhập để thực hiện chấm công."
login_manager.login_message_category = "info"

class AdminUser(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == '1':
        return AdminUser(id=1)
    return None

def read_json_file(file_path):
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0: return []
    with open(file_path, 'r', encoding='utf-8') as f: return json.load(f)

def write_json_file(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4, ensure_ascii=False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('calendar'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # So sánh mật khẩu trực tiếp
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            user = AdminUser(id=1)
            login_user(user)
            return redirect(url_for('calendar'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không chính xác.')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('calendar'))

@app.route('/')
def calendar():
    return render_template('calendar.html', is_admin=current_user.is_authenticated)

@app.route('/api/attendance', methods=['GET'])
def get_attendance_data():
    attendance_data = read_json_file(ATTENDANCE_FILE)
    events = []
    for rec in attendance_data:
        events.append({
            'title': f"{rec['status']}: {rec.get('note', '')}" if rec.get('note') else rec['status'],
            'start': rec['date'],
            'backgroundColor': '#198754' if rec['status'] == 'Đi làm' else '#dc3545',
            'borderColor': '#198754' if rec['status'] == 'Đi làm' else '#dc3545',
            'extendedProps': {
                'status': rec['status'],
                'note': rec.get('note', '')
            }
        })
    return jsonify(events)

@app.route('/api/attendance', methods=['POST'])
@login_required
def set_attendance_data():
    data = request.json
    all_attendance = read_json_file(ATTENDANCE_FILE)
    record_found = False
    for rec in all_attendance:
        if rec.get('date') == data['date']:
            rec.update({'status': data['status'], 'note': data.get('note', '')})
            record_found = True
            break
    if not record_found:
        all_attendance.append({
            'date': data['date'], 'status': data['status'], 'note': data.get('note', '')
        })
    write_json_file(ATTENDANCE_FILE, all_attendance)
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)