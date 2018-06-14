# main.py -- put your code here!
import pyb
import ujson
import ubinascii
import struct
from statemachine import StateMachine
import zigbee
import rs485
import modbus

default_did = '91000001'
did = '91000001'
period = 5
MeterCounter = 1

stm = None
zb = None
uart = None
usb = None
led1 = None
led2 = None
led3 = None
password = "123456"
save_flag = False
usb_flag = True
addr64 = bytearray([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
send_retry_count=0
cmd_request_list = []

dev_status = ["E","E","E","E","E","E","E","E"]
dev_flag = [0,0,0,0,0,0,0,0]
dev_send_flag = True
dev_db = 0
cmd_index = 1
cmd_reset_index =1

cmd_addr = 1
cmd_value = 0


count = 0

def read_params():
    global stm,period,did,MeterCounter
    
    json_txt = ''
    param_dict={}
    MeterCounter = 1
    try:           
        with open('config.json',"r") as f:
            json_txt = f.read()
            param_dict = ujson.loads(json_txt)
    except Exception as e:
        print(e)
        return
        
    
    did = param_dict.get("did",did)
    period = param_dict.get("period",period)
    if period > 0:
        stm.reset_period_task_dt("task2",period*1000)

    MeterCounter = param_dict.get("MeterCounter",MeterCounter)

    
def save_params():
    global did,period,MeterCounter
    try:
        with open('config.json','w+') as f:
            msg = '{"did":"%s","period":%d,"MeterCounter":%d}' % (did,period,MeterCounter)
            f.write(msg)
            f.flush()
    except:
        pass

def set_save_params_flag():
    global stm,save_flag
    if stm:
        stm.reset_period_task("task4")
    save_flag = True

def usb_handler(data):
    global usb,cmd_request_list,period,did,MeterCounter,save_flag,usb_flag,cmd_addr,cmd_value,cmd_reset_index
    #global tmp_reset,setValue,tmp_setPointCount
    led1.on()
    param_dict = {}
    try:
        data = bytes(data)
        param_dict = ujson.loads(data)
    except Exception as e:
        led1.off()
        return

    tmp = param_dict.get("tid",None)
    if tmp is not None:
        tid = tmp
    else:
        tid = 0xffff
        
    tmp = param_dict.get("params",None)
    if tmp is not None:
        if tmp=="all":
            msg = '{"did":"%s","period":%d,"num":%d,"tid":%d}' % (did,period,MeterCounter,tid)
            usb.write(msg)
            led1.off()
            return

    tmp = param_dict.get("at","")
    if len(tmp)==2:
        params = param_dict.get("params","")
        if params:
            usb_flag = True
            params_hex = ubinascii.unhexlify(params)
            zb.at_cmd(tmp,params_hex)
        else:
            usb_flag = True
            zb.at_cmd(tmp,"")
        led1.off()
        return

    tmp = param_dict.get("password","")
    if tmp!=password:
        msg = '{"method":"ack","error":"password invalid","tid":%d}' % tid
        usb.write(msg)
        led1.off()
        return

    tmp = param_dict.get("params","")
    if tmp=="save":
        msg = '{"method":"ack","params":"save","tid":%d}' % tid
        usb.write(msg)
        led1.off()
        set_save_params_flag()
        return

        
    tmp = param_dict.get("period",0)
    if tmp > 0:
        period = tmp
        stm.reset_period_task_dt("task2",period*1000)
        msg = '{"method":"ack","period":%d,"tid":%d}' % (period,tid)
        usb.write(msg)
        set_save_params_flag()
    
    tmp = param_dict.get("num",0)
    if 0< tmp < 7:
        MeterCounter = tmp
        msg = '{"method":"ack","num":%d,"tid":%d}' % (MeterCounter,tid)
        usb.write(msg)
        set_save_params_flag()

    tmp_did = param_dict.get("did","")
    if tmp_did:
        did = tmp_did
        msg = '{"method":"ack","did":%s,"tid":%d}' % (did,tid)
        usb.write(msg)
        set_save_params_flag()

    tmp = param_dict.get("params","")
    if tmp=="reset":
        did = default_did
        period = 5
        MeterCounter = 1
        msg = '{"method":"ack","params":"reset","tid":%d}' % tid
        usb.write(msg)
        led1.off()
        return

    tmp_reset = param_dict.get("reset",0)
    if type(tmp_reset)==int:
        if tmp_reset > MeterCounter:
            tmp_reset = MeterCounter
        if 1<= tmp_reset <= MeterCounter:
            cmd_reset_index = 1
            for i in range(tmp_reset):
                cmd_request_list.append(2)
            msg = '{"method":"ack","reset":%d,"tid":%d}' % (tmp_reset,tid)
            usb.write(msg)
            led1.off()
            
    else:
        msg = '{"method":"ack","error":"param invalid","tid":%d}' % tid
        usb.write(msg)
        led1.off()
        return

    addr = param_dict.get("a",0)
    if type(addr)==int:
        if 1<= addr <= MeterCounter:
            cmd_addr = addr
            va = param_dict.get("v",None)
            if va is not None:
                cmd_value = va
                cmd_request_list.append(3)
            msg = '{"method":"ack","a":%d,"v":%d,"tid":%d}' % (cmd_addr,cmd_value,tid)
            usb.write(msg)
            led1.off()
            
    else:
        msg = '{"method":"ack","error":"param invalid","tid":%d}' % tid
        usb.write(msg)
        led1.off()
        return
        
    led1.off()
    
def on_receive(addr64, data):
    global stm,zb,period,did,MeterCounter,save_flag,usb_flag,cmd_request_list,cmd_addr,cmd_value,cmd_reset_index

    #print(addr64)
    #print(data)
    led1.on()
    param_dict = {}
    try:
        data = bytes(data)
        param_dict = ujson.loads(data)
    except:
        #print("on_receive json fail")
        led1.off()
        return

    tmp = param_dict.get("tid",None)
    if tmp is not None:
        tid = tmp
    else:
        tid = 0xffff
        
    tmp = param_dict.get("params",None)
    if tmp is not None:
        if tmp=="all":
            msg = '{"did":"%s","period":%d,"num":%d,"tid":%d}' % (did,period,MeterCounter,tid)
            zb.send_data(addr64,msg)
            led1.off()
            return

    tmp = param_dict.get("at","")
    if len(tmp)==2:
        params = param_dict.get("params","")
        if params:
            usb_flag = False
            params_hex = ubinascii.unhexlify(params)
            zb.at_cmd(tmp,params_hex)
        else:
            usb_flag = False
            zb.at_cmd(tmp,"")
        led1.off()
        return

    tmp = param_dict.get("password","")
    if tmp!=password:
        msg = '{"method":"ack","error":"password invalid","tid":%d}' % tid
        zb.send_data(addr64,msg)
        led1.off()
        return

    tmp = param_dict.get("params","")
    if tmp=="save":
        msg = '{"method":"ack","params":"save","tid":%d}' % tid
        zb.send_data(addr64,msg)
        led1.off()
        set_save_params_flag()
        return

        
    tmp = param_dict.get("period",0)
    if tmp > 0:
        period = tmp
        stm.reset_period_task_dt("task2",period*1000)
        msg = '{"method":"ack","period":%d,"tid":%d}' % (period,tid)
        zb.send_data(addr64,msg)
        set_save_params_flag()
    
    tmp = param_dict.get("num",0)
    if 0< tmp <7:
        MeterCounter = tmp
        msg = '{"method":"ack","num":%d,"tid":%d}' % (MeterCounter,tid)
        zb.send_data(addr64,msg)
        set_save_params_flag()

    tmp_did = param_dict.get("did","")
    if tmp_did:
        did = tmp_did
        msg = '{"method":"ack","did":%s,"tid":%d}' % (did,tid)
        zb.send_data(addr64,msg)
        set_save_params_flag()

    tmp = param_dict.get("params","")
    if tmp=="reset":
        did = default_did
        period = 5
        MeterCounter = 1
        msg = '{"method":"ack","params":"reset","tid":%d}' % tid
        zb.send_data(addr64,msg)
        led1.off()
        set_save_params_flag()
        return

    tmp_reset = param_dict.get("reset",0)
    if type(tmp_reset)==int:
        if tmp_reset > MeterCounter:
            tmp_reset = MeterCounter
        if 1<= tmp_reset <= MeterCounter:
            cmd_reset_index = 1
            for i in range(tmp_reset):
                cmd_request_list.append(2)
            msg = '{"method":"ack","reset":%d,"tid":%d}' % (tmp_reset,tid)
            zb.send_data(addr64,msg)
            led1.off()
    else:
        msg = '{"method":"ack","error":"param invalid","tid":%d}' % tid
        zb.send_data(addr64,msg)
        led1.off()
        return

    addr = param_dict.get("a",0)
    if type(addr)==int:
        if 1<= addr <= MeterCounter:
            cmd_addr = addr
            va = param_dict.get("v",None)
            if va is not None:
                cmd_value = va
                cmd_request_list.append(3)
            msg = '{"method":"ack","a":%d,"v":%d,"tid":%d}' % (cmd_addr,cmd_value,tid)
            zb.send_data(addr64,msg)
            led1.off()
    else:
        msg = '{"method":"ack","error":"param invalid","tid":%d}' % tid
        zb.send_data(addr64,msg)
        led1.off()
        return
        
    led1.off()


def on_at_cmd(cmd, params):
    global usb,zb,usb_flag,dev_db
    if len(cmd)!=2:
        return

    at_str = bytes(cmd).decode('utf8')
    if at_str == 'db':
        #params_bytes = params_bytes.decode('utf8')
        dev_db = int(params[0])
        #print("db",dev_db)

    else:
        params_bytes = ubinascii.hexlify(params)
        params_hex = params_bytes.decode('utf8')
        msg = '{"method":"ack","at":"%s","params":"%s"}' % (at_str,params_hex)
        if usb_flag ==True:
            usb.write(msg)
        else:
            zb.send_data(addr64,msg)


def on_send_status(status):
    global send_retry_count
    if status !=0:
        send_retry_count +=1
        if send_retry_count >= 3:
            send_retry_count = 0
            zb.reset()


def on_rs_receive(data):
    global zb,led3,did,count,MeterCounter,period
    global dev_status,dev_flag,dev_send_flag

    #led1.on()
    #print(data)
    #led1.off()
    count = 0
    led3.on()
    
    if len(data)!=11:
        led3.off()
        return
    
    if modbus.crc16(data)!=0:
        led3.off()
        return
    
    try:
        count = struct.unpack('!l',data[5:9])[0]
    except:
        pass
        return

    #msg = '{"did":"%s","addr":%u,"count":%d,"num":%d,"period":%d}' % (did , data[0] , count,MeterCounter,period)
    #zb.send_data(addr64,msg)
    #led3.off()
    #return
            
    dev_index = int(data[0])-1
    dev_status[dev_index] = count
    dev_flag[dev_index] -=1

        
    #msg_dict = {'d':did,'c':dev_status[:MeterCounter]}
    #zb.send_data(addr64,ujson.dumps(msg_dict))
    #dev_send_flag = True
    led3.off()


def period_task1():
    pyb.LED(2).toggle()
    #zb.at_cmd('ai',"")

    
def period_task2():
    global zb,led3,dev_db,cmd_request_list,did,cmd_index,MeterCounter,dev_flag,dev_status,dev_send_flag
    led3.on()

    for i in range(MeterCounter):
        if dev_flag[i]>=1:
            dev_status[i] = 'E'
            dev_flag[i] = 0

    #if not dev_send_flag:
    msg_dict = {'d':did,'c':dev_status[:MeterCounter],'b':dev_db}
    zb.send_data(addr64,ujson.dumps(msg_dict))

    
    cmd_index =1
    for i in range(MeterCounter):
        cmd_request_list.append(1)

    dev_send_flag = False

            
    led3.off()
    zb.at_cmd('db',"")


def period_task3():
    global rs_485,zb,cmd_request_list
    global cmd_index,cmd_reset_index,MeterCounter,cmd_addr,cmd_value,dev_flag
    
    
    if len(cmd_request_list) > 0:
        led3.on()
        cmd_request_id = cmd_request_list.pop(0)
        if cmd_request_id == 1:
            if cmd_index <= MeterCounter:
                cmd = modbus.read_cmd(cmd_index)
                rs_485.clear_buf()
                rs_485.write(cmd)
                dev_flag[cmd_index-1] +=1
                cmd_index +=1
                

        elif cmd_request_id == 2:
            if cmd_reset_index <= MeterCounter:
                cmd = modbus.reset(cmd_reset_index)
                rs_485.clear_buf()
                rs_485.write(cmd)
                cmd_reset_index +=1

        elif cmd_request_id == 3:
            if cmd_addr <= MeterCounter:
                cmd = modbus.set_value(cmd_addr,cmd_value)
                rs_485.clear_buf()
                rs_485.write(cmd)
                
        led3.off()    


def period_task4():
    global save_flag
    
    if save_flag == True:
        save_flag = False
        save_params()

        
def async_task():
    global zb
    global usb
    zb.loop()
    rs_485.loop()
    n = usb.any()
    if n>0:
        data = usb.read()
        usb_handler(data)


def action_idle():
    pass
        

def action1():
    pyb.LED(1).on()
    stm.switch_task("action2")


def action2():
    pyb.LED(1).off()
    stm.switch_task("idle")


def system_init():
    global uart,usb,zb,rs_485,led1,led2,led3
    uart = pyb.UART(2,9600)
    usb = pyb.USB_VCP()
    led1 = pyb.LED(1)
    led2 = pyb.LED(2)
    led3 = pyb.LED(3)
    led1.off()
    led2.off()
    led3.off()
    rs_485 = rs485.RS485(5,9600)
    rs_485.register_receive_callback(on_rs_receive)
    zb = zigbee.ZigBee(uart)
    zb.register_receive_callback(on_receive)
    zb.register_atm_callback(on_at_cmd)
    zb.register_send_callback(on_send_status)
    

def main():
    global stm
    stm = StateMachine()
    stm.add_period_task("loop",async_task,0)
    stm.add_period_task("task1",period_task1,1000)
    stm.add_period_task("task2",period_task2,period*1000)
    stm.add_period_task("task3",period_task3,200)
    stm.add_period_task("task4",period_task4,1500)
    
    stm.add_state("action1",action1)
    stm.add_state("action2",action2)
    stm.add_state("idle",action_idle)
    stm.set_start("action1")
    system_init()
    read_params()   
    stm.run()

if __name__ == "__main__":
    main()
    pass
