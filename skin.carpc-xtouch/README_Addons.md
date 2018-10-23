This skin is prepared to make use of some third party addons:

1. the WifiManager addon by hawkeyexp. It allows you to manage WiFi-connections with an easy to use interface. 
   For more infos about the addon see: 
   - http://raspicarprojekt.de/showthread.php?tid=915
   - http://engineeringdiy.freeforums.org/addon-wifimanager-0-1-4-t704.html
   Note: This addon works with Pi3 (builtin WiFi) and Pi2 (with compatible WiFi-Dongle).

2. the USB-Manager addon by hawkeyexp. It allows you to automatically detect and, if you want, mount/unmount HDDs and USB-Sticks on the fly. It's real Plug'n'Play!

3. the 1-Wire Dashboard addon by hawkeyexp. With this addon you can manage up to eight temperature-sensors. In the skin you have the option to display the output of five sensors in the logo area and another one sensor in the top left corner. 
   For more infos about the addon and the compatible sensor-types see: 
   - http://raspicarprojekt.de/showthread.php?tid=904
   
4. the X-Touch Helper addon by hawkeyexp. It allows you to store and switch between two different skin configurations. You can create for example a bright look for daytime and a more darker look for the night. You can switch between both settings manually by submenu buttons or automatically (scheduled). 
   For more infos about the addon see: 
   - http://raspicarprojekt.de/showthread.php?tid=913
   - http://engineeringdiy.freeforums.org/addon-x-touch-helper-for-jack-s-skin-0-0-6-t699.html
   
   
#########################################################################################
   
About Sakis3G:
   
	- This working only with sakis3g
	- The buttons send commands :
	- sudo /usr/bin/modem3g/sakis3g connect
	- sudo /usr/bin/modem3g/sakis3g disconnect

	- For install sakis3g 
	- wget "http://raspberry-at-home.com/files/sakis3g.tar.gz"
	- I suggest you copy the file to /usr/bin/modem3g directory and unpack it:

	- sudo mkdir /usr/bin/modem3g
	- sudo chmod 777 /usr/bin/modem3g
	- sudo cp sakis3g.tar.gz /usr/bin/modem3g
	- cd /usr/bin/modem3g
	- sudo tar -zxvf sakis3g.tar.gz
	- sudo chmod +x sakis3g

	- Config: (This is my config ,i use Huawei E3131)
	- sudo nano /etc/sakis3g.conf
	- Add:
	- APN="internet"
	MODEM="OTHER"
	OTHER="USBMODEM"
	USBINTERFACE="0"
	USBDRIVER="option"
	USBMODEM="12d1:1506"
	APN_USER="foo"
	APN_PASS="foo"

	- More info: http://raspberry-at-home.com/installing-3g-modem/
	
#########################################################################################
