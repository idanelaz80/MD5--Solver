import socket
import hashlib
import multiprocessing

DIGITS = 10
SERVER_HOST = "127.0.0.1"   #ip שרת
SERVER_PORT = 5050


def get_local_ip():
    """
    מוצאת את כתובת ה-IP של המחשב ברשת. אין פרמטרים.
    :return: מחרוזת עם כתובת ה-IP (ואם נכשל - "127.0.0.1")
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    s.close()
    return ip


def worker(core_index, local_ip):
    """
    תהליך של ליבה אחת: מבקש נתחים מהשרת ובודק MD5 עד שנמצא הפתרון או שנגמרה העבודה.
    :param core_index: מספר הליבה (0,1,2...) - משמש רק לזיהוי בהדפסות
    :param local_ip: כתובת ה-IP של המחשב - משמשת רק לזיהוי בהדפסות
    :return: אין (None) - הפונקציה רק מדפיסה ומתקשרת עם השרת
    """
    client_id = local_ip + " - " + str(core_index + 1)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_HOST, SERVER_PORT))

        # שולחים הודעה כלשהי כדי לקבל מהשרת את ה-MD5 שמחפשים
        sock.sendall(b"HELLO\n")
        answer = sock.recv(1024).decode().strip()
        target_md5 = answer.split()[1]

        while True:
            sock.sendall(b"GET\n")
            data = sock.recv(1024).decode().strip()
            if data == "STOP":
                break

            parts = data.split()
            start = int(parts[1])
            end = int(parts[2])
            print("[" + client_id + "] קיבלתי נתח:", start, "-", end)

            found = False
            for n in range(start, end + 1):
                candidate = str(n).zfill(DIGITS)
                if hashlib.md5(candidate.encode()).hexdigest() == target_md5:
                    sock.sendall(("FOUND " + candidate + "\n").encode())
                    sock.recv(1024)
                    print("[" + client_id + "] *** מצאתי את הפתרון:", candidate, "***")
                    found = True
                    break
            if found:
                break
        sock.close()

    except Exception as e:
        print("[" + client_id + "] שגיאה:", e)


if __name__ == "__main__":
    local_ip = get_local_ip()
    num_cores = multiprocessing.cpu_count()
    processes = []
    for i in range(num_cores):
        p = multiprocessing.Process(target=worker, args=(i, local_ip))   # <-- מעבירים גם local_ip
        p.start()
        processes.append(p)
    for p in processes:
        p.join()
