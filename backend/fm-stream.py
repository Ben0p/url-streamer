#! /usr/bin/python3
from env.env import env
import vlc
import time
import pymongo


# Initialize mongo
client = pymongo.MongoClient(f"mongodb://{env['mongodb_ip']}:{env['mongodb_port']}/")
db = client[env['database']]

def play(station, url):

    state = "Stopped"

    while True:

        timestamp = f"{time.strftime('%d/%m/%Y %X')}"
        unix = time.time()

        if state != "Playing":
            try:
                inst = vlc.Instance() # Create a VLC instance
                p = inst.media_player_new() # Create a player instance
                media = inst.media_new(url) # Create media instance
                media.get_mrl() # Get media
                p.set_media(media) # Select Media
                p.play() # Play Media
                media.parse() # Parse media information
                time.sleep(10)

                db['fm_live'].find_one_and_update(
                    {
                        'station' : station,
                    },
                    {
                        '$set': {
                            'station' : station,
                        },
                        '$inc' : {
                            'restarts' : 1
                        }
                    },
                    upsert=True
                )
                print("Restarted stream.")

            except:
                # If any form of exception
                state = "Retrying"
                pass

        artist = ''
        song = ''
        state = str(media.get_state()).split('.')[1]

        try:
            track = media.get_meta(0)
            artist, song = track.split("-")
            artist = artist.strip()
            song = song.strip()
        except ValueError:
            pass
        except AttributeError:
            pass

        db['fm_live'].find_one_and_update(
            {
                'station' : station,
            },
            {
                '$set': {
                    'station' : station,
                    'time': timestamp,
                    'unix' : unix,
                    'artist': artist,
                    'song' : song,
                    'state' : state
                }
            },
            upsert=True
        )

        print(f"{timestamp} - {artist} - {song}")



        time.sleep(5)

def getStation():

    info = db['fm_live'].find()
    station = info[0]['station']
    url = info[0]['url']

    return(station, url)

if __name__ == "__main__":

    station, url = getStation()

    play(station, url)