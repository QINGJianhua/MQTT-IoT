import pyb

class RS485(object):
    def __init__(self, uart,baudrate):
        self.buffer = bytearray()
        self.notify_num = 11
        if uart==5:
            self.uart = pyb.UART(5,baudrate)
            self.enable = pyb.Pin('B3',pyb.Pin.OUT)
        elif uart ==4:
            self.uart = pyb.UART(4,baudrate)
            self.enable = pyb.Pin('C7',pyb.Pin.OUT)
        elif uart==3:
            self.uart = pyb.UART(3,baudrate)
            self.enable = pyb.Pin('C0',pyb.Pin.OUT)
        self.on_receive_fun = None

    def register_receive_callback(self,fun):
        self.on_receive_fun = fun

    def set_notify_num(self,num):
        self.notify_num = num

    def clear_buf(self):
        self.buffer = bytearray()

    def dataReceived(self, data):
        self.buffer.extend(data)

        
        if len(self.buffer)>=self.notify_num:
            data = self.buffer[:]
            self.buffer = bytearray()
            #print(data)
            #self.write(data)
            if self.on_receive_fun:
                self.on_receive_fun(data)

    def at_query_cmd(self,cmd):
        packet = bytearray()
        #packet.append('5')
        packet.extend(cmd)
        self.write(packet)


    def write(self, data):
        if len(data)<1:
            return
        if type(data)==type(''):
            data = data.encode()
        elif type(data)==type(bytearray()):
            data = bytes(data)

        self.enable.high()
        pyb.udelay(10)
        if self.uart:
            self.uart.write(data)
        pyb.udelay(1000)
        self.enable.low()
        pyb.udelay(10)


    def loop(self):
        n = self.uart.any()
        if n > 0:
            data = self.uart.read(n)
            if data:
                self.dataReceived(data)


def test(n):
    import pyb

    zb = RS485(n,9600)

    zb.at_query_cmd('1234')
    pyb.udelay(1000)
    zb.at_query_cmd('12345')
    while 1:
        zb.loop()


if __name__ == "__main__":
    test(5)
