import asyncio
import aiohttp
import logging
import os
import yaml
from dotenv import load_dotenv

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HueGestureController:
    def __init__(self):
        """Initialize with secure configuration"""
        self.ha_token = None
        self.ha_url = None
        self.session = None
        self.load_config()

        # Gesture action mappings
        self.gesture_actions = {
            'M': ('light/toggle', {"entity_id": "light.living_room_hue"}),
            'X': ('light/turn_on', {
                "entity_id": "light.living_room_hue",
                "effect": "colorloop",
                "brightness": 254
            }),
            'T': ('light/turn_on', {
                "entity_id": "light.living_room_hue",
                "color_temp": 366,
                "brightness": 200
            }),
            'circle': ('light/turn_on', {
                "entity_id": "light.living_room_hue",
                "brightness_step_pct": 15
            }),
            'triangle': ('light/turn_on', {
                "entity_id": "light.living_room_hue",
                "brightness_step_pct": -15
            })
        }

    def load_config(self):
        """Load configuration from secrets.yaml or .env"""
        try:
            # Try YAML first
            with open('secrets.yaml') as f:
                secrets = yaml.safe_load(f)
                self.ha_token = secrets['ha_token']
                self.ha_url = secrets.get('ha_url', 'http://localhost:8123')
                logger.info("Loaded config from secrets.yaml")
        except (FileNotFoundError, KeyError) as yaml_err:
            # Fallback to .env
            load_dotenv()
            self.ha_token = os.getenv('HA_TOKEN')
            self.ha_url = os.getenv('HA_URL', 'http://localhost:8123')
            logger.info("Loaded config from .env")
            
        if not self.ha_token:
            raise ValueError("No Home Assistant token found in secrets.yaml or .env")

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def send_ha_command(self, service, data):
        """Send secure command to Home Assistant"""
        url = f"{self.ha_url}/api/services/{service}"
        headers = {
            "Authorization": f"Bearer {self.ha_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.post(url, headers=headers, json=data) as resp:
                if resp.status == 200:
                    logger.info(f"Executed: {service}")
                else:
                    error = await resp.text()
                    logger.error(f"API Error {resp.status}: {error[:200]}")
        except Exception as e:
            logger.error(f"Network error: {str(e)[:100]}")

    async def process_gesture(self, gesture):
        """Handle incoming gesture"""
        if gesture in self.gesture_actions:
            service, data = self.gesture_actions[gesture]
            await self.send_ha_command(service, data)
        else:
            logger.warning(f"Unknown gesture: {gesture}")

    async def run_serial_mode(self, port=None):
        """Read gestures from serial port"""
        import serial
        import serial.tools.list_ports
        
        # Auto-detect port if not specified
        if not port:
            ports = [p.device for p in serial.tools.list_ports.comports()
                    if 'USB' in p.description or 'ACM' in p.device]
            port = ports[0] if ports else None
            
        if not port:
            logger.error("No suitable serial port found")
            return

        try:
            ser = serial.Serial(port, 115200, timeout=1)
            logger.info(f"Connected to {port}")
            
            while True:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    logger.info(f"Received: {line}")
                    await self.process_gesture(line)
                
                await asyncio.sleep(0.1)
                
        except serial.SerialException as e:
            logger.error(f"Serial error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            if 'ser' in locals() and ser.is_open:
                ser.close()

async def main():
    """Main async entry point"""
    try:
        async with HueGestureController() as controller:
            logger.info("Starting gesture controller")
            await controller.run_serial_mode()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        logger.info("Controller stopped")

if __name__ == "__main__":
    asyncio.run(main())