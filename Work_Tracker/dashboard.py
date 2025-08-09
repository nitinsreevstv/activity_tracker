import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from activity_tracker import get_mysql_connection, write_logfile

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
socketio = SocketIO(app, async_mode='eventlet')

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/daily_summary")
def daily_summary():
    conn = get_mysql_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT day, first_login, last_logout, total_active_seconds FROM daily_summary ORDER BY day DESC LIMIT 30")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

@app.route("/api/app_usage")
def app_usage():
    conn = get_mysql_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT 
            DATE(event_time) AS day,
            app_name, 
            COUNT(*) * 5 AS duration_seconds
        FROM app_usage
        WHERE event_time >= CURDATE() - INTERVAL 30 DAY
        GROUP BY day, app_name
        ORDER BY day DESC, duration_seconds DESC
    """)
    data = cur.fetchall()
    total_duration = sum(row['duration_seconds'] for row in data) or 1
    for row in data:
        row['percentage'] = round(row['duration_seconds'] / total_duration * 100, 2)
    cur.close()
    conn.close()
    return jsonify(data)

@app.route('/api/activity_events')
def activity_events():
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT event_time, event_type, details
        FROM activity_log
        WHERE event_type IN ('LOCKED', 'UNLOCKED', 'SUSPEND', 'SHUTDOWN', 'BOOT/RESUME')
        ORDER BY event_time DESC
        LIMIT 50
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)

background_task_started = False

def background_updates():
    while True:
        try:
            conn = get_mysql_connection()
            if conn:
                cur = conn.cursor(dictionary=True)
                cur.execute("SELECT day, first_login, last_logout, total_active_seconds FROM daily_summary ORDER BY day DESC LIMIT 30")
                daily_data = cur.fetchall()

                cur.execute("""
                    SELECT app_name, SUM(duration_seconds) AS duration_seconds
                    FROM app_usage
                    WHERE DATE(event_time) = CURDATE()
                    GROUP BY app_name
                    ORDER BY duration_seconds DESC
                    LIMIT 10
                """)
                app_data = cur.fetchall()

                cur.execute("""
                    SELECT event_time, event_type, details
                    FROM activity_log
                    WHERE event_type IN ('LOCKED', 'UNLOCKED', 'SUSPEND', 'SHUTDOWN', 'BOOT/RESUME')
                    ORDER BY event_time DESC
                    LIMIT 50
                """)
                activity_events = cur.fetchall()

                cur.close()
                conn.close()

                socketio.emit('daily_summary_update', daily_data)
                socketio.emit('app_usage_update', app_data)
                socketio.emit('activity_events_update', activity_events)

        except Exception as e:
            write_logfile(f"Error emitting real-time updates: {e}")

        socketio.sleep(15)

@socketio.on('connect')
def on_connect():
    global background_task_started
    if not background_task_started:
        socketio.start_background_task(background_updates)
        background_task_started = True

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
