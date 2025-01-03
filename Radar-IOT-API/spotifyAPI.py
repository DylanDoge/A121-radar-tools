# Copyright (c) Dylan Hoang, 2024.
# HTTP Requests in Spotify Web API.
# Requires OAUTH2.0 Access token from Spotify.
# See https://developer.spotify.com/documentation/web-api/tutorials/code-flow
# or follow my guide at section Setup 1. and 2. https://docs.google.com/document/d/1gdPdVMs15nirWZm48ST1pJ0AiLPySUujLyLp2ialMa4/

import requests

def changeVolume(access_token, volume):
    headers = {
        'Authorization': f'Bearer {access_token}',
        # 'Content-Type': 'application/json',
        # 'Content-Type': 'application/x-www-form-urlencoded',
        # 'Accept': 'application/json'
    }
    r = requests.put(f'https://api.spotify.com/v1/me/player/volume?volume_percent={volume}', headers=headers)
    return r

if __name__ == '__main__':
    changeVolume("berb", 20)