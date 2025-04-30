import time
import threading
import pymysql
from prometheus_client import Gauge, Counter, start_http_server, generate_latest
from flask import Flask, Response

app = Flask(__name__)


MYSQL_SERVERS = [
    {"host": "sizin-mysql-sunucu-adresiniz-veya-ip-adresi", "user": "kullanıcıadınız", "password": "şifreniz", "port": 3306},

]


# 📌 **GAUGE Tipi Metrikler (Anlık Değerler)**
mysql_uptime = Gauge("mysql_uptime", "MySQL Server Uptime in Seconds", ["server"])
mysql_threads_cached = Gauge("mysql_threads_cached", "Number of Cached Threads", ["server"])
mysql_threads_connected = Gauge("mysql_threads_connected", "Current Active Connections", ["server"])
mysql_threads_running = Gauge("mysql_threads_running", "Number of currently running queries", ["server"])
mysql_innodb_buffer_pool_pages_total = Gauge("mysql_innodb_buffer_pool_pages_total", "Total InnoDB Buffer Pool Pages", ["server"])
mysql_innodb_buffer_pool_pages_data = Gauge("mysql_innodb_buffer_pool_pages_data", "Used InnoDB Buffer Pool Pages", ["server"])
mysql_innodb_buffer_pool_pages_dirty = Gauge("mysql_innodb_buffer_pool_pages_dirty", "Total Dirty Pages in Buffer Pool", ["server"])
mysql_innodb_buffer_pool_bytes_dirty = Gauge("mysql_innodb_buffer_pool_bytes_dirty", "Total Dirty Bytes in Buffer Pool", ["server"])
mysql_innodb_buffer_pool_bytes_data = Gauge("mysql_innodb_buffer_pool_bytes_data", "Total Bytes Used in InnoDB Buffer Pool", ["server"])
mysql_innodb_buffer_pool_wait_free = Gauge("mysql_innodb_buffer_pool_wait_free", "InnoDB Buffer Pool Wait Free", ["server"])
mysql_innodb_buffer_pool_size = Gauge("mysql_innodb_buffer_pool_size", "Total Allocated InnoDB Buffer Pool Size", ["server"])
mysql_innodb_buffer_pool_pages_free = Gauge("mysql_innodb_buffer_pool_pages_free", "Free Pages in InnoDB Buffer Pool", ["server"])

# 📌 **COUNTER Tipi Metrikler (Sürekli Artan Değerler)**
mysql_total_queries = Counter("mysql_total_queries_total", "Total number of queries executed", ["server"])
mysql_total_user_queries = Counter("mysql_total_user_queries_total", "Total number of user-executed queries", ["server"])
mysql_innodb_data_written = Counter("mysql_innodb_data_written", "Total bytes written to disk by InnoDB", ["server"])
mysql_innodb_data_read = Counter("mysql_innodb_data_read", "Total bytes read from disk by InnoDB", ["server"])
mysql_innodb_data_writes = Counter("mysql_innodb_data_writes", "Total number of write operations on disk", ["server"])
mysql_innodb_data_reads = Counter("mysql_innodb_data_reads", "Total number of read operations on disk", ["server"])
mysql_innodb_data_fsyncs = Counter("mysql_innodb_data_fsyncs", "Total fsync calls on disk", ["server"])
mysql_innodb_log_writes = Counter("mysql_innodb_log_writes", "Total redo log writes by InnoDB", ["server"])
mysql_innodb_buffer_pool_pages_flushed = Counter("mysql_innodb_buffer_pool_pages_flushed", "Total buffer pool pages flushed to disk", ["server"])
mysql_innodb_buffer_pool_reads = Counter("mysql_innodb_buffer_pool_reads", "Number of data read from disk that cannot be found in the Buffer Pool", ["server"])
mysql_innodb_buffer_pool_read_requests = Counter("mysql_innodb_buffer_pool_read_requests", "Total InnoDB Buffer Pool read requests", ["server"])

