import logging
import can
import cantools
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PlantCANInterface:
    """
    Handles CAN I/O for the Plant Simulator node.
    """

    def __init__(self, interface: str = "vcan0", dbc_path: str = "can/bms_pack.dbc"):
        self._db = cantools.database.load_file(dbc_path)
        self._bus = can.interface.Bus(channel=interface, interface="socketcan")
        logger.info("Plant CAN Interface initialized on %s", interface)

    def publish_state(self, state: Dict[str, Any]):
        """
        Encodes and sends plant state messages.
        """
        # 1. BMS_CellVoltages (0x200 / 512)
        cell_msg = self._db.get_message_by_name("BMS_CellVoltages")
        cell_data = cell_msg.encode({
            "Cell_1_Voltage": state["cells"][0],
            "Cell_2_Voltage": state["cells"][1],
            "Cell_3_Voltage": state["cells"][2],
            "Cell_4_Voltage": state["cells"][3],
        })
        self._bus.send(can.Message(arbitration_id=cell_msg.frame_id, data=cell_data))

        # 2. BMS_PackStatus (0x202 / 514)
        status_msg = self._db.get_message_by_name("BMS_PackStatus")
        status_data = status_msg.encode({
            "SOC": state["soc"],
            "SOH": state["soh"],
            "Current": state["current"],
        })
        self._bus.send(can.Message(arbitration_id=status_msg.frame_id, data=status_data))

    def read_inputs(self) -> Dict[str, Any]:
        """
        Reads latest commands from MUT or Framework.
        """
        msg = self._bus.recv(0.01)
        if msg:
            try:
                msg_def = self._db.get_message_by_frame_id(msg.arbitration_id)
                return msg_def.decode(msg.data)
            except:
                pass
        return {}
