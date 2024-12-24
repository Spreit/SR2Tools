# original:
# https://aluigi.altervista.org/papers/quickbms-src-0.12.0.zip
#    src/included/unyakuza.c
#    ignored Line 34 to 69.
def unyakuza(input_data: bytes, src_size: int, dest_size: int) -> bytes:
    decomp_buff = [0] * dest_size

    src_idx = 0
    dest_idx = 0
    
    flag_bit_idx = 8
    #bit   7 6 5 4 3 2 1 0
    #index 0 1 2 3 4 5 6 7
    flag = input_data[src_idx]
    src_idx += 1
    
    # print('{0:#X}'.format(len(decomp_buff)))

    while (dest_idx < dest_size):
        if (src_idx >= src_size):
            return input_data
        
        is_comp = ((flag & 0x80) != 0)
        
        flag = flag << 1
        flag_bit_idx -= 1
        if (flag_bit_idx < 1):
            flag = input_data[src_idx]
            src_idx += 1
            flag_bit_idx = 8
        
        if (is_comp):
            if (src_idx < 0x20):
                #print('src_idx: {0:#X}'.format(src_idx))
                pass
            ref_offset = ((input_data[src_idx] >> 4) | (input_data[src_idx+1] << 4)) + 1
            length = (input_data[src_idx] & 0x0F) + 3
            for j in range(length):
                if (dest_idx >= dest_size):
                    break
                decomp_buff[dest_idx] = decomp_buff[dest_idx - ref_offset]
                dest_idx += 1
            src_idx += 2
        else:
            if (dest_idx >= dest_size):
                break
            decomp_buff[dest_idx] = input_data[src_idx]
            dest_idx += 1
            src_idx += 1
    
    return bytearray(decomp_buff)


def uncompress_SR2_subtexture(subtexture_bytes) -> bytes:
    compression_header = subtexture_bytes[:16]
    # Mini header
    uncompressed_size = int.from_bytes(compression_header[4:8], "little")
    compressed_size = int.from_bytes(compression_header[8:12], "little")

    subtexture_bytes = unyakuza(subtexture_bytes[16:], compressed_size - 16, uncompressed_size)
    subtexture_bytes = bytes(subtexture_bytes)

    return subtexture_bytes
