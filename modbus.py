def crc16(data):
    reg = 0xffff
    A001 = 0xa001
    for c in range(len(data)):
        reg ^= data[c]
        count = 0
        while count < 8: 
            count += 1
            low = reg & 0x0001
            reg >>= 1
            if low == 0:
                continue
            reg ^= A001
    crc = ((reg << 8) & 0xff00) | ((reg >> 8) & 0x00ff)
    return crc

def readRegister(dev_addr):
    data = bytearray(b'\x00'*6)
    data[0] = dev_addr & 0xff
    data[1] =  0x03
    data[2] = 0x00
    data[3] = 0x01
    crc = crc16(data[:4])
    data[4] = (crc >> 8) & 0xff
    data[5] = crc & 0xff
    return data
    
def writeRegister(dev_addr,reg_addr,reg_value):
    data = bytearray(b"\x00"*10)
    data[0] = dev_addr & 0xff
    data[1] =  0x06
    data[2] = (reg_addr >>8) & 0xff
    data[3] = reg_addr & 0xff
    data[4] = (reg_value >> 24) & 0xff
    data[5] = (reg_value >> 16) & 0xff
    data[6] = (reg_value >> 8) & 0xff
    data[7] = (reg_value & 0xff)
    crc = crc16(data[:8])
    data[8] = (crc >> 8) & 0xff
    data[9] = crc & 0xff
    return data
    
def read_cmd(addr):
    cmd = readRegister(int(addr))
    return cmd

def reset(exp):
    adr = int(exp)
    cmd = writeRegister(adr,0x01,0x00)
    return cmd

def set_value(addr,va):
    return writeRegister(addr,0x01,va)

if __name__ == "__main__":
    import ubinascii
    pass

    
