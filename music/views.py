from django.shortcuts import render, redirect
from django.contrib import messages

from django.contrib.auth.models import User,auth
from django.contrib.auth.decorators import login_required
from bs4 import BeautifulSoup as bs
import re

import requests
rapid_key = '3bbb778222mshba9b17ded18d774p11d14djsnc86335283e40'
def top_artists():
    url = "https://spotify-scraper.p.rapidapi.com/v1/home"

    headers = {
        "x-rapidapi-key": rapid_key,
        "x-rapidapi-host": "spotify-scraper.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)

    print(response.json())
    response_data = response.json()
    # print(response.json())
    artist_info = []
    if 'sections' in response_data:
        for artist in response_data['sections'].get('items')[0].get('contents').get('items'):
            name = artist.get('name', 'No name')
            artist_id = artist.get('id', 'No id')
            avatar_url  = artist.get('visuals', {}).get('avatar',[{}])[0].get('url', 'No url')
            artist_info.append((name,avatar_url,artist_id))
    # print(artist_info)
    return artist_info

def top_tracks():
    url = "https://spotify-scraper.p.rapidapi.com/v1/home"

    headers = {
        "x-rapidapi-key": rapid_key,
        "x-rapidapi-host": "spotify-scraper.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)
    response_data = response.json()
    # print(response.json())
    track_details = []
    if 'sections' in response_data:
        for artist in response_data['sections'].get('items')[1].get('contents').get('items'):
            track_id = artist.get('id', 'No id')
            track_name = artist.get('name', 'No name')
            artist_name = artist.get('artists', [{}])[0].get('name','No name')
            cover_url = artist.get('cover', [{}])[0].get('url','No url')
            track_details.append({
                'id' : track_id,
                'name' : track_name,
                'artist' : artist_name,
                'cover_url' : cover_url
            })
    else:
        print('there is no data available')
    # print(artist_info)
    return track_details
# Create your views here.

# def get_track_image(track_id,   track_name):
    url = "https://open.spotify.com/track/"+track_id
    r = requests.get(url)
    soup = bs(r.content)
    image_links_html = soup.find('img', {'alt': track_name})
    if image_links_html:
        image_links = image_links_html("srcset")
    else:
        image_links = ""
        
    match = re.search(r'https:\/\/i\.scdn\.co\/image\/[a-zA-Z0-9]+ 640w', image_links)
    
    if match:
        url_640w = match.group().rstrip(' 640w')
    else:
        url_640w = ''

    return url_640w

def profile(request,pk):
    artist_id = pk
    import requests

    url = "https://spotify-scraper.p.rapidapi.com/v1/artist/overview"

    querystring = {"artistId":artist_id}

    headers = {
    	"x-rapidapi-key": rapid_key,
    	"x-rapidapi-host": "spotify-scraper.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code == 200:
        data = response.json()
        
        name = data['name']
        monthly_listeners = data['stats']['monthlyListeners']
        header_url = data["visuals"]["header"][0]["url"]
        
        top_tracks = []
        
        for track in data["discography"]["topTracks"]:
            # trackid = track["id"]
            # trackname = track["name"] 
            # if get_track_image(trackid,trackname):
                # trackimage = get_track_image(trackid,trackname)
            # else:
                # trackimage = ""
            # trackimage = track["album"]["cover"][0]["url"]
            
            track_info = {
                "id" : track["id"],
                "name" : track["name"],
                "durationText" : track["durationText"],
                "playCount" : track["playCount"],
                "track_image" : track["album"]["cover"][0]["url"]
                 
            }
            top_tracks.append(track_info)
        
        
        artist_data = {
            "name":name,
            "monthlyListeners": monthly_listeners,
            "headerUrl" : header_url,
            "topTracks" : top_tracks
        }
    else:
        artist_data = {}
    return render(request,'profile.html',artist_data)

@login_required(login_url='login')
def index(request):
    artist_info = top_artists()
    tracks_info = top_tracks()
    context = {
        'artists_info' : artist_info,
        'first_six_tracks' : tracks_info
    }
    return render(request,'index.html', context)

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username = username, password = password)
        if user is None:
            messages.info(request, 'Invalid Credentials')
            return render(request, 'login.html')
        else:
            auth.login(request,user)
            return redirect('/')
    else:    
        return render(request,'login.html')

def search(request):
    if request.method == "POST":
        search_query = request.POST['search_query']
        
        url = "https://spotify-scraper.p.rapidapi.com/v1/search"

        querystring = {"term":search_query,"type":"track"}

        headers = {
            "x-rapidapi-key": rapid_key,
            "x-rapidapi-host": "spotify-scraper.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring)

        track_list = []
        
        if response.status_code == 200:
            data = response.json()
            
            seacrh_results_count = data["tracks"]["totalCount"]
            tracks = data["tracks"]["items"]
            
            for track in tracks:
                track_name = track["name"]
                artist_name = track["artists"][0]["name"]
                duration = track["durationText"]
                trackid = track["id"]
                track_image = track["album"]["cover"][2]["url"]
                
                track_list.append({
                    "track_name" : track_name,
                    "artist_name" : artist_name,
                    "duration" : duration,
                    "trackid" : trackid,
                    "track_image" : track_image 
                })
        context = {
            "search_results_count" : seacrh_results_count,
            "track_list" : track_list,
        }
        return render(request,"search.html",context)
    else:
        return render(request,"search.html")

def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']
        
        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email already taken by another user')
                return render(request, 'signup.html')  # Return to signup page with message
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username already taken by another user')
                return render(request, 'signup.html')  # Return to signup page with message
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()

                # Authenticate and log in the user
                user_login = auth.authenticate(username=username, password=password)
                if user_login is not None:
                    auth.login(request, user_login)
                    return redirect('index')  # Redirect to the homepage after successful login
                else:
                    messages.error(request, 'Authentication failed, please try logging in manually.')
                    return redirect('login')  # Redirect to login page in case of authentication failure
        else:
            messages.info(request, 'Passwords do not match!')
            return render(request, 'signup.html')  # Return to signup page with message
    else:   
        return render(request, 'signup.html')  # Render the signup form if request method is GET

@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    return redirect('login')



def get_audio_details(query):
    url = "https://spotify-scraper.p.rapidapi.com/v1/track/download"

    querystring = {"track":query}

    headers = {
        "x-rapidapi-key": rapid_key,
        "x-rapidapi-host": "spotify-scraper.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    audio_details = []
    if response.status_code == 200:
        response_data = response.json()
        if 'youtubeVideo' in response_data and 'audio' in response_data['youtubeVideo']:
            audio_list = response_data['youtubeVideo']['audio']
            if audio_list:
                first_audio_url = audio_list[0]['url']
                duration_text = audio_list[0]['durationText']

                audio_details.append(first_audio_url)
                audio_details.append(duration_text)
            else:
                print('No audio data available')
        else:
            print('No audio key found')
    else:
        print('Failed to fetch data')
    return audio_details

def song(request,pk):
    track_id = pk
    url = "https://spotify-scraper.p.rapidapi.com/v1/track/metadata"

    querystring = {"trackId":track_id}

    headers = {
        "x-rapidapi-key": rapid_key,
        "x-rapidapi-host": "spotify-scraper.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code == 200:
        data = response.json()
        track_name = data.get('name')
        artist_list = data.get('artists',[])
        track_image = artist_list[0].get('visuals').get('avatar')[0].get('url')
        first_artist_name = artist_list[0].get('name') if artist_list else 'no artists found'
        
        audio_details_query = track_name+first_artist_name
        audio_details = get_audio_details(audio_details_query)
        audio_url = audio_details[0]
        duration_text = audio_details[1]
        context = {
            'track_name' : track_name,
            'artist_name' : first_artist_name,
            'track_image' : track_image,
            'audio_url' : audio_url,
            'duration_text' : duration_text
        }
    # print(response.json())
    # print(context)
    return render(request,'music.html',context)


def music(request,pk):
    track_id = pk

    url = "https://spotify-scraper.p.rapidapi.com/v1/album/metadata"

    querystring = {"albumId": track_id}
    
    headers = {
        "x-rapidapi-key": rapid_key,
        "x-rapidapi-host": "spotify-scraper.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code == 200:
        data = response.json()
        track_name = data.get('name')
        artist_list = data.get('artists',[])
        track_image = artist_list[0].get('visuals').get('avatar')[0].get('url')
        first_artist_name = artist_list[0].get('name') if artist_list else 'no artists found'
        
        audio_details_query = track_name+first_artist_name
        audio_details = get_audio_details(audio_details_query)
        audio_url = audio_details[0]
        duration_text = audio_details[1]
        context = {
            'track_name' : track_name,
            'artist_name' : first_artist_name,
            'track_image' : track_image,
            'audio_url' : audio_url,
            'duration_text' : duration_text
        }
    # print(response.json())
    # print(context)
    return render(request,'music.html',context)