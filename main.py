""" TCP AND UDP BASED CLIENT-SERVER COMMUNICATION SYSTEM Author: S JANANI | Register Number: 1911260131 Run: python main.py Python 3 standard library only (Tkinter required). """
import socket
import threading
import time
import queue
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

TCP_DEFAULT = 5000
UDP_DEFAULT = 5001
BUFFER_SIZE = 4096


class Server:
    def __init__(self, log):
        self.log = log
        self.running = False
        self.tcp = None
        self.udp = None

    def start(self, tcp_port, udp_port):
        if self.running:
            return
        try:
            self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tcp.bind(("0.0.0.0", tcp_port))
            self.tcp.listen(10)
            self.tcp.settimeout(1)

            self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp.bind(("0.0.0.0", udp_port))
            self.udp.settimeout(1)
        except OSError:
            self.stop()
            raise

        self.running = True
        threading.Thread(target=self._tcp_loop, daemon=True).start()
        threading.Thread(target=self._udp_loop, daemon=True).start()
        self.log(f"Server started | TCP: {tcp_port} | UDP: {udp_port}")

    def _tcp_loop(self):
        while self.running:
            try:
                conn, addr = self.tcp.accept()
                threading.Thread(
                    target=self._handle_tcp, args=(conn, addr), daemon=True
                ).start()
            except socket.timeout:
                continue
            except OSError:
                break

    def _handle_tcp(self, conn, addr):
        self.log(f"[TCP] Connected: {addr}")
        try:
            with conn:
                conn.settimeout(10)
                while self.running:
                    data = conn.recv(BUFFER_SIZE)
                    if not data:
                        break
                    msg = data.decode("utf-8", errors="replace")
                    self.log(f"[TCP] Received: {msg}")
                    conn.sendall(f"TCP server received: {msg}".encode("utf-8"))
        except OSError as exc:
            self.log(f"[TCP] Client error: {exc}")
        self.log(f"[TCP] Disconnected: {addr}")

    def _udp_loop(self):
        while self.running:
            try:
                data, addr = self.udp.recvfrom(BUFFER_SIZE)
                msg = data.decode("utf-8", errors="replace")
                self.log(f"[UDP] Received from {addr}: {msg}")
                # This is an application-level reply, not a UDP transport ACK.
                self.udp.sendto(
                    f"UDP server received: {msg}".encode("utf-8"), addr
                )
            except socket.timeout:
                continue
            except OSError:
                break

    def stop(self):
        self.running = False
        for sock in (self.tcp, self.udp):
            if sock:
                try:
                    sock.close()
                except OSError:
                    pass
        self.tcp = self.udp = None
        self.log("Server stopped.")


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("TCP and UDP Client-Server Communication System")
        self.root.geometry("850x660")
        self.root.minsize(720, 560)
        self.events = queue.Queue()
        self.server = Server(lambda msg: self.events.put(("log", msg)))
        self._build()
        self.root.after(100, self._poll)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build(self):
        main = ttk.Frame(self.root, padding=14)
        main.pack(fill="both", expand=True)

        ttk.Label(
            main, text="TCP AND UDP CLIENT-SERVER COMMUNICATION SYSTEM",
            font=("Arial", 15, "bold"), anchor="center"
        ).pack(fill="x", pady=(0, 4))
        ttk.Label(
            main, text="Transport Layer Protocol Demonstration"
        ).pack(pady=(0, 10))

        form = ttk.LabelFrame(main, text="Client Communication", padding=10)
        form.pack(fill="x", pady=5)

        self.client_id = tk.StringVar(value="Client-1")
        self.server_ip = tk.StringVar(value="127.0.0.1")
        self.protocol = tk.StringVar(value="TCP")
        self.port = tk.StringVar(value=str(TCP_DEFAULT))
        self.message = tk.StringVar()

        fields = [
            ("Client ID:", self.client_id),
            ("Server IP Address:", self.server_ip),
            ("Protocol:", self.protocol),
            ("Port Number:", self.port),
            ("Message:", self.message),
        ]
        for i, (label, var) in enumerate(fields):
            row, col = divmod(i, 2)
            ttk.Label(form, text=label).grid(row=row, column=col*2, sticky="w", padx=5, pady=5)
            if label == "Protocol:":
                widget = ttk.Combobox(
                    form, textvariable=var, values=("TCP", "UDP"),
                    state="readonly", width=22
                )
                widget.bind("<<ComboboxSelected>>", self.protocol_changed)
            else:
                widget = ttk.Entry(form, textvariable=var, width=25)
            widget.grid(row=row, column=col*2+1, sticky="ew", padx=5, pady=5)

        for col in range(4):
            form.columnconfigure(col, weight=1)

        ttk.Button(form, text="Send Message", command=self.send).grid(
            row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=8
        )
        ttk.Button(form, text="Clear Results", command=self.clear).grid(
            row=3, column=2, columnspan=2, sticky="ew", padx=5, pady=8
        )

        controls = ttk.LabelFrame(main, text="Server Controls", padding=10)
        controls.pack(fill="x", pady=5)
        self.tcp_port = tk.StringVar(value=str(TCP_DEFAULT))
        self.udp_port = tk.StringVar(value=str(UDP_DEFAULT))
        self.server_status = tk.StringVar(value="Server Status: Stopped")

        ttk.Label(controls, text="TCP Port:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(controls, textvariable=self.tcp_port, width=12).grid(row=0, column=1, padx=5)
        ttk.Label(controls, text="UDP Port:").grid(row=0, column=2, padx=5, pady=5)
        ttk.Entry(controls, textvariable=self.udp_port, width=12).grid(row=0, column=3, padx=5)
        ttk.Button(controls, text="Start Server", command=self.start_server).grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=6
        )
        ttk.Button(controls, text="Stop Server", command=self.stop_server).grid(
            row=1, column=2, columnspan=2, sticky="ew", padx=5, pady=6
        )
        ttk.Label(controls, textvariable=self.server_status).grid(
            row=2, column=0, columnspan=4, sticky="w", padx=5, pady=4
        )

        results = ttk.LabelFrame(main, text="Communication Results", padding=10)
        results.pack(fill="x", pady=5)
        self.connection = tk.StringVar(value="Not connected")
        self.received = tk.StringVar(value="No message received")
        self.elapsed = tk.StringVar(value="Not measured")
        self.ack = tk.StringVar(value="Not available")

        for r, (label, var) in enumerate([
            ("Connection Status:", self.connection),
            ("Message Received:", self.received),
            ("Packet / Response Time:", self.elapsed),
            ("Acknowledgment Status:", self.ack),
        ]):
            ttk.Label(results, text=label, font=("Arial", 9, "bold")).grid(
                row=r, column=0, sticky="w", padx=5, pady=4
            )
            ttk.Label(results, textvariable=var, wraplength=620).grid(
                row=r, column=1, sticky="w", padx=5, pady=4
            )
        results.columnconfigure(1, weight=1)

        log_frame = ttk.LabelFrame(main, text="Server Activity Log", padding=8)
        log_frame.pack(fill="both", expand=True, pady=5)
        self.log_box = scrolledtext.ScrolledText(
            log_frame, height=8, state="disabled", wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.log_box.pack(fill="both", expand=True)

        ttk.Label(
            main, text="S JANANI | Register Number: 1911260131",
            font=("Arial", 8)
        ).pack(anchor="e", pady=(4, 0))

    def protocol_changed(self, _event=None):
        self.port.set(str(TCP_DEFAULT if self.protocol.get() == "TCP" else UDP_DEFAULT))

    def _log(self, text):
        self.log_box.configure(state="normal")
        self.log_box.insert(tk.END, f"{time.strftime('%H:%M:%S')} {text}\n")
        self.log_box.see(tk.END)
        self.log_box.configure(state="disabled")

    def _poll(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == "log":
                    self._log(data)
                elif kind == "success":
                    response, ms, ack = data
                    self.connection.set("Communication successful")
                    self.received.set(response)
                    self.elapsed.set(f"{ms:.3f} ms (send/response round trip)")
                    self.ack.set(ack)
                elif kind == "error":
                    self.connection.set("Communication failed")
                    self.ack.set("No response received")
                    messagebox.showerror("Communication Error", data)
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def start_server(self):
        try:
            tcp = int(self.tcp_port.get())
            udp = int(self.udp_port.get())
            if not (1 <= tcp <= 65535 and 1 <= udp <= 65535):
                raise ValueError("Port numbers must be from 1 to 65535.")
            if tcp == udp:
                raise ValueError("Choose different TCP and UDP port numbers.")
            self.server.start(tcp, udp)
            self.server_status.set(f"Server Status: Running (TCP {tcp}, UDP {udp})")
        except ValueError as exc:
            messagebox.showerror("Invalid Port", str(exc))
        except OSError as exc:
            messagebox.showerror("Server Error", str(exc))

    def stop_server(self):
        self.server.stop()
        self.server_status.set("Server Status: Stopped")

    def send(self):
        client_id = self.client_id.get().strip()
        host = self.server_ip.get().strip()
        msg = self.message.get().strip()
        protocol = self.protocol.get().strip().upper()

        if not client_id or not host or not msg:
            messagebox.showwarning("Missing Details", "Enter Client ID, Server IP and Message.")
            return
        try:
            port = int(self.port.get())
            if not 1 <= port <= 65535:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Port", "Enter a port from 1 to 65535.")
            return

        self.connection.set("Sending...")
        self.received.set("Waiting for response...")
        self.elapsed.set("Measuring...")
        self.ack.set("Waiting...")

        def worker():
            payload = f"{client_id}: {msg}".encode("utf-8")
            start = time.perf_counter()
            try:
                if protocol == "TCP":
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(5)
                        sock.connect((host, port))
                        sock.sendall(payload)
                        data = sock.recv(BUFFER_SIZE)
                    ack_text = "Server response received (TCP)"
                else:
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                        sock.settimeout(5)
                        sock.sendto(payload, (host, port))
                        data, remote = sock.recvfrom(BUFFER_SIZE)
                    ack_text = f"Application-level reply received from {remote[0]}"
                ms = (time.perf_counter() - start) * 1000
                self.events.put(("success", (
                    data.decode("utf-8", errors="replace"), ms, ack_text
                )))
            except (OSError, socket.timeout) as exc:
                self.events.put(("error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def clear(self):
        self.connection.set("Not connected")
        self.received.set("No message received")
        self.elapsed.set("Not measured")
        self.ack.set("Not available")
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", tk.END)
        self.log_box.configure(state="disabled")

    def close(self):
        self.server.stop()
        self.root.destroy()


if __name__ == "__main__":
    window = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass
    App(window)
    window.mainloop()
