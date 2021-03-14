import logging
import time

from indi.device import Driver, non_blocking, properties
from indi.device.pool import default_pool
from indi.message import const
from indi.message import DelProperty
from indi.device.properties.const import DriverInterface
from indi.device.properties import standard

import settings
import os
import json

if os.environ.get("SIM", None):
    from .hardware.NodeSim import NodeSim as NodeHardware
else:
    from .hardware.NodeSerial import NodeSerial as NodeHardware

logger = logging.getLogger(__name__)


@default_pool.register
class NodeFocuser(Driver):
    name = "NODE_FOCUSER"
    NUM_BOOKMARKS = 10

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.focuser = NodeHardware(settings.FOCUSER_PORT, onupdate=self.device_updated)
        self.BOOKMARKS = {}

    general = properties.Group(
        "GENERAL",
        vectors=dict(
            connection=standard.common.Connection(),
            driver_info=standard.common.DriverInfo(
                interface=(DriverInterface.FOCUSER,)
            ),
            info=properties.TextVector(
                "INFO",
                enabled=False,
                perm=const.Permissions.READ_ONLY,
                elements=dict(
                    manufacturer=properties.Text(
                        "MANUFACTURER", default="Wiktor Latanowicz"
                    ),
                    camera_model=properties.Text(
                        "FOCUSER_MODEL", default="NodeFocuser"
                    ),
                    ip=properties.Text("IP_ADDRESS", default=settings.FOCUSER_IP),
                ),
            ),
        ),
    )
    general.connection.connect.onwrite = "connect"

    position = properties.Group(
        "POSITION",
        enabled=False,
        vectors=dict(
            position=standard.focuser.AbsolutePosition(min=0, max=15000, step=1),
            motion=standard.focuser.FocusMotion(),
            rel_position=standard.focuser.RelativePosition(),
            fmax=standard.focuser.FocusMax(),
            speed=properties.NumberVector(
                "SPEED",
                elements=dict(
                    speed=properties.Number(
                        "SPEED_VALUE",
                        default=100,
                    )
                ),
            ),
        ),
    )
    position.position.position.onwrite = "reposition"
    position.rel_position.position.onwrite = "step"
    position.speed.speed.onchange = "change_speed"

    bookmarks = properties.Group(
        "BOOKMARKS",
        enabled=False,
        vectors={
            **{
                f"save{i}": properties.TextVector(
                    f"SAVE_BOOKMARK_{i}",
                    elements={
                        f"bookmark{i}": properties.Text(
                            f"SAVE_BOOKMARK_{i}",
                            onwrite="save_bookmark_eventhandler",
                        )
                    },
                )
                for i in range(NUM_BOOKMARKS)
            },
            **dict(
                restore=properties.SwitchVector(
                    "RESTORE_BOOKMARK",
                    rule=const.SwitchRule.AT_MOST_ONE,
                    elements={
                        f"bookmark{i}": properties.Switch(
                            f"RESTORE_BOOKMARK_{i}",
                            default=const.SwitchState.OFF,
                            onwrite="restore_bookmark_eventhandler",
                        )
                        for i in range(NUM_BOOKMARKS)
                    },
                ),
            ),
        },
    )

    @non_blocking
    def connect(self, sender, value):
        connected = value == const.SwitchState.ON
        self.general.connection.state_ = const.State.BUSY

        if connected:
            try:
                self.focuser.connect()
                pos = None
                for _ in range(30):
                    time.sleep(1)
                    pos = self.focuser.get_position()
                    if pos is not None:
                        self.position.position.position.reset_value(pos)
                        break
                if pos is None:
                    raise Exception("Did not get focuser position")
                self.general.connection.state_ = const.State.OK
            except Exception as e:
                self.general.connection.state_ = const.State.ALERT
                connected = False
                logger.error(e)

        self.general.connection.connect.bool_value = connected
        self.position.enabled = connected
        self.general.info.enabled = connected
        self.bookmarks.enabled = connected
        self.load_bookmarks()

    def device_updated(self):
        self.position.position.position.state_ = (
            const.State.OK if self.focuser.get_status() == "idle" else const.State.BUSY
        )
        self.position.position.position.value = self.focuser.get_position()

    def reposition(self, sender, value):
        self.focuser.set_position(value)

    def change_speed(self, event):
        self.focuser.set_speed(self.position.speed.speed.value)

    def step(self, sender, value):
        self.position.rel_position.position.state_ = const.State.BUSY
        current_position = self.position.position.position.value
        direction = 1 if self.position.motion.outward.bool_value else -1
        new_value = current_position + direction * value

        self.focuser.set_position(new_value)

        self.position.rel_position.position.state_ = const.State.OK

    def _save_file_path(self):
        return os.path.join(os.path.dirname(__file__), "BOOKMARKS.json")

    def save_bookmarks(self):
        with open(self._save_file_path(), "w") as f:
            f.write(json.dumps(self.BOOKMARKS))

    def load_bookmarks(self):
        try:
            with open(self._save_file_path(), "r") as f:
                self.BOOKMARKS = {int(k): v for k, v in json.loads(f.read()).items()}
        except Exception as e:
            print(e)
            pass
        self.refresh_bookmarks()

    def refresh_bookmarks(self):
        for i in range(self.NUM_BOOKMARKS):
            save, restore = self._get_bookmark_elements(i)
            bookmark = self._get_bookmark(i)
            save.value = bookmark["label"]
            restore._definition.label = f'{bookmark["label"]} @ {bookmark["position"]}'

        delmsg = DelProperty(device=self.name, name="RESTORE_BOOKMARK")
        self.send_message(delmsg)
        defmsg = self.bookmarks.restore.to_def_message()
        self.send_message(defmsg)

    def _get_bookmark_elements(self, idx):
        save = getattr(getattr(self.bookmarks, f"save{idx}"), f"bookmark{idx}")
        restore = getattr(self.bookmarks.restore, f"bookmark{idx}")
        return save, restore

    def _get_bookmark(self, idx):
        empty = {
            "label": "Unnamed",
            "position": 0,
        }
        return self.BOOKMARKS.get(idx, empty)

    def save_bookmark_eventhandler(self, sender, value):
        idx = int(sender.name.rsplit("_", 1)[-1])
        self.BOOKMARKS[idx] = {
            "label": value,
            "position": self.position.position.position.value,
        }
        self.save_bookmarks()
        self.refresh_bookmarks()

    def restore_bookmark_eventhandler(self, sender, value):
        if value == const.SwitchState.ON:
            idx = int(sender.name.rsplit("_", 1)[-1])
            bookmark = self._get_bookmark(idx)
            self.focuser.set_position(bookmark["position"])

            for i in range(self.NUM_BOOKMARKS):
                if i != idx:
                    save, restore = self._get_bookmark_elements(i)
                    restore.value = const.SwitchState.OFF
