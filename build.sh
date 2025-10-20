#!/usr/bin/env bash
# Backend build script for Render

set -o errexit

pip install --upgrade pip
pip install -r requirements.txt
