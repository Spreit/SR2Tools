# Conversion functions for RGB565, ARGB1555, ARGB4444 and RGBA8888 color spaces
# Split into individual functions for speed. You know what it is, right, Python?


def convertRGB565toRGBA8888(pixel_bytes) -> list:
    rgba8888_pixel_list = []
    for i in range(0, len(pixel_bytes), 2):
        twopixelbytes = int.from_bytes(pixel_bytes[i:i + 2], "little")

        R8 = (twopixelbytes & 0b1111100000000000) >> 8  # >> 11 and * 8
        G8 = (twopixelbytes & 0b0000011111100000) >> 3  # >> 5 and * 4
        B8 = (twopixelbytes & 0b0000000000011111) << 3  # * 8
        # A8 = 255

        rgba8888_pixel_list.append((R8, G8, B8, 255))
    return rgba8888_pixel_list


def convertARGB1555toRGBA8888(pixel_bytes) -> list:
    rgba8888_pixel_list = []
    for i in range(0, len(pixel_bytes), 2):
        twopixelbytes = int.from_bytes(pixel_bytes[i:i + 2], "little")

        R8 = (twopixelbytes & 0b0111110000000000) >> 7  # >> 10 and * 8
        G8 = (twopixelbytes & 0b0000001111100000) >> 2  # >> 5 and * 8
        B8 = (twopixelbytes & 0b0000000000011111) << 3  # * 8
        A8 =((twopixelbytes & 0b1000000000000000) >> 15) * 255

        rgba8888_pixel_list.append((R8, G8, B8, A8))
    return rgba8888_pixel_list


def convertARGB4444toRGBA8888(pixel_bytes) -> list:
    rgba8888_pixel_list = []
    for i in range(0, len(pixel_bytes), 2):
        twopixelbytes = int.from_bytes(pixel_bytes[i:i + 2], "little")

        R8 = (twopixelbytes & 0b0000111100000000) >> 4
        G8 = (twopixelbytes & 0b0000000011110000)
        B8 = (twopixelbytes & 0b0000000000001111) << 4
        A8 = (twopixelbytes & 0b1111000000000000) >> 8

        rgba8888_pixel_list.append((R8, G8, B8, A8))
    return rgba8888_pixel_list


def convertARGB8888toRGB565bytes(color_array) -> bytes:
    bytes_list = []
    for row in color_array:
        for pixel in row:
            red_value   = pixel[0]
            green_value = pixel[1]
            blue_value  = pixel[2]

            # Int because numpy
            R = int(red_value   >> 3) << 11
            G = int(green_value >> 2) << 5
            B = int(blue_value  >> 3)

            bytes_list.append(R + G + B)

    return b''.join(output_pixel.to_bytes(2, "little") for output_pixel in bytes_list)


def convertARGB8888toRGBA1555bytes(color_array) -> bytes:
    bytes_list = []
    for row in color_array:
        for pixel in row:
            red_value   = pixel[0]
            green_value = pixel[1]
            blue_value  = pixel[2]

            try:
                alpha_value = pixel[3]
            except:
                alpha_value = 255

            A = (alpha_value >> 7) << 15
            R = (red_value   >> 3) << 10
            G = (green_value >> 3) << 5
            B = blue_value  >> 3

            bytes_list.append(A + R + G + B)

    return b''.join(output_pixel.to_bytes(2, "little") for output_pixel in bytes_list)


def convertARGB8888toARGB4444bytes(color_array) -> bytes:
    bytes_list = []
    for row in color_array:
        for pixel in row:
            red_value   = pixel[0]
            green_value = pixel[1]
            blue_value  = pixel[2]

            try:
                alpha_value = pixel[3]
            except:
                alpha_value = 255

            A = int(alpha_value >> 4) << 12
            R = int(red_value   >> 4) << 8
            G = int(green_value >> 4) << 4
            B = int(blue_value  >> 4)

            bytes_list.append(A + R + G + B)

    return b''.join(output_pixel.to_bytes(2, "little") for output_pixel in bytes_list)
