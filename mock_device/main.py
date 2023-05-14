"""This is a simple example of an IoT device that sends telemetry and receives direct methods from IoTHub"""

import asyncio
import os
from azure.iot.device import (
    IoTHubSession,
    DirectMethodResponse,
    MQTTConnectionFailedError,
    MQTTError,
    Message,
)
import json
from dotenv import load_dotenv

load_dotenv()


CONNECTION_STRING = os.getenv("IOTHUB_DEVICE_CONNECTION_STRING")

import math


class Car:
    def __init__(self):
        self.direction = 0
        self.speed = 0
        self.x = 250
        self.y = 250

    def temperature(self):
        def temp_func(x, y):
            return x**2 - 28 * x + y**3 + 45 * y - 543 + x * y * 2

        return temp_func(self.x, self.y) / 1e6

    def change_direction(self, angle):
        """
        Change the direction of the car
        :param angle: angle in degrees to change the direction of the car.
        """
        if -180 <= angle <= 180:
            self.direction = angle
        else:
            raise ValueError("Angle must be between -180 and 180 degrees.")

    def change_speed(self, speed):
        """
        Changes the speed of the car
        :param speed: speed from 0 to 100 percent
        """
        if 0 <= speed <= 100:
            self.speed = speed
        else:
            raise ValueError("Speed must be between 0 and 100.")

    def step(self):
        """Updates and returns current position"""
        rad = math.radians(self.direction)
        self.x += self.speed * math.cos(rad)
        self.y += self.speed * math.sin(rad)
        # wrap around the screen
        if self.x > 500:
            self.x -= 500
        elif self.x < 0:
            self.x += 500

        if self.y > 500:
            self.y -= 500
        elif self.y < 0:
            self.y += 500

        return (self.x, self.y)

    def telemetry(self):
        return json.dumps({"x": self.x, "y": self.y})


async def receive_direct_method_requests(session, car):
    async with session.direct_method_requests() as method_requests:
        async for method_request in method_requests:
            if method_request.name == "speed":
                speed = int(method_request.payload)
                car.change_speed(speed)
                result = car.speed
                status = 200
            elif method_request.name == "direction":
                direction = int(method_request.payload)
                car.change_direction(direction)
                result = car.direction
                status = 200
            elif method_request.name == "telemetry":
                car.step()
                result = car.telemetry()
                status = 200
            elif method_request.name == "temperature":
                result = car.temperature()
                status = 200

            else:
                result = None
                status = 400
                print(
                    "Unknown Direct Method request received: {}".format(
                        method_request.name
                    )
                )
            method_response = DirectMethodResponse.create_from_method_request(
                method_request, status, {"result": result}
            )

            await session.send_direct_method_response(method_response)


async def main():
    car = Car()

    while True:
        try:
            print("Connecting to IoT Hub...")
            async with IoTHubSession.from_connection_string(
                CONNECTION_STRING
            ) as session:
                print("Connected to IoT Hub")

                await asyncio.gather(
                    # send_telemetry(session, car),
                    receive_direct_method_requests(session, car),
                )

        except MQTTError:
            # Connection has been lost. Reconnect on next pass of loop.
            print("Dropped connection. Reconnecting in 1 second")
            await asyncio.sleep(1)
        except MQTTConnectionFailedError:
            # Connection failed to be established. Retry on next pass of loop.
            print("Could not connect. Retrying in 10 seconds")
            await asyncio.sleep(10)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Exit application because user indicated they wish to exit.
        print("User initiated exit. Exiting.")
