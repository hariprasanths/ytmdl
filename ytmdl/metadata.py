"""Define functions related to getting tags."""

import itunespy
import re
from ytmdl.stringutils import (
    remove_multiple_spaces, remove_punct, compute_jaccard, remove_stopwords,
    check_keywords
)
from ytmdl import defaults
from simber import Logger
from ytmdl.meta import (
    gaana, deezer, saavn, lastfm, musicbrainz, spotify,
    preconfig
)
from unidecode import unidecode

from datetime import datetime

logger = Logger('metadata')


def _logger_provider_error(exception, name):
    """Show error if providers throw an error"""
    logger.debug('{}'.format(exception))
    logger.error(
        "Something went wrong with {}. The program will continue with"
        "the other providers. Please check '{}' for more details.\
            ".format(name, logger.get_log_file()))


def get_from_itunes(SONG_NAME):
    """Try to download the metadata using itunespy."""
    # Try to get the song data from itunes
    try:
        # Get the country from the config
        country = defaults.DEFAULT.ITUNES_COUNTRY
        SONG_INFO = itunespy.search_track(SONG_NAME, country=country)
        return SONG_INFO
    except Exception as e:
        _logger_provider_error(e, 'iTunes')
        return None


def get_from_gaana(SONG_NAME):
    """Get some tags from gaana."""
    try:
        nana = gaana.searchSong(SONG_NAME)
        return nana
    except Exception as e:
        _logger_provider_error(e, 'Gaana')
        return None


def get_from_deezer(SONG_NAME):
    """Get some tags from deezer."""
    try:
        songs = deezer.searchSong(SONG_NAME)
        return songs
    except Exception as e:
        _logger_provider_error(e, 'Deezer')


def get_from_lastfm(SONG_NAME):
    """Get metadata from Last FM"""
    try:
        songs = lastfm.searchSong(SONG_NAME)
        return songs
    except Exception as e:
        _logger_provider_error(e, 'LastFM')


def get_from_saavn(SONG_NAME):
    """
    Get the songs from JioSaavn
    """
    try:
        results = saavn.search_query(SONG_NAME)
        return results
    except Exception as e:
        _logger_provider_error(e, "Saavn")
        return None


def get_from_musicbrainz(SONG_NAME):
    """Get the songs from musicbrainz"""
    try:
        results = musicbrainz.search_song(SONG_NAME)
        return results
    except Exception as e:
        _logger_provider_error(e, "MusicBrainz")
        return None


def get_from_spotify(SONG_NAME):
    """
    Get the songs from Spotify
    """
    try:
        country = defaults.DEFAULT.SPOTIFY_COUNTRY
        logger.debug(f"Using {country} for Spotify country")

        return spotify.search_song(SONG_NAME, country=country)
    except Exception as e:
        _logger_provider_error(e, "Spotify")
        return None


def lookup_from_itunes(ID):
    """Lookup metadata by id using itunespy."""
    # Try to get the song data from itunes
    try:
        # Get the country from the config
        country = defaults.DEFAULT.ITUNES_COUNTRY
        SONG_INFO = itunespy.lookup_track(int(ID), country=country)

        # Only keep track results
        SONG_INFO = [i for i in SONG_INFO if i.type == 'track']
        return SONG_INFO
    except Exception as e:
        _logger_provider_error(e, 'iTunes')
        return None


def lookup_from_spotify(id):
    """
    Lookup the track using the ID on Spotify.
    """
    try:
        country = defaults.DEFAULT.SPOTIFY_COUNTRY
        SONG_INFO = spotify.get_track_from_spotify(id=id, country=country)

        return [SONG_INFO]
    except Exception as e:
        _logger_provider_error(e, 'Spotify')
        return None


