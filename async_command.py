import time


# ACK value
ACK_ERROR = -1
ACK_TIMEOUT = 0
ACK_SUCCESS = 1


class CommandPacket:
    def __init__(self,topic,cmd,ack='',callback_fun =None,
        callback_params=None,check_fun=None,timeout=3):
        self.timestamp = time.time()
        self.topic = topic
        self.cmd = cmd
        self.ack = ack
        self.timeout = 3
        self.callback_fun = callback_fun
        self.callback_params = callback_params
        self.check_fun = check_fun
        self.valid = True


    def __repr__(self):
        return self.cmd


    def register_callback(self,callback,userdata,check):
        self.callback_fun = callback
        self.callback_params = userdata
        self.check_fun = check


    def check_and_callback(self,message):
        if self.valid == False:
            return

        if self.callback_fun is None:
            return
        
        try:

            if self.ack:
                msg = message.payload.decode('utf8')
                topic = message.topic
                if msg == self.ack:
                    self.callback_fun(self.callback_params,ACK_SUCCESS)
                    self.valid = False
        
            if self.check_timeout():
                return
            
            if self.check_fun and self.check_fun(self,message) == True:
                self.callback_fun(self.callback_params,ACK_SUCCESS)
                self.valid = False
                
        except Exception as e:
            self.callback_fun(self.callback_params,ACK_ERROR)
            self.valid = False


    def check_timeout(self):
        ret = False
        tnow = time.time()
        if tnow - self.timestamp > self.timeout:
            if self.callback_fun:
                self.callback_fun(self.callback_params,ACK_TIMEOUT)
                self.valid = False
                ret = True

        return ret
            


class CommandManagent(object):
    def __init__(self):
        self.packet_list = []


    def push(self,packet):
        if len(self.packet_list)<10:
            self.packet_list.append(packet)


    def len(self):
        return len(self.packet_list)


    def loop(self,message):
        for packet in self.packet_list:
            packet.check_and_callback(message)
            if packet.valid == False:
                self.packet_list.remove(packet)
            

def mycallback(user,ack):
    pass
    print("callback",user,ack)

def mycheck(obj,message):
    pass
    print("mycheck",obj,message)
    return True

def _test():
    m = CommandManagent()
    c = CommandPacket('/dev/topic/','cmd2')
    c.register_callback(mycallback,None,mycheck)
    m.push(CommandPacket('/dev/topic/','cmd1','ack'))
    m.push(c)
    m.push(CommandPacket('test3','cmd3'))
    m.loop('')
    print(m.packet_list)

    
if __name__ == '__main__':
    _test()
    
