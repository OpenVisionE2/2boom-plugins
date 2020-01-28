#Edit By RAED 2020

from Screens.Screen import Screen
from Components.Pixmap import Pixmap

SKIN_HD = """
<screen name="QCIfH" position="50,165" size="1180,335" title="2boom's QuickChannelInfo for Hotkey" zPosition="1">
  <widget source="session.FrontendStatus" render="Label" position="420,5" zPosition="2" size="360,35" font="Regular; 33" foregroundColor="#00aaaaaa" halign="center" valign="center" transparent="1">
    <convert type="FrontendInfo">SNRdB</convert>
  </widget>
  <eLabel name="snr" text="SNR:" position="5,85" size="100,35" font="Regular;33" halign="right" foregroundColor="#00aaaaaa" transparent="1" />
  <widget source="session.FrontendStatus" render="Progress" position="135,50" size="910,100" pixmap="~/images/bar.png" zPosition="2" borderWidth="4" borderColor="un656565">
    <convert type="FrontendInfo">SNR</convert>
  </widget>
  <widget source="session.FrontendStatus" render="Label" position="1080,85" size="100,35" font="Regular;33" foregroundColor="#00aaaaaa" transparent="1">
    <convert type="FrontendInfo">SNR</convert>
  </widget>
  <eLabel name="agc" text="AGC:" position="5,190" size="100,35" font="Regular;33" halign="right" foregroundColor="#00aaaaaa" transparent="1" />
  <widget source="session.FrontendStatus" render="Progress" position="135,160" size="910,100" pixmap="~/images/bar.png" zPosition="2" borderWidth="4" borderColor="un656565">
    <convert type="FrontendInfo">AGC</convert>
  </widget>
  <widget source="session.FrontendStatus" render="Label" position="1080,190" size="100,35" font="Regular;33" foregroundColor="#00aaaaaa" transparent="1">
    <convert type="FrontendInfo">AGC</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="133,270" size="575,30" font="Regular; 27" foregroundColor="#00aaaaaa" transparent="1" halign="left" zPosition="5" valign="center">
    <convert type="ServiceName">Name</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="131,304" zPosition="3" size="350,25" valign="top" halign="left" font="Regular; 22" transparent="1" foregroundColor="#00aaaaaa">
    <convert type="ServiceName">Provider</convert>
  </widget>
</screen>"""

SKIN_FHD = """
<screen name="QCIfH" position="center,175" size="1180,340" title="2boom's QuickChannelInfo for Hotkey" zPosition="1">
  <eLabel name="snrdb" text="SNRdB:" position="864,5" size="110,28" font="Regular; 25" halign="left" foregroundColor="#00aaaaaa" transparent="1" />
  <widget source="session.FrontendStatus" render="Label" position="956,5" zPosition="2" size="110,28" font="Regular; 25" halign="left" valign="center" transparent="1">
    <convert type="FrontendInfo2">SNRdB</convert>
  </widget>
  <eLabel name="snr" text="SNR:" position="5,75" size="100,30" font="Regular; 27" halign="right" foregroundColor="#00aaaaaa" transparent="1" />
  <widget source="session.FrontendStatus" render="Progress" position="135,40" size="910,100" pixmap="~/images/bar.png" zPosition="2" borderWidth="4" borderColor="#00aaaaaa">
    <convert type="FrontendInfo2">SNR</convert>
  </widget>
  <widget source="session.FrontendStatus" render="Label" position="1080,75" size="100,30" font="Regular; 27" transparent="1">
    <convert type="FrontendInfo2">SNR</convert>
  </widget>
  <eLabel name="agc" text="AGC:" position="5,180" size="100,30" font="Regular; 27" halign="right" foregroundColor="#00aaaaaa" transparent="1" />
  <widget source="session.FrontendStatus" render="Progress" position="135,148" size="910,100" pixmap="~/images/bar.png" zPosition="2" borderWidth="4" borderColor="#00aaaaaa">
    <convert type="FrontendInfo2">AGC</convert>
  </widget>
  <widget source="session.FrontendStatus" render="Label" position="1080,175" size="100,30" font="Regular; 27" transparent="1">
    <convert type="FrontendInfo2">AGC</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="133,5" size="575,28" font="Regular; 25" foregroundColor="#00aaaaaa" transparent="1" halign="left" zPosition="5" valign="center">
    <convert type="ServiceName2">%n | %N | %P</convert>
  </widget>
  <eLabel text="Video:" position="132,310" size="110,28" font="Regular; 25" transparent="1" foregroundColor="#00aaaaaa" />
  <widget source="vbit" render="Label" position="215,310" size="150,28" font="Regular; 25" zPosition="2" transparent="1" />
  <eLabel text="Audio:" position="365,310" size="110,28" font="Regular; 25" transparent="1" foregroundColor="#00aaaaaa" />
  <widget source="abit" render="Label" position="450,310" size="150,28" font="Regular; 25" zPosition="2" transparent="1" />
  <widget source="codec" render="Label" position="864,310" zPosition="4" size="180,28" valign="top" halign="right" font="Regular; 25" transparent="1" foregroundColor="#00aaaaaa" />
  <widget source="session.CurrentService" render="Label" position="132,252" size="910,28" font="Regular; 25" transparent="1" halign="center" noWrap="1" valign="center" zPosition="3">
    <convert type="ServiceName2">%S %s %F %p %Y %f %b %o %r</convert>
  </widget>
   <eLabel text="Nims:" position="710,5" size="110,28" font="Regular; 25" transparent="1" zPosition="5" foregroundColor="#00aaaaaa" />
  <widget source="session.FrontendInfo" render="Label" position="785,5" size="100,28" font="Regular; 25" transparent="1" zPosition="5">
    <convert type="TunerBar">#00aaaaaa, #00f0bf4f</convert>
  </widget>
<widget source="sids" render="Label"  position="132,281" size="910,28" font="Regular; 25" transparent="1" halign="center" noWrap="1" valign="center" zPosition="5" foregroundColor="#00aaaaaa" />
<widget source="resx" render="Label" font="Regular; 25" position="550,310" size="100,28" halign="right" transparent="1" foregroundColor="#00aaaaaa" />
<eLabel text="x" font="Regular; 25" position="650,310" size="18,28" halign="center" transparent="1" />
<widget source="resy" render="Label" font="Regular; 25" position="668,310" size="110,28" halign="left" transparent="1" foregroundColor="#00aaaaaa" />
<eLabel text="Fps:" position="770,310" size="90,28" font="Regular; 25" transparent="5" foregroundColor="#00aaaaaa" zPosition="5" />
<widget source="fps" render="Label" font="Regular; 25" position="830,310" size="90,28" halign="left" zPosition="1" transparent="1" valign="center" />
</screen>
"""
