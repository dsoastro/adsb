# Monitoring airplanes with RTL-SDR dongle and python script

Monitoring is performed by decoding ADS-B signal from airplane in 1090 MHz range. 

The code in this repo is subject to GPL v2 license terms.

## Installation. RTL-SDR
```
sudo apt-get install rtl-sdr libatlas-base-dev
echo "blacklist dvb_usb_rtl28xxu" | sudo tee /etc/modprobe.d/rtlsdr.conf
sudo reboot
```

## Installation. Python application
```
git clone https://github.com/dsoastro/adsb
cd adsb
pip3 install -r requirements.txt
```

## Getting started

### Writing info on the ADS-B signal to stdout
```
rtl_sdr -f 1090000000  -s 2000000   -g 40 - | python3 log_messages.py
```
All messages except for df11 messages are shown. The total number of messages for a given icao is printed when a multiple of 10 is reached. 

### Getting notification on the airplane flying nearby
```
rtl_sdr -f 1090000000  -s 2000000   -g 40 - | python3 send_messages_bot.py
```
Set your position, maximum distance to the plane to send notification, telegram bot token and chat id  

### Showing airplane information table
On computer with rtl-sdr dongle  
```
rtl_sdr -f 1090000000  -s 2000000   -g 40 - | python3 send_messages_tui.py
```
On computer to display the information table 
```
python3 tui.py
```
Example output  
```
ICAO     Callsign          Pos                                     Alt       Speed                         Msgs      Last seen
 683266                                                                                                    2/2       10:17:78
 151df1                                                                      450.0/125.9E/-19.2/IAS        15/10     10:21:21
 15203a                                                                                                    3/3       10:17:50
 142584                                                                      674.1/89.7E/633.6/TAS         14/11     10:23:45
 151f18                   (55.59425, 38.06671)/32.3               5895.0                                   6/4       10:23:37
```
Explanation  
`Pos` Position of the airplane  
`Alt` Altitude of the airplane  
`Msgs` Received messages. The first number - the total number of messages. The second number - the messages of df11 type.  
`(55.59425, 38.06671)/32.3` (lattitude, longitude of the airplane)/distance to the airplane from observer  
`674.1/89.7E/633.6/TAS` speed (km/h),  heading (degrees), vertical rate (m/min), speed type (`GS` for ground speed, `AS` for airspeed) 

## Configuration (conf.py)

OBSERVER_LAT. Observer lattitude  
OBSERVER_LON. Observer longitude  
MAX_PROXIMITY_DST. Max proximity of airplane to observer (in km) for sending notification with telegram bot  
TOKEN. Telegram bot token  
CHAT_ID. Telegram chat id  
SERVER. IP address of server with running information table script (tui.py)  
PORT. Port the information table script listens on  

## Additional info

https://habr.com/ru/articles/443498/  
http://airmetar.main.jp/radio/ADS-B%20Decoding%20Guide.pdf  
