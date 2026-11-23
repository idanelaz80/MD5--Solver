import socket
import threading
import time

HOST = "0.0.0.0"
PORT = 5050
BLOCK_SIZE = 100000       # כמה מספרים כל ליבה מקבלת בכל פעם
TARGET_MD5 = "ec9c0f7edcc18a98b1f31853b1813301"

SPACE_MIN = 1000000000    # המספר הקטן ביותר בן 10 ספרות
SPACE_MAX = 9999999999    # המספר הגדול ביותר בן 10 ספרות

# משתנים משותפים לכל התהליכים
lock = threading.Lock()
next_start = SPACE_MIN
found = False
found_number = None
machines = set()          # כתובות IP של מחשבים שהצטרפו
requeued = []             # נתחים של ליבות שנפלו - צריך לחלק אותם מחדש
start_time = None


def get_block():
    """
    מחזירה את נתח העבודה הבא לחלוקה - קודם נתחים שחזרו לתור, ואז נתח חדש. אין פרמטרים.
    :return: tuple של (start, end), או None אם נמצא פתרון או שנגמרו המספרים
    """
    global next_start
    result = None
    with lock:
        if not found:
            if requeued:
                result = requeued.pop(0)
            elif next_start <= SPACE_MAX:
                start = next_start
                end = min(start + BLOCK_SIZE - 1, SPACE_MAX)
                next_start = end + 1
                result = (start, end)
    return result


def handle_client(conn, addr):
    """
    מטפלת בלקוח אחד (thread נפרד): מקבלת בקשות GET/FOUND ומחלקת נתחים עד שהחיבור נסגר.
    :param conn: אובייקט ה-socket של החיבור ללקוח
    :param addr: tuple של (ip, port) של הלקוח
    :return: אין (None)
    """
    global found, found_number, start_time
    ip = addr[0]
    current_block = None      # הנתח שהליבה הזאת עובדת עליו כרגע

    with lock:
        if start_time is None:
            start_time = time.time()
        if ip not in machines:
            machines.add(ip)
            print("[SERVER] מחשב חדש הצטרף:", ip)

    try:
        while True:
            data = conn.recv(1024).decode().strip()
            if not data:
                break
            if data == "GET":
                current_block = None    # אם ביקש נתח חדש - סימן שסיים את הקודם
                block = get_block()
                if block is None:
                    conn.sendall(b"STOP\n")
                else:
                    current_block = block
                    msg = "BLOCK " + str(block[0]) + " " + str(block[1]) + "\n"
                    conn.sendall(msg.encode())
            elif data.startswith("FOUND"):
                number = data.split()[1]
                current_block = None
                with lock:
                    if not found:
                        found = True
                        found_number = number
                        elapsed = time.time() - start_time
                        print("\nנמצא פתרון!")
                        print("המספר שפוענח:", number)
                        print("מספר המחשבים:", len(machines))
                        print("זמן בשניות: %.2f" % elapsed)
                conn.sendall(b"OK\n")

            else:
                conn.sendall(b"TARGET " + TARGET_MD5.encode() + b"\n")
    except:
        pass
    finally:
        # אם הליבה נפלה באמצע נתח - מחזירים אותו לתור כדי שליבה אחרת תעשה אותו
        if current_block is not None and not found:
            with lock:
                requeued.append(current_block)
            print("[SERVER] הליבה", ip, "נפלה באמצע הנתח",
                  current_block[0], "-", current_block[1], "- מחזירים לתור")
        conn.close()


def main():
    """
    הפעולה הראשית של השרת: פותחת socket, מאזינה לחיבורים ופותחת thread לכל לקוח. אין פרמטרים.
    :return: אין (None)
    """
    sock = socket.socket()
    sock.bind((HOST, PORT))
    sock.listen(100)

    print("[SERVER] מאזין על פורט", PORT)
    print("[SERVER] מחפש מספר שה-MD5 שלו הוא:", TARGET_MD5)

    while True:
        conn, addr = sock.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr))
        t.start()


main()