def _search_tokens(song_name, song_list, yt_title):
    """Search song in the cache based on simple each word matching."""
    song_name = remove_punct(
        remove_stopwords(
            remove_multiple_spaces(unidecode(song_name)).lower()
        ))
    ytSongNameTokens = song_name.split()
    if len(ytSongNameTokens) > 5:
        ytSongNameTokens = ytSongNameTokens[:5]
    cached_songs = song_list
    yt_title = remove_punct(
        remove_stopwords(
            remove_multiple_spaces(unidecode(yt_title)).lower()
        ))
    ytTitleTokens = yt_title.split()

    res = []
    for song in cached_songs:
        song_back = song
        providerSongName = song.track_name.lower()
        # If there is a part like (featuring ..) or any extra data
        # we should remove it as it doesn't aid the search
        providerSongName = re.sub(r'\([^)]*\)', '', providerSongName)
        providerSongName = re.sub(r'&', 'and', providerSongName)
        providerSongName = remove_stopwords(providerSongName)
        providerSongName = remove_punct(providerSongName)
        providerSongName = remove_multiple_spaces(providerSongName)
        providerSongName = unidecode(providerSongName)
        providerSongNameTokens = providerSongName.split()
        # match = check_keywords(tokens1, tokens2) or len(tokens1)/len(tokens2) >= 2
        match = True
        if match:
            dist = compute_jaccard(ytSongNameTokens, providerSongNameTokens)
            if dist >= preconfig.CONFIG().SEARCH_SENSITIVITY:
                albumDist = 0
                artistDist = 0
                weightedDist = 0
                if yt_title:
                    # Compare the yt_title (which may have artist and collection names) with the song's collection_name and artist_name as well to get more accurate matches

                    # Compute artist dist
                    artist_name = song.artist_name.lower()
                    # If there is a part like (featuring ..) or any extra data
                    # we should remove it as it doesn't aid the search
                    artist_name = re.sub(r'\([^)]*\)', '', artist_name)
                    artist_name = re.sub(r'&', 'and', artist_name)
                    artist_name = remove_stopwords(artist_name)
                    artist_name = remove_punct(artist_name)
                    artist_name = remove_multiple_spaces(artist_name)
                    artist_name = unidecode(artist_name)
                    artistNameTokens = (artist_name.split())
                    artistDist = compute_jaccard(ytTitleTokens, artistNameTokens)
                    # logger.debug(f'artist comparison stats: {round(artistDist, 3)}; - {artist_name} - {len(artistNameTokens)} - {len(ytTitleTokens)} - {ytTitleTokens} - {artistNameTokens}')

                    # Compute album dist
                    collection_name = song.collection_name.lower()
                    # If there is a part like (featuring ..) or any extra data
                    # we should remove it as it doesn't aid the search
                    collection_name = re.sub(r'\([^)]*\)', '', collection_name)
                    collection_name = re.sub(r'&', 'and', collection_name)
                    collection_name = remove_stopwords(collection_name)
                    collection_name = remove_punct(collection_name)
                    collection_name = remove_multiple_spaces(collection_name)
                    collection_name = unidecode(collection_name)
                    albumNameTokens = set(collection_name.split())
                    albumNameTokens = albumNameTokens - set(providerSongNameTokens) - set(artistNameTokens)
                    albumDist = compute_jaccard(ytTitleTokens, albumNameTokens)
                    
                    weightedDist = (albumDist * 0.65) + (artistDist * 0.3) + (dist * 0.05)
                
                res.append((song_back, dist, albumDist, artistDist, weightedDist))
    # Sort the results based on albumDist desc and artistDist desc and dist desc
    res.sort(key=lambda x: (x[4], x[2], x[3], x[1]), reverse=True)

    if len(res) > 0:
        # for the first 5 entries, pick the item with oldest release date if dist matches and wightedDist is within 30% of the first item
        first_item_weighted_dist = res[0][4] * 0.7
        for i in range(0, len(res)):
            if i < 10:
                if i == 0:
                    continue
                if (res[0][0].release_date is None or res[0][0].release_date == ""):
                    first_item_weighted_dist = res[i][4] * 0.7
                if res[i][4] < (first_item_weighted_dist):
                    break
                if (((res[i][0].release_date is not None and res[i][0].release_date != "") and (res[0][0].release_date is not None and res[0][0].release_date != ""))):
                    # convert to release_date fields to datetime and compare
                    date_format1 = "%Y-%m-%d"
                    date_format2 = "%Y-%m-%d"
                    if (len(res[0][0].release_date) == 4): date_format1 = "%Y"
                    if (len(res[0][0].release_date) == 7): date_format1 = "%Y-%m"
                    if (len(res[i][0].release_date) == 4): date_format2 = "%Y"
                    if (len(res[i][0].release_date) == 7): date_format2 = "%Y-%m"          
                    date1 = datetime.strptime(res[0][0].release_date.split('T')[0], date_format1)
                    date2 = datetime.strptime(res[i][0].release_date.split('T')[0], date_format2)
                    if date1 > date2:
                        res[0], res[i] = res[i], res[0]
                elif (res[0][0].release_date is None or res[0][0].release_date == ""):
                    res[0], res[i] = res[i], res[0]

    # Return w/o the dist values
    for i in range(0, len(res)):
        if i < 20:
            logger.debug(f"title comparison stats: {round(res[i][1], 3)} - {round(res[i][2], 3)} - {round(res[i][3], 3)} - {round(res[i][4], 4)}; -- ;{res[i][0].track_name}; {res[i][0].collection_name}; {res[i][0].artist_name}; {res[i][0].release_date};")

        # skip first item if release date is not present
        if (res[i][0].release_date is None or res[i][0].release_date == '') and i == 0:
            continue

        res[i] = res[i][0]
        res[i].release_date = res[i].release_date.split('T')[0]

    return res


