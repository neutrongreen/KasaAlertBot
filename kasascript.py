#incldue json for file loading
import json
#import operators for operatior translation
import operator
#import kasa
import kasa


import collections

from socket import socket

import requests

import asyncio
optTranslation = {
    "rising": operator.lt,
    "falling": operator.gt
}

class kasadevice:
    def __init__(self, deviceip, operator, message, value, name, url):
        self.device = kasa.SmartPlug(deviceip)
        self.operator = optTranslation[operator]
        self.limwatt = value
        self.votlbuffer  = collections.deque(maxlen=3)
        self.current_power = 0
        self.message = message
        self.state = False
        self.name = name
        self.url = url

    async def update_power(self):
        while True:
            try:
                await self.device.update()
                self.votlbuffer.append((await self.device.get_emeter_realtime())["power_mw"])
                self.current_power = sum(self.votlbuffer)/len(self.votlbuffer)
                print("{} Power: {:.2f}W".format(self.name, self.current_power*0.001))
                if(self.operator(self.current_power, self.limwatt) and self.state):
                    print("Sending " + self.message)
                    await send_message(self.message, self.name)
                    self.state = False
                elif(not self.operator(self.current_power, self.limwatt) and not self.state):
                    self.state = True
            except:
                print("Error In {} is it connected?".format(self.name))    
            await asyncio.sleep(15)


            
devices = []
bot_url = ""

def loaddata(jsonName):
    with open(jsonName, "r+") as file:
        tempdata = json.load(file)
        for i in tempdata:
            devices.append(kasadevice(i["ip"], i["operator"], i["message"], i["value"], i["name"], bot_url))

def loadbot(jsonName):
    with open(jsonName, "r+") as file:
        tempdata = json.load(file)
        bot_url = tempdata["url"]
        print(bot_url)

async def send_message(message, name):
    data = {"username": name, "content": message}
    url = ''
    requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})

print("\nLoading Jsons...")
loaddata("data.json")
loadbot("bot.json")
print("Done\n")

async def main(loop):
    print("Done. Starting Loops\n")
    for i in devices:
        loop.create_task(i.update_power())

print("starting program")
loop = asyncio.events.new_event_loop()
loop.create_task(main(loop))
loop.run_forever()
