#! /usr/bin/python3
from env.env import env
import vlc
import time
import pymongo


# Initialize mongo
client = pymongo.MongoClient(f"mongodb://{env['mongodb_ip']}:{env['mongodb_port']}/")
db = client[env['database']]

def play():

    state = "Stopped"
    p = ''
    url = ''
    station = ''

    restart_timer = 0
    restart_after = 4320 # x5sec = 6 hours

    while True:
        
        restart_timer += 1

        # Get info from local DB
        info = db['fm_live'].find(sort=[("changed", pymongo.DESCENDING)])
        info = info[0]
        current_url = info['url']

        if current_url != url:
            url = current_url
            station = info['station']
            state = 'URL Changed'
            print("URL Changed")
        
        if restart_timer > restart_after:
            restart_timer = 0
            state = "Restart Timer"
            print("Reached restart time")


        timestamp = f"{time.strftime('%d/%m/%Y %X')}"
        unix = time.time()

        if state != "Playing":
            try:
                p.stop()
            except:
                pass
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
                        'changed' : info['changed'],
                    },
                    {
                        '$set': {
                            'station' : station,
                            'url' : url,
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
                'changed' : info['changed'],
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


if __name__ == "__main__":

    play()