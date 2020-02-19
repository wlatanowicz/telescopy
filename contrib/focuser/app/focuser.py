import time

import machine
import uasyncio
# import const
from lib.uasyncio.websocket.server import WSReader, WSWriter


def log(*args, **kwargs):
    print(*args, **kwargs)


class WriterPool:
    writers = {}

    @classmethod
    def register(cls, writer):
        uid = len(cls.writers)
        cls.writers[uid] = writer
        return uid

    @classmethod
    def unregister(cls, uid):
        del cls.writers[uid]

    @classmethod
    async def write(cls, msg):
        for w in cls.writers:
            await cls.writers[w].awrite(msg)
            log("Sent message {} to {}".format(msg, w))


class DeviceHandler:
    MIN_POSITION = 0
    MAX_POSITION = 10000

    DIR_UP = 1
    DIR_DOWN = -1

    BROADCAST_INTERVAL = 100

    position = MIN_POSITION

    steps = 0
    step_dir = DIR_UP

    pins = (
        machine.Pin(13, machine.Pin.OUT),  # D7
        machine.Pin(14, machine.Pin.OUT),  # D7
        machine.Pin(15, machine.Pin.OUT),  # D7
        machine.Pin(16, machine.Pin.OUT),  # D7
    )

    PIN_MAP = (
        (0, 0, 1, 1),
        (0, 1, 1, 0),
        (1, 1, 0, 0),
        (1, 0, 0, 1),
    )

    @classmethod
    async def main(cls):

        send_in = cls.BROADCAST_INTERVAL

        while 1:
            if cls.steps > 0:

                cls.steps -= 1
                cls.position += cls.step_dir

                cls.drive_pins(cls.position)

                await uasyncio.sleep_ms(1)
            else:
                await uasyncio.sleep_ms(20)

            if send_in > 0:
                send_in -= 1
            else:
                send_in = cls.BROADCAST_INTERVAL
                await cls.send_position()

    @classmethod
    def drive_pins(cls, position):
        index = position % 4

        cls.pins[0].value(cls.PIN_MAP[index][0])
        cls.pins[1].value(cls.PIN_MAP[index][1])
        cls.pins[2].value(cls.PIN_MAP[index][2])
        cls.pins[3].value(cls.PIN_MAP[index][3])

    @classmethod
    def set_target(cls, target):
        if target > cls.MAX_POSITION or target < cls.MIN_POSITION:
            return

        position = cls.position

        dist = abs(target - position)

        if target >= position:
            cls.steps = dist
            cls.step_dir = cls.DIR_UP
        else:
            cls.steps = dist
            cls.step_dir = cls.DIR_DOWN

    @classmethod
    def park(cls):
        cls.set_target(cls.MIN_POSITION)

    @classmethod
    def reset(cls, target):
        if target > cls.MAX_POSITION or target < cls.MIN_POSITION:
            return

        cls.position = target

    @classmethod
    async def send_position(cls):
        dir = "up" if cls.step_dir == cls.DIR_UP else "down"
        if cls.steps == 0:
            status = "idle"
        else:
            status = "go"

        status = (
            "{"
            + '"position": {}, "direction": "{}", "status": "{}"\}'.format(
                cls.position, dir, status
            )
            + "}"
        )
        await WriterPool.write(status)


async def conn_handler(reader, writer):
    # Consume GET line
    await reader.readline()

    ws_reader = await WSReader(reader, writer)
    ws_writer = WSWriter(reader, writer)

    uid = WriterPool.register(ws_writer)

    while 1:
        l = await ws_reader.read(1024)

        log("Got message {}".format(l))

        if not l:
            log("Disconnecting")
            break

        if l.startswith("pos:"):
            DeviceHandler.set_target(int(l[4:]))

        elif l.startswith("home"):
            DeviceHandler.park()

        elif l.startswith("reset:"):
            DeviceHandler.reset(int(l[6:]))

    WriterPool.unregister(uid)


def start():
    machine.freq(160000000)

    loop = uasyncio.get_event_loop()
    loop.create_task(DeviceHandler.main())
    loop.create_task(uasyncio.start_server(conn_handler, "0.0.0.0", 8081))
    loop.run_forever()
    loop.close()
