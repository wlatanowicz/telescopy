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

    DIR_CW = 1
    DIR_CCW = -1

    BROADCAST_INTERVAL = 100

    position = HOME_POSITION

    steps = 0
    step_dir = DIR_CW

    pin_dir = machine.Pin(13, machine.Pin.OUT)  # D7
    pin_step = machine.Pin(15, machine.Pin.OUT)  # D8

    sensor_triggered = False
    trigger_position = (MAX_POSITION - TRIGGER_PADDING, HOME_POSITION + TRIGGER_PADDING)

    OP_IDLE = 0
    OP_GO = 1
    OP_ROT = 2
    OP_RESET = 3
    OP_RESET_STAGE_2 = 4

    operation = OP_IDLE

    @classmethod
    def setup_irq(cls):
        pin_sensor = machine.Pin(6, machine.Pin.IN)  # GPIO 12 / D6

        # pin_sensor.irq(trigger=machine.Pin.IRQ_RISING, handler=cls.sensor_trigger_enter_handler)

    @classmethod
    async def main(cls):

        send_in = cls.BROADCAST_INTERVAL

        while 1:
            if cls.sensor_triggered:
                cls.position_cal()

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
            elif cls.operation == cls.OP_RESET:
                cls.reset(cls.OP_RESET_STAGE_2)
            else:
                cls.operation = cls.OP_IDLE
                await uasyncio.sleep_ms(20)

            if send_in > 0:
                send_in -= 1
            else:
                send_in = cls.BROADCAST_INTERVAL
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
        if target > cls.MAX_POSITION or target < cls.HOME_POSITION:
            return

        position = cls.position
        cls.operation = cls.OP_GO

        cw_dist, ccw_dist = cls.dist(position, target)

        if cw_dist <= ccw_dist:
            cls.steps = cw_dist
            cls.step_dir = cls.DIR_CW
        else:
            cls.steps = ccw_dist
            cls.step_dir = cls.DIR_CCW

        cls.pin_dir.value(1 if cls.step_dir == cls.DIR_CW else 0)

    @classmethod
    def park(cls):
        cls.set_target(cls.HOME_POSITION)

    @classmethod
    def full_rotate(cls, dir=DIR_CW):
        cls.step_dir = dir
        cls.steps = cls.MAX_POSITION - cls.HOME_POSITION
        cls.operation = cls.OP_ROT

    @classmethod
    def reset(cls, stage=OP_RESET):
        if stage == cls.OP_RESET:
            cls.step_dir = cls.DIR_CCW
            cls.steps = cls.TRIGGER_PADDING * 1
            cls.operation = cls.OP_RESET

        if stage == cls.OP_RESET_STAGE_2:
            cls.step_dir = cls.DIR_CW
            cls.steps = cls.MAX_POSITION - cls.HOME_POSITION
            cls.operation = cls.OP_RESET_STAGE_2

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

        if cls.operation == cls.OP_RESET_STAGE_2:
            cls.park()
        else:
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

        elif l.startswith('home'):
            DeviceHandler.park()

        elif l.startswith('reset'):
            DeviceHandler.reset()

        elif l.startswith('rot:ccw'):
            DeviceHandler.full_rotate(DeviceHandler.DIR_CCW)

        elif l.startswith('rot'):
            DeviceHandler.full_rotate(DeviceHandler.DIR_CW)

    WriterPool.unregister(uid)


def start_dome():
    machine.freq(160000000)

    loop = uasyncio.get_event_loop()
    loop.create_task(DeviceHandler.main())
    loop.create_task(uasyncio.start_server(conn_handler, "0.0.0.0", 8081))
    loop.run_forever()
    loop.close()
