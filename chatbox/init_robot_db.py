"""
$ ./manage.py shell < chatbox/init_robot_db.py
"""

import os
import json
from chatbox.models import DeviceStatus
import pyaudio


def init_dev_status_db():
    # os
    os_note = os.uname()
    DeviceStatus.objects.update_or_create(name="os", defaults={"note": os_note})

    # Audio devices detailed information
    p = pyaudio.PyAudio()
    device_count = p.get_device_count()

    # Microphone information
    for i in range(device_count):
        device_info = p.get_device_info_by_index(i)
        if device_info.get("maxInputChannels") > 0:
            mic_info = {
                "index": i,
                "name": device_info.get("name"),
                "defaultSampleRate": device_info.get("defaultSampleRate"),
                "maxInputChannels": device_info.get("maxInputChannels"),
                "hostApi": p.get_host_api_info_by_index(device_info.get("hostApi")).get(
                    "name"
                ),
            }
            mic_note = json.dumps(mic_info)
            DeviceStatus.objects.update_or_create(
                name="mic" + str(i), defaults={"note": mic_note}
            )

    # Speaker information
    for i in range(device_count):
        device_info = p.get_device_info_by_index(i)
        if device_info.get("maxOutputChannels") > 0:
            spk_info = {
                "index": i,
                "name": device_info.get("name"),
                "defaultSampleRate": device_info.get("defaultSampleRate"),
                "maxOutputChannels": device_info.get("maxOutputChannels"),
                "hostApi": p.get_host_api_info_by_index(device_info.get("hostApi")).get(
                    "name"
                ),
            }
            spk_note = json.dumps(spk_info)
            DeviceStatus.objects.update_or_create(
                name="spk", defaults={"note": spk_note}
            )

    # Clean up
    p.terminate()


init_dev_status_db()
print("Initialization of robot database is done!")
