import asyncio
from bleak import BleakScanner, BleakClient
import logging
from phue import Bridge  # For Hue bridge (WiFi) control

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HueGestureController:
    def __init__(self, connection_mode='ble'):
        """
        Initialize the controller
        :param connection_mode: 'ble' for direct BLE or 'bridge' for Hue bridge
        """
        self.connection_mode = connection_mode
        self.hue_bridge_ip = '192.168.1.100'  # Change to your Hue Bridge IP
        self.hue_ble_name = "Hue"  # Partial name for BLE discovery
        
        # Gesture to action mapping - updated with your gestures
        self.gesture_actions = {
            'M': self.toggle_power,
            'X': self.activate_party_mode,
            'T': self.set_reading_mode,
            'circle': self.increase_brightness,
            'triangle': self.decrease_brightness,
            'square': self.toggle_color_scene
        }
        
        # BLE client
        self.hue_client = None
        
    async def connect_to_hue(self):
        """Connect to Hue device based on selected mode"""
        if self.connection_mode == 'ble':
            return await self.connect_to_hue_ble()
        else:
            return self.connect_to_hue_bridge()
    
    async def connect_to_hue_ble(self):
        """Connect to Hue bulb via BLE"""
        logger.info("Searching for Hue BLE devices...")
        devices = await BleakScanner.discover()
        for d in devices:
            if self.hue_ble_name in d.name:
                logger.info(f"Found Hue bulb: {d.name} at {d.address}")
                self.hue_client = BleakClient(d.address)
                try:
                    await self.hue_client.connect()
                    logger.info("Connected to Hue bulb via BLE")
                    return True
                except Exception as e:
                    logger.error(f"Hue BLE connection failed: {e}")
                    return False
        logger.error("No Hue BLE bulb found")
        return False
    
    def connect_to_hue_bridge(self):
        """Connect to Hue bridge (WiFi)"""
        try:
            self.bridge = Bridge(self.hue_bridge_ip)
            self.bridge.connect()
            self.bridge.get_api()
            logger.info("Connected to Hue bridge")
            return True
        except Exception as e:
            logger.error(f"Hue bridge connection failed: {e}")
            return False
    
    async def send_hue_command(self, command):
        """Send command to Hue bulb"""
        if self.connection_mode == 'ble' and self.hue_client:
            try:
                # Example BLE command - adjust with actual Hue BLE characteristics
                await self.hue_client.write_gatt_char(
                    "0000fff3-0000-1000-8000-00805f9b34fb",  # Example char UUID
                    command.encode()
                )
                return True
            except Exception as e:
                logger.error(f"BLE command failed: {e}")
                return False
        elif self.connection_mode == 'bridge' and hasattr(self, 'bridge'):
            try:
                lights = self.bridge.lights
                for light in lights:
                    if command == "brightness_up":
                        current = light.brightness
                        light.brightness = min(254, current + 50)
                    elif command == "brightness_down":
                        current = light.brightness
                        light.brightness = max(0, current - 50)
                    elif command == "toggle_power":
                        light.on = not light.on
                    elif command == "party_mode":
                        light.xy = [0.5, 0.5]  # Vivid color
                        light.brightness = 254
                        light.saturation = 254
                    elif command == "reading_mode":
                        light.xy = [0.3, 0.3]  # Neutral white
                        light.brightness = 200
                        light.saturation = 100
                    elif command == "toggle_scene":
                        # Cycle through scenes
                        scenes = self.bridge.scenes
                        current = light.scene
                        next_scene = (current + 1) % len(scenes) if current else 0
                        light.scene = scenes[next_scene]
                return True
            except Exception as e:
                logger.error(f"Bridge command failed: {e}")
                return False
        return False
    
    async def toggle_power(self):
        """Toggle bulb power state (M gesture)"""
        logger.info("Toggling power (M gesture)")
        await self.send_hue_command("toggle_power")
    
    async def activate_party_mode(self):
        """Activate party mode (X gesture)"""
        logger.info("Activating party mode (X gesture)")
        await self.send_hue_command("party_mode")
    
    async def set_reading_mode(self):
        """Set reading mode (T gesture)"""
        logger.info("Setting reading mode (T gesture)")
        await self.send_hue_command("reading_mode")
    
    async def increase_brightness(self):
        """Increase brightness (circle gesture)"""
        logger.info("Increasing brightness (circle gesture)")
        await self.send_hue_command("brightness_up")
    
    async def decrease_brightness(self):
        """Decrease brightness (triangle gesture)"""
        logger.info("Decreasing brightness (triangle gesture)")
        await self.send_hue_command("brightness_down")
    
    async def toggle_color_scene(self):
        """Toggle color scene (square gesture)"""
        logger.info("Toggling color scene (square gesture)")
        await self.send_hue_command("toggle_scene")
    
    async def process_gesture(self, gesture):
        """Execute action based on recognized gesture"""
        action = self.gesture_actions.get(gesture)
        if action:
            await action()
        else:
            logger.warning(f"Unknown gesture received: {gesture}")
    
    async def run_serial_mode(self, port=None):
        """Run in serial mode, receiving gestures from Arduino/ESP"""
        import serial
        import serial.tools.list_ports
        
        if not port:
            # Auto-detect Arduino/ESP port
            ports = serial.tools.list_ports.comports()
            for p in ports:
                if 'Arduino' in p.description or 'ESP' in p.description:
                    port = p.device
                    break
        
        if not port:
            logger.error("No Arduino/ESP port found")
            return
        
        try:
            ser = serial.Serial(port, baudrate=115200, timeout=1)
            logger.info(f"Connected to {port}")
            
            while True:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    logger.info(f"Received gesture: {line}")
                    await self.process_gesture(line)
                
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Serial communication error: {e}")
        finally:
            if 'ser' in locals():
                ser.close()
    
    async def run_ble_mode(self):
        """Run in BLE mode, receiving gestures from BLE device"""
        # This would be similar to your ESP code's BLE implementation
        # You would need to implement the BLE client side to receive gestures
        pass
    
    async def run(self, input_mode='serial'):
        """Main execution loop"""
        # First connect to Hue
        if not await self.connect_to_hue():
            logger.error("Could not connect to Hue device")
            return
            
        if input_mode == 'serial':
            await self.run_serial_mode()
        elif input_mode == 'ble':
            await self.run_ble_mode()
        else:
            logger.error(f"Unknown input mode: {input_mode}")

if __name__ == "__main__":
    # Choose connection mode: 'ble' or 'bridge'
    # Choose input mode: 'serial' (from Arduino/ESP) or 'ble' (direct from wand)
    controller = HueGestureController(connection_mode='bridge')
    
    try:
        asyncio.run(controller.run(input_mode='serial'))
    except KeyboardInterrupt:
        logger.info("Exiting...")