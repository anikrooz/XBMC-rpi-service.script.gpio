# XBMC-rpi-service.script.gpio
Simple script to notify / modify GPIO status from within XBMC skin

USAGE:
(In eg. Home.xml)
<onload>Runscript(script.GPIO, backend=true, ins=0, ins=1)</onload>
Then, in a control

<onfocus>SetProperty(GPIOon, 17)</onfocus>
	<onunfocus>SetProperty(GPIOoff, 17)</onunfocus>

And, for example, an icon to denote status:
  <control>
   <description>Test</description>
   <type>image</type>
   <id>0</id>
   <width>63</width>
   <height>60</height>
   <posx>100</posx>
   <posy>128</posy>
   <texture>handbrake.png</texture>
   <visible>SubString(Window(home).Property(GPIO0), "0")</visible>
  </control>
