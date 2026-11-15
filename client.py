import socket
import hashlib
import multiprocessing

DIGITS = 10
SERVER_HOST = "127.0.0.1"   # <-- כאן שמים את ה-IP של השרת
SERVER_PORT = 5050


def get_local_ip():
    # מחזיר את ה-IP של המחשב ברשת (ולא 127.0.0.1)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))   # לא באמת שולח כלום, רק בודק דרך איזה ממשק יוצאים
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    s.close()
    return ip


def worker(core_index, local_ip):
    client_id = local_ip + " - " + str(core_index + 1)   # לדוגמה: "192.168.4.93 - 10"

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_HOST, SERVER_PORT))

        # שולחים הודעה כלשהי כדי לקבל מהשרת את ה-MD5 שמחפשים
        sock.sendall(b"HELLO\n")
        answer = sock.recv(1024).decode().strip()
        target_md5 = answer.split()[1]   # ההודעה היא "TARGET <md5>"

        while True:
            # מבקשים נתח עבודה חדש
            sock.sendall(b"GET\n")
            data = sock.recv(1024).decode().strip()

            if data == "STOP":
                break   # מישהו אחר מצא, או שנגמרו המספרים

            # ההודעה היא "BLOCK start end"
            parts = data.split()
            start = int(parts[1])
            end = int(parts[2])
            print("[" + client_id + "] קיבלתי נתח:", start, "-", end)

            found = False
            for n in range(start, end + 1):
                candidate = str(n).zfill(DIGITS)
                if hashlib.md5(candidate.encode()).hexdigest() == target_md5:
                    sock.sendall(("FOUND " + candidate + "\n").encode())
                    sock.recv(1024)   # מחכים ל-OK מהשרת
                    print("[" + client_id + "] *** מצאתי את הפתרון:", candidate, "***")
                    found = True
                    break

            if found:
                break

        sock.close()

    except Exception as e:
        print("[" + client_id + "] שגיאה:", e)


def main():
    local_ip = get_local_ip()
    num_cores = multiprocessing.cpu_count()
    print("[CLIENT] IP מקומי:", local_ip, "| מספר ליבות:", num_cores)
    print("[CLIENT] מפעיל", num_cores, "תהליכים, מתחבר ל-" + SERVER_HOST + ":" + str(SERVER_PORT), "\n")

    processes = []
    for i in range(num_cores):
        p = multiprocessing.Process(target=worker, args=(i, local_ip))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    print("[CLIENT] (" + local_ip + ") כל התהליכים סיימו.")


if __name__ == "__main__":   # חובה בווינדוס! בלי זה כל תהליך־בן מריץ שוב את main
    main()