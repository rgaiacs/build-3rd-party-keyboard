#!/usr/bin/python3

"""
Script to create 3rd party keyboards for every language supported by Firefox OS
native keyboard.
"""

import os
import os.path
import time
import shutil
from subprocess import call
import argparse
import json
import fileinput
import re

def get_available_languages():
    languages_available = os.listdir(os.path.join(GAIA_PATH,
            "apps/keyboard/js/layouts"))

    return [lang.replace(".js", "") for lang in languages_available]

def build_keyboard(lang):
    call("GAIA_KEYBOARD_LAYOUTS={0} APP=keyboard make".format(lang), shell=True) 

def change_manifest(lang):
    build_full_path = os.path.join(GAIA_PATH, BUILD_PATH,
            "{0}-keyboard".format(lang))
    manifest_file_name = os.path.join(build_full_path,
        "manifest.webapp")
    with open(manifest_file_name, "r") as file_:
        manifest = json.load(file_)

    layout_name = manifest["inputs"][lang]["name"]
    if OFFICIAL_BUILD:
        description = "{0} Gaia Official Keyboard".format(layout_name)
    else:
        description = "{0} Keyboard".format(layout_name)
    name = "{0} Keyboard".format(layout_name)
    manifest["name"] = name
    manifest["description"] = description
    manifest["developer"]["name"] = DEVELOPER_NAME
    manifest["developer"]["url"] = DEVELOPER_URL
    manifest["locales"] = {"en-US": {"description": description, "name":
        name}}
    manifest["type"] = "privileged"
    manifest["permissions"]["input"]["description"] = "Required for input text"
    manifest["inputs"].pop("number")

    del manifest["permissions"]["settings"]

    # Handle icon
    if ICON_PATH and os.path.isfile(ICON_PATH):
        manifest["icons"] = {}
        appicon_dir = "icons"
        os.makedirs(os.path.join(build_full_path, appicon_dir))
        for size in [32, 60, 90, 120, 128, 256]:
            appicon_path = os.path.join(appicon_dir,
                    "keyboard-{0}.png".format(size))
            call("convert -density 512 -background none {0} {1}".format(
                ICON_PATH, os.path.join(build_full_path, appicon_path), size),
                shell=True)
            manifest["icons"][size] = '/{0}'.format(appicon_path)

    with open(manifest_file_name, "w") as file_:
        json.dump(manifest, file_, indent=2, sort_keys=True)

def build_3rd_keyboard(lang):
    try:
        shutil.rmtree(os.path.join(GAIA_PATH, BUILD_PATH, "{0}-keyboard".format(lang))) 
    except (shutil.Error, FileNotFoundError):
        pass
    shutil.copytree(os.path.join(GAIA_PATH, BUILD_PATH, "keyboard"),
            os.path.join(GAIA_PATH, BUILD_PATH, "{0}-keyboard".format(lang))) 
    change_manifest(lang)

def add_shim_for_mozSettings(lang):

    def add_shimscript(f):
        match = None
        shimadded = False
        for line in f:
            newline = line
            if not shimadded:
                match = re.match(r"(\s*)<script", line)
                if match:
                    indentation = match.group(1)
                    newline = indentation + shimscript + "\n" + line
                    shimadded = True

            print(newline, end="")

    keyboardfolder = "{0}-keyboard".format(lang)
    keyboardpath = os.path.join(GAIA_PATH, BUILD_PATH, keyboardfolder)
    shimsource = os.path.join(os.path.dirname(__file__), "shim_mozSettings.js")
    shimtarget = os.path.join(keyboardpath, "js", "vendor", "shimmozsettings")
    os.makedirs(shimtarget)
    shutil.copy(shimsource, shimtarget)

    shimscript = "<script defer type=\"text/javascript\" " +\
                 "src=\"js/vendor/shimmozsettings/shim_mozSettings.js\"></script>"


    indexpath = os.path.join(keyboardpath, "index.html")
    with fileinput.input(indexpath, inplace=True) as index:
        add_shimscript(index)

    settingspath = os.path.join(keyboardpath, "settings.html")
    with fileinput.input(settingspath, inplace=True) as settings:
        add_shimscript(settings)

if __name__ == "__main__":
    global BUILD_PATH
    global DEVELOPER_NAME
    global DEVELOPER_URL
    global GAIA_PATH
    global ICON_PATH
    global LANGUAGES
    global OFFICIAL_BUILD

    parser = argparse.ArgumentParser(description="Build 3rd party keyboard")
    parser.add_argument("--gaia", default=".", type=str, help="Path to Gaia")
    parser.add_argument("--build", default="build_stage", type=str,
            help="Path to build repository")
    parser.add_argument("-l", "--languages", default=["en"], nargs="+", type=str,
            help="List of languages to build")
    parser.add_argument("--list", action="store_true",
            help="List available languages")
    parser.add_argument("--developer-name", type=str,
            default="John Doe",
            help="Name of the developer")
    parser.add_argument("--developer-url", type=str,
            default="https://github.com/john-doe/gaia",
            help="URL of the developer page")
    parser.add_argument("--icon", default=None,
            help="Path to image to be used as icon")
    parser.add_argument("--official", action="store_true",
            help="Only to be used by Gaia team release manager")
    args = parser.parse_args()

    BUILD_PATH = args.build
    DEVELOPER_NAME = args.developer_name
    DEVELOPER_URL = args.developer_url
    GAIA_PATH = args.gaia
    ICON_PATH = args.icon
    LANGUAGES = args.languages
    OFFICIAL_BUILD = args.official

    if OFFICIAL_BUILD:
        DEVELOPER_NAME = "The Gaia Team"
        DEVELOPER_URL = "https://github.com/mozilla-b2g/gaia"

    if args.list:
        for lang in get_available_languages():
            print("- {0}".format(lang))
    else:
        for lang in LANGUAGES:
            build_keyboard(lang)
            build_3rd_keyboard(lang)
            add_shim_for_mozSettings(lang)