def filterSongs(data, filters=[]):
    """Filter the songs according to the passed filters.

    In the passed filters the first element is artist.
    The second element is album."""

    # In some cases the data can be None, then just return
    if data is None:
        return data

    new_tuple = []
    rest = []

    for songData in data:
        artistMatch = True
        albumMatch = True

        if filters[0] is not None:
            artistMatch = (songData.artist_name == filters[0])
        if filters[1] is not None:
            albumMatch = (songData.collection_name == filters[1])

        if artistMatch and albumMatch:
            new_tuple.append(songData)
        else:
            rest.append(songData)
    return (new_tuple + rest)


def _extend_to_be_sorted_and_rest(provider_data, to_be_sorted, rest, filters):
    """Create the to be sorted and rest lists"""
    # Before passing for sorting filter the songs
    # with the passed args
    if filters:
        provider_data = filterSongs(provider_data, filters)
    if provider_data is not None:
        to_be_sorted.extend(provider_data)
        rest.extend(provider_data)


def SEARCH_SONG(search_by="Tera Buzz", song_name="Tera Buzz", filters=[], disable_sort=False, yt_title=""):
    """Do the task by calling other functions."""
    to_be_sorted = []
    rest = []

    metadata_providers = defaults.DEFAULT.METADATA_PROVIDERS

    GET_METADATA_ACTIONS = {
        'itunes': get_from_itunes,
        'gaana': get_from_gaana,
        'deezer': get_from_deezer,
        'saavn': get_from_saavn,
        'lastfm': get_from_lastfm,
        'musicbrainz': get_from_musicbrainz,
        'spotify': get_from_spotify
    }

    broken_provider_counter = 0

    search_by_query_names_array = []
    search_by_query_names_array.append(search_by)
    search_by_song_name_tokens = search_by.split()
    # logger.debug(f'query - {search_by}; tokens - {search_by_song_name_tokens}; ')
    if len(search_by_song_name_tokens) > 3:
        if len(search_by_song_name_tokens) > 5:
            search_by_first_5_words = ' '.join(search_by_song_name_tokens[:5])
            search_by_query_names_array.append(search_by_first_5_words)
        search_by_first_3_words = ' '.join(search_by_song_name_tokens[:3])
        search_by_query_names_array.append(search_by_first_3_words)
        search_by_first_2_words = ' '.join(search_by_song_name_tokens[:2])
        search_by_query_names_array.append(search_by_first_2_words)
        search_by_first_1_words = ' '.join(search_by_song_name_tokens[:1])
        search_by_query_names_array.append(search_by_first_1_words)
        search_by_3_and_4_word = ' '.join(search_by_song_name_tokens[2:4])
        search_by_query_names_array.append(search_by_3_and_4_word)
        # logger.debug(f'query - {search_by}; tokens - {search_by_song_name_tokens}; {search_by_first_5_words}; {search_by_first_3_words}; {search_by_first_2_words}; {search_by_first_1_words}')
    
    if yt_title != search_by:
        search_by_song_name_tokens = yt_title.split()
        if len(search_by_song_name_tokens) > 3:
            if len(search_by_song_name_tokens) > 5:
                search_by_first_5_words = ' '.join(search_by_song_name_tokens[:5])
                search_by_query_names_array.append(search_by_first_5_words)
            search_by_first_3_words = ' '.join(search_by_song_name_tokens[:3])
            search_by_query_names_array.append(search_by_first_3_words)
            search_by_first_2_words = ' '.join(search_by_song_name_tokens[:2])
            search_by_query_names_array.append(search_by_first_2_words)
            search_by_first_1_words = ' '.join(search_by_song_name_tokens[:1])
            search_by_query_names_array.append(search_by_first_1_words)
            search_by_3_and_4_word = ' '.join(search_by_song_name_tokens[2:4])
            search_by_query_names_array.append(search_by_3_and_4_word)
            # logger.debug(f'yt_title - {yt_title}; tokens - {search_by_song_name_tokens}; {search_by_first_5_words}; {search_by_first_3_words}; {search_by_first_2_words}; {search_by_first_1_words}')
    # logger.debug(f'array - {search_by_query_names_array}')
    search_by_query_names_array = set(search_by_query_names_array)
    # logger.debug(f'array - {search_by_query_names_array}')

    for search_by_query in search_by_query_names_array:
        for provider in metadata_providers:
            if provider in GET_METADATA_ACTIONS:
                logger.debug(f"Searching metadata with '{provider}' with query '{search_by_query}'")
                data_provider = GET_METADATA_ACTIONS.get(
                    provider, lambda _: None)(search_by_query)
                
                if data_provider:
                    _extend_to_be_sorted_and_rest(
                        data_provider, to_be_sorted, rest, filters)
                    logger.debug(f'result for {provider} having length {len(data_provider)}')
            else:
                logger.warning(
                    '"{}" isn\'t implemented. Skipping!'.format(provider)
                )
                broken_provider_counter += 1

    # remove duplicates from to_be_sorted list by comparing the hash of the objects
    to_be_sorted_hash = set()
    to_be_sorted_unique = []
    for item in to_be_sorted:
        # logger.debug(f'item - {item.track_name} - {item.artist_name} - {item.collection_name} - {item.release_date} - {item.hash()}')
        if item.hash() not in to_be_sorted_hash:
            to_be_sorted_hash.add(item.hash())
            to_be_sorted_unique.append(item)
    to_be_sorted = to_be_sorted_unique
    
    # to_be_sorted will be empty and it will return None anyway, no need
    # to do it here as well
    if broken_provider_counter == len(metadata_providers):
        logger.critical("{}".format(
            'No metadata provider in the configuration is '
            'implemented. Please change it to something \
                            available or use the --skip-meta flag'))
    
    logger.debug(f'to_be_sorted - {len(to_be_sorted)}, disable_sort - {disable_sort} - yt_title - {yt_title}')

    if not to_be_sorted:
        return None

    # If sorting is disabled, return as is
    if disable_sort:
        return to_be_sorted

    # Send the data to get sorted
    sorted_data = _search_tokens(song_name, to_be_sorted, yt_title)

    # Add the unsorted data
    # sorted_data += rest

    return sorted_data


if __name__ == '__main__':
    n = SEARCH_SONG("Cradles", "Cradles", ["Sub Urban", None])

    for i in n:
        print(i.track_name + ' by ' + i.artist_name + ' of ' + i.collection_name)
