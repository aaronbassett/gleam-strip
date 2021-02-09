import os
import board
import neopixel
import asyncio
import uvloop
import motor.motor_asyncio
from rich import print

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
motor_client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["DB_URL"])
db = motor_client[os.environ["DB_NAME"]]

pixel_pin = board.D18
num_pixels = 119
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=1, auto_write=False)

animation_type = ""
animation_speed = 0.05
rgb = (0, 0, 255)


def wheel(pos):
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (r, g, b)


async def rainbow_animation():
    while animation_type == "rainbow":
        for j in range(255):
            for i in range(num_pixels):
                if animation_type == "rainbow":
                    pixel_index = (i * 256) + j
                    pixels[i] = wheel(pixel_index & 255)
                else:
                    return
            pixels.show()
            await asyncio.sleep(animation_speed)


async def cylon_animation():
    while animation_type == "cylon":
        for i in range(num_pixels * 2):
            if animation_type == "cylon":
                pixels.fill((0, 0, 0))

                if i < num_pixels:  # going left
                    pixels[i] = rgb
                    if i > 0:
                        pixels[i - 1] = rgb
                    if i > 1:
                        pixels[i - 2] = rgb
                else:  # going right
                    x = (num_pixels * 2) - (i + 1)
                    pixels[x] = rgb

                    if x < num_pixels - 2:
                        pixels[x + 1] = rgb
                    if x < num_pixels - 3:
                        pixels[x + 2] = rgb

                pixels.show()
            else:
                return

            await asyncio.sleep(animation_speed)


async def static_lights():
    pixels.fill(rgb)
    pixels.show()
    return


async def fetch_strip():
    strip = await db.strips.find_one({"_id": os.environ["STRIP_ID"]})
    return strip


async def work():
    global animation_type
    global animation_speed
    global rgb
    while True:
        strip = await fetch_strip()
        rgb = tuple(int(strip["hex_color"][i : i + 2], 16) for i in (0, 2, 4))
        animation_speed = float(strip["animation_speed"])

        if animation_type != strip["animation"]:
            if strip["animation"] == "rainbow":
                asyncio.ensure_future(rainbow_animation())
            elif strip["animation"] == "cylon":
                asyncio.ensure_future(cylon_animation())
            else:
                asyncio.ensure_future(static_lights())

            animation_type = strip["animation"]
        await asyncio.sleep(1)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        asyncio.ensure_future(work())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print("Closing Loop")
        loop.close()