# 📌 **MySQL Genel ve Buffer Pool Metriklerini Çeken Fonksiyon**
def collect_mysql_metrics():
    while True:
        for server in MYSQL_SERVERS:
            try:
                conn = pymysql.connect(
                    host=server["host"],
                    user=server["user"],
                    password=server["password"],
                    port=server["port"],
                    connect_timeout=5
                )
                cursor = conn.cursor()

                # 🔹 **Uptime, Threads, Queries**
                cursor.execute("""
                    SHOW GLOBAL STATUS 
                    WHERE Variable_name IN (
                        'Uptime', 'Threads_cached', 'Threads_connected', 'Threads_running',
                        'Queries', 'Questions', 'Innodb_data_written', 'Innodb_data_read',
                        'Innodb_data_writes', 'Innodb_data_reads', 'Innodb_data_fsyncs', 'Innodb_log_writes','Innodb_buffer_pool_reads', 'Innodb_buffer_pool_read_requests'
                    );
                """)
                result = dict(cursor.fetchall())

                if "Uptime" in result:
                    mysql_uptime.labels(server=server["host"]).set(int(result["Uptime"]))

                if "Threads_cached" in result:
                    mysql_threads_cached.labels(server=server["host"]).set(int(result["Threads_cached"]))

                if "Threads_connected" in result:
                    mysql_threads_connected.labels(server=server["host"]).set(int(result["Threads_connected"]))

                if "Threads_running" in result:
                    mysql_threads_running.labels(server=server["host"]).set(int(result["Threads_running"]))

                if "Queries" in result:
                    mysql_total_queries.labels(server=server["host"]).inc(int(result["Queries"]))

                if "Questions" in result:
                    mysql_total_user_queries.labels(server=server["host"]).inc(int(result["Questions"]))

                if "Innodb_data_written" in result:
                    mysql_innodb_data_written.labels(server=server["host"]).inc(int(result["Innodb_data_written"]))

                if "Innodb_data_read" in result:
                    mysql_innodb_data_read.labels(server=server["host"]).inc(int(result["Innodb_data_read"]))

                if "Innodb_data_writes" in result:
                    mysql_innodb_data_writes.labels(server=server["host"]).inc(int(result["Innodb_data_writes"]))

                if "Innodb_data_reads" in result:
                    mysql_innodb_data_reads.labels(server=server["host"]).inc(int(result["Innodb_data_reads"]))

                if "Innodb_data_fsyncs" in result:
                    mysql_innodb_data_fsyncs.labels(server=server["host"]).inc(int(result["Innodb_data_fsyncs"]))

                if "Innodb_log_writes" in result:
                    mysql_innodb_log_writes.labels(server=server["host"]).inc(int(result["Innodb_log_writes"]))

                if "Innodb_buffer_pool_reads" in result:
                    mysql_innodb_buffer_pool_reads.labels(server=server["host"]).inc(int(result["Innodb_buffer_pool_reads"]))

                if "Innodb_buffer_pool_read_requests" in result:
                    mysql_innodb_buffer_pool_read_requests.labels(server=server["host"]).inc(int(result["Innodb_buffer_pool_read_requests"]))



                # 🔹 **Buffer Pool Metrikleri**
                cursor.execute("""
                    SHOW GLOBAL STATUS 
                    WHERE Variable_name IN (
                        'Innodb_buffer_pool_pages_total', 'Innodb_buffer_pool_pages_data',
                        'Innodb_buffer_pool_wait_free', 'Innodb_buffer_pool_bytes_data',
                        'Innodb_buffer_pool_bytes_dirty', 'Innodb_buffer_pool_pages_dirty',
                        'Innodb_buffer_pool_pages_flushed', 'Innodb_buffer_pool_pages_free'
                    );
                """)
                buffer_result = dict(cursor.fetchall())

                if "Innodb_buffer_pool_pages_total" in buffer_result:
                    mysql_innodb_buffer_pool_pages_total.labels(server=server["host"]).set(int(buffer_result["Innodb_buffer_pool_pages_total"]))

                if "Innodb_buffer_pool_wait_free" in buffer_result:
                    mysql_innodb_buffer_pool_wait_free.labels(server=server["host"]).set(int(buffer_result["Innodb_buffer_pool_wait_free"]))

                if "Innodb_buffer_pool_bytes_data" in buffer_result:
                    mysql_innodb_buffer_pool_bytes_data.labels(server=server["host"]).set(int(buffer_result["Innodb_buffer_pool_bytes_data"]))

                if "Innodb_buffer_pool_pages_data" in buffer_result:
                    mysql_innodb_buffer_pool_pages_data.labels(server=server["host"]).set(int(buffer_result["Innodb_buffer_pool_pages_data"]))

                if "Innodb_buffer_pool_bytes_dirty" in buffer_result:
                    mysql_innodb_buffer_pool_bytes_dirty.labels(server=server["host"]).set(int(buffer_result["Innodb_buffer_pool_bytes_dirty"]))

                if "Innodb_buffer_pool_pages_dirty" in buffer_result:
                    mysql_innodb_buffer_pool_pages_dirty.labels(server=server["host"]).set(int(buffer_result["Innodb_buffer_pool_pages_dirty"]))

                if "Innodb_buffer_pool_pages_flushed" in buffer_result:
                    mysql_innodb_buffer_pool_pages_flushed.labels(server=server["host"]).inc(int(buffer_result["Innodb_buffer_pool_pages_flushed"]))

                if "Innodb_buffer_pool_pages_free" in buffer_result:
                    mysql_innodb_buffer_pool_pages_free.labels(server=server["host"]).set(int(buffer_result["Innodb_buffer_pool_pages_free"]))

                cursor.execute("SELECT @@innodb_buffer_pool_size;")
                pool_size = cursor.fetchone()[0]
                mysql_innodb_buffer_pool_size.labels(server=server["host"]).set(int(pool_size))

                conn.close()
            except Exception as e:
                print(f"❌ Bağlantı hatası (MySQL Metrics): {server['host']} - {e}")

        time.sleep(10)  # 🔹 **Her 10 saniyede bir güncelle**

# 📌 **Flask Uygulaması (Prometheus için /metrics Endpoint)**
@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype="text/plain")

# 📌 **Arka Planda Çalışan Thread'leri Başlat**
threading.Thread(target=collect_mysql_metrics, daemon=True).start()

# 📌 **Flask Web Sunucusunu Başlat**
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9106)
