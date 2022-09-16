import twitter #Make sure to pip3 install python-twitter for this. Not just install twitter!
import requests
import time
from skyfield.api import load, EarthSatellite
import math


#This block changes directory to allow paths relative to this script, even when executing this script from elsewhere (such as cron)
import os
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

#Loads credentials for a Twitter account from an external file
def load_creds(filename):
    cred_dict = {}
    with open(filename) as f:
        cred_lines = f.read().splitlines()
        for line in cred_lines:
            key,value = line.split(":")
            cred_dict[key] = value
    return cred_dict

#Initialize Skyfield timescale.
ts = load.timescale()
#Reads in an Epoch from TLE and converts to a Time object compatible with Skyfield
def epoch_to_sf_time(tle_in):
    epoch = get_epoch(tle_in)
    year = int("20" + epoch[:2])
    day_of_year = float(epoch[2:])
    sfdate = ts.utc(year,1,day_of_year)
    return sfdate
#Converts Mean Motion from a TLE to a Semimajor axis
def MM_TO_SMA(mean_motion):

    orbital_period = 86400 / mean_motion
    mu = 398600441800000

    orb_period_frac = (mu*orbital_period**2)/(4*math.pi**2)
    semimajor_axis = orb_period_frac**(1/3)

    return semimajor_axis/1000 #convert from m to km
#Pulls out the epoch string from a TLE
def get_epoch(tle_in):
    return tle_in[0][18:32]
#Retrives the newest ISS TLE from Celestrak
def get_iss_tle():
    session = requests.session()
    url = "https://www.celestrak.com/NORAD/elements/gp.php?CATNR=25544"
    page = session.get(url)
    sat_tle = page.text[:-2].split("\r\n")[1:]
    #Save to a file so we can load it next time as the previous
    with open("25544.tle","w") as f:
        f.write("\n".join(sat_tle))
    return sat_tle

#Load in user's twitter credentials. Create a tweeter object that we can use to send tweets.
creds=load_creds('twitter_creds')
tweeter = twitter.Api(consumer_key = creds['consumer_key'],
                            consumer_secret = creds['consumer_secret'],
                            access_token_key = creds['access_token_key'],
                            access_token_secret = creds['access_token_secret'])

#Main execution sequence. First load in what we've logged as the prior newest-known TLE.
with open("25544.tle") as f:
    previous_tle = f.read().splitlines()
#Now, get the newest TLE (and overwrite the file we just pulled from)
new_web_tle = get_iss_tle()

#Start the log with a timestamp. Then show what TLE's we're pulling from.
print(f"\n{time.strftime('%d %b %Y %H:%M:%S',time.gmtime())}")

if previous_tle == new_web_tle:
    print(f"\nFiles match. Exiting.")
else:
    print(f"\nChange Detected!")
    print(f"\nPrevious TLE: {previous_tle}")
    print(f"\nUpdated  TLE: {new_web_tle}")
    time_diff = float(get_epoch(new_web_tle))- float(get_epoch(previous_tle)) 
    print(f"\nElapsed time: {time_diff} days")
    prev_sat = EarthSatellite(*previous_tle)
    now_sat = EarthSatellite(*new_web_tle)
    tle_time = epoch_to_sf_time(new_web_tle)
    prev_pos = prev_sat.at(tle_time)
    now_pos = now_sat.at(tle_time)
    dist = (now_pos - prev_pos).position.length().km
    print(f"\nDistance deviation: {dist} km")
    #mean motion difference
    prev_MM = float(previous_tle[1][52:63])
    now_MM = float(new_web_tle[1][52:63])
    print(f"\nMean Motion change: {(now_MM-prev_MM):.8}")
    SMA_change = MM_TO_SMA(now_MM) - MM_TO_SMA(prev_MM)
    print(f"\nSemimajor axis changed by {SMA_change} km")
    tweetstring = f'Potential ISS maneuver detected! Latest TLE position is {dist:.2f} km from where previous TLE predicted!\nSemi-Major Axis changed by {SMA_change:.2f} km'
    #Have a cooldown period, we won't tweet again for 24 hours.
    if dist > 5 and not os.path.exists('cooldown'):
        with open('cooldown','w') as cooldownfile:
            cooldownfile.write("\n".join(previous_tle))
        print("\nGoing to tweet")
    
        status = tweeter.PostUpdate(tweetstring)
    #After 24 hours, resolve the cooldown.
    if os.path.exists('cooldown'):
        print("Cooldown exists")
        cooldown_age = time.time() - os.stat('cooldown').st_mtime
        if cooldown_age > 86400:
            with open('cooldown') as pre_burn_file:
                pre_burn_tle = pre_burn_file.readlines()
                pre_burn_SMA = MM_TO_SMA(float(pre_burn_tle[1][52:63]))
                post_cooldown_SMA_change = MM_TO_SMA(now_MM) - pre_burn_SMA
                print(post_cooldown_SMA_change)
                tweeter.PostUpdate(f"It has now been 24 hours since the burn. Now that TLE's have settled, it appears the orbit changed by {post_cooldown_SMA_change:.2f} km.")
            print("deleting cooldown")
            os.remove('cooldown')
            print("Does cooldown still exist?" + str(os.path.exists('cooldown')))
print("\n")