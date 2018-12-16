import uasyncio
import machine
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
    MAX_POSITION = 4000

    position = 0

    steps = 0
    step_dir = 1

    pin_dir = machine.Pin(10, machine.Pin.OUT)
    pin_step = machine.Pin(12, machine.Pin.OUT)

    sensor1_triggered = False
    sensor2_triggered = False

    @classmethod
    def setup_irq(cls):
        pin_sensor1 = machine.Pin(4, machine.Pin.IN)
        pin_sensor2 = machine.Pin(5, machine.Pin.IN)

        pin_sensor1.irq(trigger=machine.Pin.IRQ_FALLING, handler=cls.sensor1_trigger_handler)
        pin_sensor2.irq(trigger=machine.Pin.IRQ_RISING, handler=cls.sensor2_trigger_handler)

    @classmethod
    async def main(cls):

        while 1:
            if cls.steps > 0:
                cls.steps -= 1
                cls.position += cls.step_dir

                if cls.position < 0:
                    cls.position += cls.MAX_POSITION
                if cls.position > cls.MAX_POSITION:
                    cls.position -= cls.MAX_POSITION

                cls.pin_step.value(0)
                await uasyncio.sleep_ms(10)
                cls.pin_step.value(1)
                await uasyncio.sleep_ms(10)
            else:
                await uasyncio.sleep_ms(20)

            await cls.send_position()

    @classmethod
    def set_target(cls, target):
        if target > cls.MAX_POSITION or target < 0:
            return

        position = cls.position

        cw_dist = target - position
        if cw_dist < 0:
            cw_dist += cls.MAX_POSITION

        ccw_dist = cls.MAX_POSITION - cw_dist

        if cw_dist <= ccw_dist:
            cls.steps = cw_dist
            cls.step_dir = 1
        else:
            cls.steps = ccw_dist
            cls.step_dir = -1

        cls.pin_dir.value(1 if cls.step_dir > 0 else 0)

    @classmethod
    async def send_position(cls):
        await WriterPool.write("pos:{}".format(cls.position))

    @classmethod
    def sensor1_trigger_handler(cls):
        cls.sensor1_triggered = True

    @classmethod
    def sensor2_trigger_handler(cls):
        cls.sensor2_triggered = True


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

        if l.startswith('pos:'):
            DeviceHandler.set_target(int(l[4:]))

    WriterPool.unregister(uid)


machine.freq(160000000)

loop = uasyncio.get_event_loop()
loop.create_task(DeviceHandler.main())
loop.create_task(uasyncio.start_server(conn_handler, "0.0.0.0", 8081))
loop.run_forever()
loop.close()
