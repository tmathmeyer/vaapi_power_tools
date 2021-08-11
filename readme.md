# Vaapi Chromium Power Test Suite

## installing
 - requirements
  - python3.9
  - selenium python package

 - setup
  - clone this repo
  - download https://files.tedm.io/chromedriver
  - run `./install.sh`
  
## scripts & tools
 - install.sh
  - pulls the latest custom chromium build I've made

 - power_gadget
  - a custom build of intel's power gadged with some tweaks.
  - built from https://github.com/tmathmeyer/intel-power-gadget

 - demo_vaapi.py
  - uses selenium to auto-play 100 seconds of selected videos
  - records power usage during playback
  - exports to report.csv

## collecting power numbers
You'll probably have to edit `demo_vaapi.py` in order to get the
paths all set up properly. They're hardcoded for my laptop right now.

run `./demo_vaapi.py`
