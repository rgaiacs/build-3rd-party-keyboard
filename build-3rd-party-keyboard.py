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

def get_available_languages():
    languages_available = os.listdir(os.path.join(GAIA_PATH,
            "apps/keyboard/js/layouts"))

    return [lang.replace(".js", "") for lang in languages_available]

def build_keyboard(lang):
    call("GAIA_KEYBOARD_LAYOUTS={0} APP=keyboard make".format(lang), shell=True) 

def change_manifest(lang):
    manifest_file_name = os.path.join(GAIA_PATH, BUILD_PATH,
        "{0}-keyboard".format(lang), "manifest.webapp")
    with open(manifest_file_name, 'r') as file_:
        manifest = json.load(file_)

    layout_name = manifest['inputs'][lang]['name']
    description = '{0} Gaia Official Keyboard'.format(layout_name)
    manifest['description'] = description
    manifest['locales'] = {'en-US': {'description': description, 'name':
        description}}
    manifest['type'] = "privileged"
    manifest['inputs'].pop("number")

    with open(manifest_file_name, 'w') as file_:
        json.dump(manifest, file_)

def build_3rd_keyboard(lang):
    try:
        shutil.rmtree(os.path.join(GAIA_PATH, BUILD_PATH, "{0}-keyboard".format(lang))) 
    except (shutil.Error, FileNotFoundError):
        pass
    shutil.copytree(os.path.join(GAIA_PATH, BUILD_PATH, "keyboard"),
            os.path.join(GAIA_PATH, BUILD_PATH, "{0}-keyboard".format(lang))) 
    change_manifest(lang)

if __name__ == "__main__":
    global GAIA_PATH
    global BUILD_PATH
    global LANGUAGES

    parser = argparse.ArgumentParser(description="Build 3rd party keyboard")
    parser.add_argument("--gaia", default='.', type=str, help="Path to Gaia")
    parser.add_argument("--build", default='build_stage', type=str, help="Path to build repository")
    parser.add_argument("-l", "--languages", default=['en'], nargs='+', type=str,
            help="List of languages to build")
    parser.add_argument("--list", action="store_true", help="List available languages")
    args = parser.parse_args()

    GAIA_PATH = args.gaia
    BUILD_PATH = args.build
    LANGUAGES = args.languages

    if args.list:
        for lang in get_available_languages():
            print("- {0}".format(lang))
    else:
        for lang in LANGUAGES:
            build_keyboard(lang)
            build_3rd_keyboard(lang)
