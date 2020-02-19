import json
import logging
import queue
import socket
import threading
import time

from indi.device import Driver, properties
from indi.device.pool import DevicePool
from indi.message import const
from telescopy import settings


@DevicePool.register
class PHD2(Driver):
    name = "PHD2"

    general = properties.Group(
        "GENERAL",
        vectors=dict(
            connection=properties.Standard("CONNECTION", onchange="connect"),
            connection_settings=properties.TextVector(
                "CONNECTION_SETTINGS",
                perm=const.Permissions.READ_ONLY,
                elements=dict(
                    ip=properties.Text("IP_ADDRESS", default=settings.PHD2_IP),
                    port=properties.Text("PORT", default=settings.PHD2_PORT),
                ),
            ),
            info=properties.TextVector(
                "INFO",
                enabled=False,
                perm=const.Permissions.READ_ONLY,
                elements=dict(
                    phdversion=properties.Text("PHD_VERSION"),
                    state=properties.Text("APP_STATE"),
                ),
            ),
        ),
    )

    dithering = properties.Group(
        "DITHERING",
        enabled=False,
        vectors=dict(
            dither=properties.NumberVector(
                "DITHER",
                elements=dict(
                    dither=properties.Number(
                        "DITHER_BY_PIXELS", default=5, onwrite="dither"
                    ),
                ),
            ),
            dither_settle_settings=properties.NumberVector(
                "DITHER_SETTLE_SETTINGS",
                elements=dict(
                    pixels=properties.Number("PIXELS", default=1.5),
                    time=properties.Number("TIME", default=10),
                    timeout=properties.Number("TIMEOUT", default=30),
                ),
            ),
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection = self.Connection(self)

    def connect(self, sender, **kwargs):
        if self.general.connection.connect.bool_value:
            self.connection.connect()
            self.general.info.enabled = True
            self.dithering.enabled = True
        else:
            self.general.info.enabled = False
            self.dithering.enabled = False

    def dither(self, sender, value, **kwargs):
        self.dithering.dither.dither.value = value
        amount = float(self.dithering.dither.dither.value)
        ra_only = False
        settle = {
            "pixels": self.dithering.dither_settle_settings.pixels.value,
            "time": self.dithering.dither_settle_settings.time.value,
            "timeout": self.dithering.dither_settle_settings.timeout.value,
        }
        self.connection.rpc("dither", [amount, ra_only, settle])

    def event_settlebegin(self, **kwargs):
        self.dithering.dither.state_ = const.State.BUSY

    event_settling = event_settlebegin

    def event_settledone(self, **kwargs):
        self.dithering.dither.state_ = const.State.OK

    def event_version(self, phdversion, **kwargs):
        self.general.info.phdversion.value = phdversion

    def event_appstate(self, state, **kwargs):
        self.general.info.state.value = state

    def event_noop(self, **kwargs):
        pass

    event_loopingexposures = event_noop
    event_guidestep = event_noop

    class Connection:
        class Buffer:
            def __init__(self, connection, device):
                self._buffer = ""
                self.connection = connection
                self.device = device

            def append(self, msg):
                self._buffer += msg

            def process(self):
                messages = self._buffer.split("\r\n")
                if messages[-1]:
                    self._buffer = messages[-1]
                    messages = messages[0:-1]
                else:
                    self._buffer = ""

                for msg in messages:
                    self.process_message(msg)

            def process_message(self, raw_msg):
                if not raw_msg:
                    return

                msg = json.loads(raw_msg)
                if "Event" in msg:
                    msg = {k.lower(): v for k, v in msg.items()}
                    event_name = msg["event"].lower()
                    method = f"event_{event_name}"
                    if hasattr(self.device, method):
                        getattr(self.device, method)(**msg)
                    else:
                        print(msg)
                if "jsonrpc" in msg:
                    print(msg)
                    if msg["id"] in self.connection.rpc_responses:
                        self.connection.rpc_responses[msg["id"]].put(msg)

        def __init__(self, device):
            self.buffer = self.Buffer(self, device)
            self.sock = None
            self.device = device
            self.rpc_serial = 0
            self.rpc_responses = {}

        def handle_incoming_messages(self):
            while True:
                logging.debug(f"PHD2: waiting for data")
                message = self.sock.recv(1024)
                if not message:
                    logging.debug(f"PHD2: no data, breaking")
                    break
                logging.debug(f"PHD2: got data: {message}")
                self.buffer.append(message.decode("latin1"))
                self.buffer.process()

        def rpc(self, method, params, response_timeout=30):
            self.rpc_serial += 1
            id = self.rpc_serial
            payload = {
                "method": method,
                "params": params,
                "id": id,
            }
            q = queue.Queue()
            self.rpc_responses[id] = q
            payload_raw = json.dumps(payload) + "\r\n"
            print(payload_raw)
            self.sock.sendall(payload_raw.encode("latin1"))
            try:
                response = q.get(timeout=response_timeout)
            except:
                raise Exception(
                    f"Timeout waiting for JSONRPC response for request id={id}"
                )

            del self.rpc_responses[id]

            if "result" in response:
                return response["result"]

            if "error" in response:
                raise Exception(response["error"])

            raise Exception(f"Invalid JSONRPC response for request id={id}")

        def connect(self):
            ip = self.device.general.connection_settings.ip.value
            port = int(self.device.general.connection_settings.port.value)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ip, port))

            handler_thread = threading.Thread(
                target=self.handle_incoming_messages, daemon=True,
            )
            handler_thread.start()
