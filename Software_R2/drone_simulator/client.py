"""Optimized client for drone simulator WebSocket server with advanced flight control."""
import asyncio
import json
import sys
import websockets
import time
import re
from typing import Dict, Any, Optional, Tuple
from logging_config import get_logger

logger = get_logger("optimized_client")

class OptimizedDroneClient:
    """Advanced WebSocket client for drone simulator with optimized flight control."""
    
    def _init_(self, uri: str = "ws://localhost:8765"):
        self.uri = uri
        self.connection_id = None
        self.telemetry = {}
        self.metrics = {}
        self.start_time = time.time()
        self.command_count = 0
        self.crash_avoidance_mode = False
        logger.info(f"Optimized drone client initialized with server URI: {uri}")
    
    async def connect(self) -> None:
        """Connect to the WebSocket server with robust error handling."""
        logger.info(f"Attempting optimized connection to {self.uri}")
        
        try:
            async with websockets.connect(
                self.uri, 
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5
            ) as websocket:
                response = await websocket.recv()
                data = json.loads(response)
                self.connection_id = data.get("connection_id")
                logger.info(f"Connected successfully with ID: {self.connection_id}")
                
                # Start optimized flight control immediately
                await self.optimized_flight_control(websocket)
                
        except Exception as e:
            logger.error(f"Connection error: {e}", exc_info=True)
            raise
    
    async def send_command(self, websocket, speed: int, altitude: int, movement: str) -> Optional[Dict[str, Any]]:
        """Send optimized command to the drone server with safety checks."""
        try:
            # Validate command parameters before sending
            speed = max(0, min(5, speed))
            altitude = self._adjust_altitude_based_on_conditions(altitude)
            
            data = {
                "speed": speed,
                "altitude": altitude,
                "movement": movement
            }
            self.command_count += 1
            logger.debug(f"Sending optimized command #{self.command_count}: {data}")
            
            await websocket.send(json.dumps(data))
            response = await websocket.recv()
            return json.loads(response)
            
        except Exception as e:
            logger.error(f"Error in send_command: {e}", exc_info=True)
            return None
    
    async def optimized_flight_control(self, websocket) -> None:
        """Advanced flight control algorithm to maximize distance and iterations."""
        logger.info("Starting optimized flight control algorithm")
        
        try:
            # Initial ascent to safe altitude
            await self._safe_ascent(websocket, target_altitude=50)
            
            # Main flight loop
            while True:
                # Get current telemetry
                response = await self.send_command(3, 0, "fwd")
                if not response or response.get("status") == "crashed":
                    break
                
                self._update_telemetry(response["telemetry"])
                self.metrics = response["metrics"]
                
                # Dynamic adjustment based on conditions
                speed, altitude, movement = self._calculate_optimal_movement()
                
                # Send optimized command
                response = await self.send_command(speed, altitude, movement)
                if not response or response.get("status") == "crashed":
                    break
                
                # Update state and check conditions
                self._update_telemetry(response["telemetry"])
                self.metrics = response["metrics"]
                
                # Emergency checks
                if self._should_activate_crash_avoidance():
                    await self._activate_crash_avoidance(websocket)
                
                # Small delay to prevent overwhelming the server
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error in flight control: {e}", exc_info=True)
        finally:
            self._log_flight_summary()
    
    def _update_telemetry(self, telemetry_str: str) -> None:
        """Parse and update telemetry data from the server response."""
        # Example telemetry format: X-123-Y-456-BAT-78-GYR-[1,2,3]-WIND-5-DUST-2-SENS-GREEN
        pattern = r"X-(?P<x_position>-?\d+)-Y-(?P<y_position>\d+)-BAT-(?P<battery>\d+)-" \
                  r"GYR-\[(?P<gx>-?\d+),(?P<gy>-?\d+),(?P<gz>-?\d+)\]-" \
                  r"WIND-(?P<wind_speed>\d+)-DUST-(?P<dust_level>\d+)-" \
                  r"SENS-(?P<sensor_status>GREEN|YELLOW|RED)"
        
        match = re.match(pattern, telemetry_str)
        if match:
            self.telemetry = {k: int(v) if v.lstrip('-').isdigit() else v 
                            for k, v in match.groupdict().items()}
    
    def _calculate_optimal_movement(self) -> Tuple[int, int, str]:
        """Determine the best movement parameters based on current conditions."""
        # Base values
        speed = 3  # Moderate default speed
        altitude_change = 0
        movement = "fwd"
        
        # Adjust based on battery
        if self.telemetry["battery"] < 30:
            speed = max(1, speed - 1)
            if self.telemetry["y_position"] > 20:
                altitude_change = -1  # Descend slightly to conserve battery
        
        # Adjust based on sensor status
        if self.telemetry["sensor_status"] == "YELLOW":
            altitude_change = -1 if self.telemetry["y_position"] > 50 else 0
        elif self.telemetry["sensor_status"] == "RED":
            altitude_change = -2 if self.telemetry["y_position"] > 3 else 0
        
        # Adjust based on wind
        if self.telemetry["wind_speed"] > 5:
            speed = min(4, speed + 1)  # Slightly increase speed to overcome wind
        
        # Random variation to prevent patterns
        if time.time() % 10 < 2:  # 20% chance to vary
            altitude_change += 1 if time.time() % 2 else -1
        
        return speed, altitude_change, movement
    
    def _should_activate_crash_avoidance(self) -> bool:
        """Check if we need to activate emergency crash avoidance."""
        if self.telemetry["sensor_status"] == "RED" and self.telemetry["y_position"] > 2:
            return True
        if self.telemetry["battery"] < 15:
            return True
        if abs(self.telemetry["gx"]) > 30 or abs(self.telemetry["gy"]) > 30:
            return True
        return False
    
    async def _activate_crash_avoidance(self, websocket) -> None:
        """Execute emergency procedures to avoid crashing."""
        logger.warning("Activating crash avoidance mode")
        self.crash_avoidance_mode = True
        
        # Rapid descent if sensor status is RED
        if self.telemetry["sensor_status"] == "RED":
            while self.telemetry["y_position"] > 2:
                response = await self.send_command(1, -2, "fwd")
                if not response or response.get("status") == "crashed":
                    return
                self._update_telemetry(response["telemetry"])
        
        # Return to base if battery is low
        elif self.telemetry["battery"] < 15:
            response = await self.send_command(2, -1, "rev")
            if not response or response.get("status") == "crashed":
                return
            self._update_telemetry(response["telemetry"])
        
        self.crash_avoidance_mode = False
    
    async def _safe_ascent(self, websocket, target_altitude: int) -> None:
        """Safely ascend to a target altitude."""
        logger.info(f"Executing safe ascent to {target_altitude}")
        
        while self.telemetry.get("y_position", 0) < target_altitude:
            response = await self.send_command(1, 1, "fwd")
            if not response or response.get("status") == "crashed":
                break
            self._update_telemetry(response["telemetry"])
            await asyncio.sleep(0.2)
    
    def _adjust_altitude_based_on_conditions(self, altitude: int) -> int:
        """Adjust altitude change based on current conditions."""
        current_alt = self.telemetry.get("y_position", 0)
        
        # Prevent going too high (risk of instability)
        if current_alt > 1000 and altitude > 0:
            return 0
        
        # Prevent going too low
        if current_alt < 10 and altitude < 0:
            return 0
        
        return altitude
    
    def _log_flight_summary(self) -> None:
        """Log the final flight statistics."""
        duration = time.time() - self.start_time
        distance = self.metrics.get("total_distance", 0)
        iterations = self.metrics.get("iterations", 0)
        
        logger.info(f"Flight summary - Duration: {duration:.1f}s, "
                   f"Distance: {distance}, Iterations: {iterations}")
        print(f"\nFlight completed - Distance: {distance}, Iterations: {iterations}")

def main() -> None:
    """Start the optimized drone client."""
    uri = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8765"
    logger.info(f"Starting Optimized Drone Client with server URI: {uri}")
    
    client = OptimizedDroneClient(uri)
    try:
        asyncio.run(client.connect())
    except KeyboardInterrupt:
        logger.info("Optimized client stopped by user")
        print("\nOptimized client stopped by user")
    except Exception as e:
        logger.error(f"Client error: {e}", exc_info=True)
        print(f"\nError: {e}")

if __name__ == "_main_":
    main()