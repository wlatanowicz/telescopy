import uasyncio
import machine
import time
#import const
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
    MAX_POSITION = 1334930
    TRIGGER_PADDING = 25
    HOME_POSITION = 0
    BATCH_SIZE = 100

    position = 0

    steps = 0
    step_dir = 1
    go_home = False

    pin_dir = machine.Pin(13, machine.Pin.OUT)  # D7
    pin_step = machine.Pin(15, machine.Pin.OUT)  # D8

    sensor_triggered = False
    trigger_position = (MAX_POSITION - TRIGGER_PADDING, HOME_POSITION + TRIGGER_PADDING)

    @classmethod
    def setup_irq(cls):
        pin_sensor = machine.Pin(6, machine.Pin.IN)  # GPIO 12 / D6

        # pin_sensor.irq(trigger=machine.Pin.IRQ_RISING, handler=cls.sensor_trigger_enter_handler)

    @classmethod
    async def main(cls):

        send_interval = 100
        send_in = send_interval

        while 1:
            if cls.sensor_triggered:
                cls.position_cal()

            if cls.go_home and cls.position == cls.HOME_POSITION:
                cls.steps = 0
                cls.go_home = False

            if cls.steps > 0:

                if cls.steps > 2 * cls.BATCH_SIZE:
                    steps = cls.BATCH_SIZE
                else:
                    steps = cls.steps

                cls.steps -= steps
                cls.position += cls.step_dir * steps

                cls.position = cls.normalize(cls.position)
                if cls.position < 0:
                    cls.position += cls.MAX_POSITION
                if cls.position > cls.MAX_POSITION:
                    cls.position -= cls.MAX_POSITION

                cls.batch_step(steps)

                await uasyncio.sleep_ms(1)
            else:
                await uasyncio.sleep_ms(20)

            if send_in > 0:
                send_in -= 1
            else:
                send_in = send_interval
                await cls.send_position()

    @classmethod
    def batch_step(cls, batch_size):
        for i in range(0, batch_size):
            time.sleep_us(50)
            cls.pin_step.value(0)
            time.sleep_us(50)
            cls.pin_step.value(1)

    @classmethod
    def set_target(cls, target):
        if target > cls.MAX_POSITION or target < 0:
            return

        position = cls.position

        cw_dist, ccw_dist = cls.dist(position, target)

        if cw_dist <= ccw_dist:
            cls.steps = cw_dist
            cls.step_dir = 1
        else:
            cls.steps = ccw_dist
            cls.step_dir = -1

        cls.pin_dir.value(1 if cls.step_dir > 0 else 0)

    @classmethod
    def park(cls):
        cls.step_dir = 1
        cls.steps = cls.MAX_POSITION
        cls.go_home = True

    @classmethod
    async def send_position(cls):
        await WriterPool.write("pos:{}".format(cls.position))

    @classmethod
    def sensor_trigger_enter_handler(cls):
        cls.sensor_triggered = True

    @classmethod
    def position_cal(cls):
        dir_index = 1 if cls.step_dir == 1 else 0
        target = cls.normalize(cls.position + (cls.step_dir * cls.steps))

        cal_position = cls.trigger_position[dir_index]

        cls.position = cal_position
        cls.set_target(target)

        cls.sensor_triggered = False

    @classmethod
    def dist(cls, position, target):
        cw_dist = target - position
        if cw_dist < cls.HOME_POSITION:
            cw_dist += cls.MAX_POSITION

        ccw_dist = cls.MAX_POSITION - cw_dist

        return cw_dist, ccw_dist

    @classmethod
    def normalize(cls, position):
        if position < 0:
            return position + cls.MAX_POSITION
        if position > cls.MAX_POSITION:
            return position - cls.MAX_POSITION
        return position


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

        if l.startswith('home'):
            DeviceHandler.park()

    WriterPool.unregister(uid)


def start_dome():
    machine.freq(160000000)

    loop = uasyncio.get_event_loop()
    loop.create_task(DeviceHandler.main())
    loop.create_task(uasyncio.start_server(conn_handler, "0.0.0.0", 8081))
    loop.run_forever()
    loop.close()
