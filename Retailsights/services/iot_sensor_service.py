"""
IoT Sensor Integration Service
Real-time monitoring of temperature, humidity, and environmental conditions.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import random  # For simulated sensor data
from ..db import get_connection
from ..logger import logger


class IoTSensorService:
    """IoT sensor monitoring and alerts."""
    
    # Temperature thresholds (Celsius)
    TEMP_THRESHOLDS = {
        "frozen": {"min": -25, "max": -15, "name": "Frozen Foods"},
        "chilled": {"min": 0, "max": 5, "name": "Chilled/Dairy"},
        "ambient": {"min": 15, "max": 25, "name": "Ambient/Dry Goods"}
    }
    
    @staticmethod
    def register_sensor(
        shop_id: int,
        sensor_id: str,
        sensor_type: str,
        location: str,
        zone_type: str
    ) -> Dict[str, Any]:
        """Register new IoT sensor."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO iot_sensors 
                (shop_id, sensor_id, sensor_type, location, zone_type, status, registered_at)
                VALUES (%s, %s, %s, %s, %s, 'active', NOW())
                ON DUPLICATE KEY UPDATE 
                    location = VALUES(location),
                    zone_type = VALUES(zone_type),
                    status = 'active'
            """, (shop_id, sensor_id, sensor_type, location, zone_type))
            
            conn.commit()
            
            return {
                "success": True,
                "sensor_id": sensor_id,
                "message": f"Sensor {sensor_id} registered successfully"
            }
            
        except Exception as e:
            logger.error(f"register_sensor error: {e}")
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    @staticmethod
    def record_sensor_reading(
        sensor_id: str,
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        door_open: Optional[bool] = None,
        power_status: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Record sensor reading and check for alerts."""
        conn = get_connection()
        try:
            # Get sensor info
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT id, shop_id, zone_type, location 
                FROM iot_sensors 
                WHERE sensor_id = %s AND status = 'active'
            """, (sensor_id,))
            
            sensor = cur.fetchone()
            
            if not sensor:
                return {"success": False, "error": "Sensor not found or inactive"}
            
            # Insert reading
            cur.execute("""
                INSERT INTO sensor_readings 
                (sensor_id, temperature, humidity, door_open, power_status, recorded_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (sensor_id, temperature, humidity, door_open, power_status))
            
            reading_id = cur.lastrowid
            
            # Check for alerts
            alerts = []
            zone_type = sensor['zone_type']
            thresholds = IoTSensorService.TEMP_THRESHOLDS.get(zone_type, {})
            
            if temperature is not None and thresholds:
                if temperature < thresholds['min']:
                    alerts.append({
                        "severity": "HIGH",
                        "type": "TEMP_TOO_LOW",
                        "message": f"Temperature {temperature}°C below minimum {thresholds['min']}°C",
                        "location": sensor['location']
                    })
                elif temperature > thresholds['max']:
                    alerts.append({
                        "severity": "HIGH",
                        "type": "TEMP_TOO_HIGH",
                        "message": f"Temperature {temperature}°C above maximum {thresholds['max']}°C",
                        "location": sensor['location']
                    })
            
            if door_open:
                alerts.append({
                    "severity": "MEDIUM",
                    "type": "DOOR_OPEN",
                    "message": f"Fridge/freezer door open at {sensor['location']}",
                    "location": sensor['location']
                })
            
            if power_status is False:
                alerts.append({
                    "severity": "CRITICAL",
                    "type": "POWER_FAILURE",
                    "message": f"Power failure detected at {sensor['location']}",
                    "location": sensor['location']
                })
            
            # Store alerts
            for alert in alerts:
                cur.execute("""
                    INSERT INTO sensor_alerts 
                    (sensor_id, shop_id, severity, alert_type, message, triggered_at, resolved)
                    VALUES (%s, %s, %s, %s, %s, NOW(), FALSE)
                """, (sensor_id, sensor['shop_id'], alert['severity'], 
                      alert['type'], alert['message']))
            
            conn.commit()
            
            return {
                "success": True,
                "reading_id": reading_id,
                "alerts": alerts,
                "alert_count": len(alerts)
            }
            
        except Exception as e:
            logger.error(f"record_sensor_reading error: {e}")
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    @staticmethod
    def get_sensor_dashboard(shop_id: int) -> Dict[str, Any]:
        """Real-time sensor dashboard."""
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            
            # Get all sensors with latest readings
            cur.execute("""
                SELECT 
                    s.sensor_id,
                    s.sensor_type,
                    s.location,
                    s.zone_type,
                    s.status,
                    r.temperature,
                    r.humidity,
                    r.door_open,
                    r.power_status,
                    r.recorded_at as last_reading,
                    TIMESTAMPDIFF(MINUTE, r.recorded_at, NOW()) as minutes_since_reading
                FROM iot_sensors s
                LEFT JOIN (
                    SELECT sensor_id, temperature, humidity, door_open, 
                           power_status, recorded_at,
                           ROW_NUMBER() OVER (PARTITION BY sensor_id ORDER BY recorded_at DESC) as rn
                    FROM sensor_readings
                ) r ON s.sensor_id = r.sensor_id AND r.rn = 1
                WHERE s.shop_id = %s
                ORDER BY s.location
            """, (shop_id,))
            
            sensors = cur.fetchall()
            
            # Get active alerts
            cur.execute("""
                SELECT 
                    sensor_id,
                    severity,
                    alert_type,
                    message,
                    triggered_at
                FROM sensor_alerts
                WHERE shop_id = %s AND resolved = FALSE
                ORDER BY 
                    CASE severity 
                        WHEN 'CRITICAL' THEN 1 
                        WHEN 'HIGH' THEN 2 
                        WHEN 'MEDIUM' THEN 3 
                        ELSE 4 
                    END,
                    triggered_at DESC
            """, (shop_id,))
            
            alerts = cur.fetchall()
            
            # Count sensors by status
            total_sensors = len(sensors)
            offline_sensors = len([s for s in sensors if not s['last_reading'] or s.get('minutes_since_reading', 999) > 15])
            alert_count = len(alerts)
            
            return {
                "shop_id": shop_id,
                "summary": {
                    "total_sensors": total_sensors,
                    "online_sensors": total_sensors - offline_sensors,
                    "offline_sensors": offline_sensors,
                    "active_alerts": alert_count
                },
                "sensors": sensors,
                "alerts": alerts,
                "updated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"get_sensor_dashboard error: {e}")
            return {}
        finally:
            conn.close()
    
    @staticmethod
    def get_temperature_history(
        sensor_id: str,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get temperature history for charts."""
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT 
                    recorded_at as timestamp,
                    temperature,
                    humidity,
                    door_open
                FROM sensor_readings
                WHERE sensor_id = %s
                  AND recorded_at >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                ORDER BY recorded_at ASC
            """, (sensor_id, hours))
            
            return cur.fetchall()
            
        except Exception as e:
            logger.error(f"get_temperature_history error: {e}")
            return []
        finally:
            conn.close()
    
    @staticmethod
    def predict_spoilage_risk(shop_id: int) -> List[Dict[str, Any]]:
        """
        Predict products at risk of spoilage based on temperature violations.
        """
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            
            # Find sensors with recent temperature violations
            cur.execute("""
                SELECT 
                    s.sensor_id,
                    s.location,
                    s.zone_type,
                    COUNT(DISTINCT sa.id) as violation_count,
                    AVG(sr.temperature) as avg_temp,
                    MAX(sa.triggered_at) as last_violation
                FROM iot_sensors s
                JOIN sensor_alerts sa ON s.sensor_id = sa.sensor_id
                JOIN sensor_readings sr ON s.sensor_id = sr.sensor_id
                WHERE s.shop_id = %s
                  AND sa.alert_type IN ('TEMP_TOO_HIGH', 'TEMP_TOO_LOW')
                  AND sa.triggered_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                  AND sr.recorded_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                GROUP BY s.sensor_id, s.location, s.zone_type
                HAVING violation_count > 0
            """, (shop_id,))
            
            violations = cur.fetchall()
            
            at_risk = []
            for violation in violations:
                # Find products in this location
                location_keyword = violation['location'].split()[0]  # e.g., "Dairy" from "Dairy Fridge 1"
                
                cur.execute("""
                    SELECT 
                        p.id,
                        p.sku,
                        p.name,
                        p.category,
                        e.expiry_date,
                        e.days_left,
                        e.quantity_remaining
                    FROM products p
                    JOIN expiry_records e ON p.id = e.product_id
                    WHERE p.shop_id = %s
                      AND e.status = 'active'
                      AND (p.category LIKE %s OR p.name LIKE %s)
                    LIMIT 10
                """, (shop_id, f"%{location_keyword}%", f"%{location_keyword}%"))
                
                products = cur.fetchall()
                
                if products:
                    at_risk.append({
                        "location": violation['location'],
                        "zone_type": violation['zone_type'],
                        "violation_count": violation['violation_count'],
                        "avg_temperature": violation['avg_temp'],
                        "last_violation": violation['last_violation'],
                        "risk_level": "HIGH" if violation['violation_count'] > 3 else "MEDIUM",
                        "affected_products": len(products),
                        "products": products[:5],  # Top 5
                        "recommendation": "Inspect immediately - potential spoilage risk"
                    })
            
            return at_risk
            
        except Exception as e:
            logger.error(f"predict_spoilage_risk error: {e}")
            return []
        finally:
            conn.close()
    
    @staticmethod
    def simulate_sensor_data(shop_id: int, sensor_count: int = 5) -> Dict[str, Any]:
        """
        Generate simulated sensor data for demo purposes.
        In production, this receives real data from IoT devices via MQTT/HTTP.
        """
        zones = [
            {"type": "frozen", "location": "Frozen Section Zone A"},
            {"type": "frozen", "location": "Frozen Section Zone B"},
            {"type": "chilled", "location": "Dairy Fridge 1"},
            {"type": "chilled", "location": "Meat Chiller"},
            {"type": "ambient", "location": "Main Store Floor"}
        ]
        
        results = []
        
        for i, zone in enumerate(zones[:sensor_count]):
            sensor_id = f"SENSOR-{shop_id}-{i+1:03d}"
            
            # Register sensor
            IoTSensorService.register_sensor(
                shop_id=shop_id,
                sensor_id=sensor_id,
                sensor_type="temperature_humidity",
                location=zone['location'],
                zone_type=zone['type']
            )
            
            # Generate realistic reading
            thresholds = IoTSensorService.TEMP_THRESHOLDS[zone['type']]
            base_temp = (thresholds['min'] + thresholds['max']) / 2
            
            # 10% chance of violation for demo
            if random.random() < 0.1:
                temperature = base_temp + random.uniform(5, 10)  # Violation
            else:
                temperature = base_temp + random.uniform(-1, 1)  # Normal
            
            humidity = random.uniform(40, 60)
            door_open = random.random() < 0.05  # 5% chance door open
            
            result = IoTSensorService.record_sensor_reading(
                sensor_id=sensor_id,
                temperature=round(temperature, 1),
                humidity=round(humidity, 1),
                door_open=door_open,
                power_status=True
            )
            
            results.append({
                "sensor_id": sensor_id,
                "location": zone['location'],
                "result": result
            })
        
        return {
            "simulated": True,
            "sensors_created": len(results),
            "results": results
        }
