#!/usr/bin/env python3

from selenium import webdriver
import csv
import dataclasses
import multiprocessing
import os
import time


@dataclasses.dataclass
class Video:
  name: str
  url: str
  duration: int


VIDEOS = [
  Video('h264.480', 'http://storage.googleapis.com/watk/buck480p30_h264.mp4', 100),#634),
  Video('h264.720', 'https://', 0),
  Video('h264.1080', 'http://storage.googleapis.com/watk/buck1080p60_h264.mp4', 100),

  Video('vp9.480', 'http://storage.googleapis.com/watk/buck480p30_vp9.webm', 100),
  Video('vp9.720', 'https://', 0),
  Video('vp9.1080', 'http://storage.googleapis.com/watk/buck1080p_vp9.webm', 100),

  Video('vp8.480', 'https://', 0),
  Video('vp8.720', 'https://', 0),
  Video('vp8.1080', 'https://', 0),

  Video('av1.480', 'https://', 0),
  Video('av1.720', 'https://', 0),
  Video('av1.1080', 'https://', 0),
]


class VaapiMode():
  __slots__ = ('chrome_options', 'accel', 'vulkan', '_expected_accel', '_expected_vulkan')

  def __init__(self, options, accelerated, vulkan):
    self.chrome_options = options
    self.accel = accelerated
    self.vulkan = vulkan
    self._expected_accel = 'Hardware accelerated' if accelerated else 'Software only'
    self._expected_vulkan = 'Enabled' if vulkan else 'Disabled'

  def check_features(self, features):
    for feature in features.find_elements_by_tag_name('li'):
      if 'Video Decode' in feature.text:
        assert self._expected_accel in feature.text
      if 'Vulkan' in feature.text:
        assert self._expected_vulkan in feature.text

  def check_media_internals(self, driver):
    node = driver.find_element_by_id('player-list').find_elements_by_tag_name('li')[0]
    node.find_elements_by_tag_name('label')[0].click()
    for row in driver.find_element_by_id('log').find_elements_by_tag_name('tr'):
      data = row.find_elements_by_tag_name('td')
      if data and data[1].text == 'kVideoDecoderName':
        print(data[2].text)


class Stats():
  def __init__(self):
    self._stats = []
    self._header = ['timestamp']

  def generate_report(self, vaapi_mode, video):
    self._header.append(self.generate_report_name(vaapi_mode, video))
    with open('gadget_stat') as csvfile:
      index = 0
      for row in csv.reader(csvfile):
        time, power = row
        if time == 'Elapsed Time':
          continue
        time = round(float(time), 1)
        if len(self._stats) > index:
          self._stats[index].append(power)
        elif index != 0:
          self._stats.append([0] * len(self._stats[index-1]))
          self._stats[index][-1] = power
          self._stats[index][0] = time
        else:
          self._stats.append([time, power])
        index += 1

  def generate_report_name(self, vaapi_mode, video):
    if vaapi_mode.accel and vaapi_mode.vulkan:
      return f'HW0.{video.name}'
    if vaapi_mode.accel and not vaapi_mode.vulkan:
      return f'HWC.{video.name}'
    if not vaapi_mode.accel:
      return f'SW.{video.name}'
    return 'UNKNOWN'

  def export_report(self):
    with open('report.csv', 'w') as output:
      output.write(', '.join(self._header) + '\n')
      for line in self._stats:
        line = [str(l) for l in line]
        output.write(', '.join(line) + '\n')


def run_power_gadget(duration):
  os.system(f'sudo ./power_gadget -e 500 -d {duration} -f elapsed,powerW > gadget_stat')


def evaluate_video_power(vaapi_mode, video, stats):
  driver = webdriver.Chrome('./chromedriver', chrome_options=vaapi_mode.chrome_options)
  try:
    driver.get('chrome://gpu')
    vaapi_mode.check_features(driver.find_element_by_class_name('feature-status-list'))
    p = multiprocessing.Process(target=run_power_gadget, args=(video.duration,))
    driver.get(video.url)
    p.start()
    p.join()
    driver.execute_script("window.open();")
    driver.switch_to_window(driver.window_handles[1])
    driver.get('chrome://media-internals')
    vaapi_mode.check_media_internals(driver)
    stats.generate_report(vaapi_mode, video)
  finally:
    driver.quit()


def main():
  stats = Stats()

  vaapi_enabled = webdriver.chrome.options.Options()
  vaapi_enabled.add_argument('--enable-features=VaapiVideoDecoder')
  vaapi_enabled.add_argument('--enable-vulkan')
  vaapi_enabled.add_argument('--user-data-dir=/home/ted/documents/chrome/datadir')
  vaapi_enabled.binary_location = "/home/ted/documents/chrome/install/chrome"
  vaapi_mode = VaapiMode(vaapi_enabled, True, True)

  vaapi_disabled = webdriver.chrome.options.Options()
  vaapi_disabled.add_argument('--disable-features=VaapiVideoDecoder')
  vaapi_disabled.add_argument('--enable-vulkan')
  vaapi_disabled.add_argument('--user-data-dir=/home/ted/documents/chrome/datadir')
  vaapi_disabled.binary_location = "/home/ted/documents/chrome/install/chrome"
  sw_mode = VaapiMode(vaapi_disabled, False, True)

  evaluate_video_power(vaapi_mode, VIDEOS[0], stats)
  evaluate_video_power(sw_mode, VIDEOS[0], stats)
  evaluate_video_power(vaapi_mode, VIDEOS[2], stats)
  evaluate_video_power(sw_mode, VIDEOS[2], stats)
  evaluate_video_power(vaapi_mode, VIDEOS[3], stats)
  evaluate_video_power(sw_mode, VIDEOS[3], stats)
  evaluate_video_power(vaapi_mode, VIDEOS[5], stats)
  evaluate_video_power(sw_mode, VIDEOS[5], stats)

  stats.export_report()


if __name__ == '__main__':
  main()