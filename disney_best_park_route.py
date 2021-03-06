"""This module looks at The Walt Disney Company's average wait time per ride
data. With this data, we are able to say with the user choosing the park and
month they would like to visit one of the Disney parks, the best day and the
best route at what times they should go to the list of avalible rides in the
data.

One thing to make this project better is to make the global dataframes taking
into account all they years, not just 2019, and conbining them into one
dataframe with the averages of the wait times. Also another thing that could be
added is taking into consideration an opening and closing time a user might
want to visit a park such as only visiting between 09:00 and 18:00.
"""

from datetime import datetime, timedelta
import os
import numpy as np
import pandas as pd

path = os.path.dirname(__file__)


def check_input(checking, lower_limit, upper_limit):
    """Check if the inputs are valid"""

    try:
        checking = int(checking)
        if checking < lower_limit or checking > upper_limit:
            raise Exception
        return checking
    except Exception:
        print('Invalid input, try again.\n')
        return False


def mean_wait_times(date, rides):
    """Calculate and return a dict of ride names and their mean wait times"""

    ride_means = {}
    ride_keys = list(rides.keys())
    for i, df in enumerate(rides.values()):
        day_means = []
        for day in range(1, 32):
            df_day = df.loc[df['date'].str.contains(f'{date:02}/{day:02}/.*')]
            day_mean = df_day._get_numeric_data().mean()['SPOSTMIN']
            day_means.append(day_mean)
        
        ride_means.update({ride_keys[i]: day_means})
    
    return ride_means


def total_wait_times(ride_means):
    """Return a dict of the the day of the month and its total average wait
    time
    """

    first_day = True
    day_mean_totals = {}
    inital_days = True
    nan_mean = 0
    for mean_set in ride_means.values():
        for day in range(0, 31):
            if inital_days:
                if pd.isna(mean_set[day]):
                    day_mean_totals.update({day+1: mean_set[day]})
                else:
                    day_mean_totals.update({day+1: mean_set[day]})
            else:
                if pd.isna(mean_set[day]):
                    day_mean_totals.update({day+1: day_mean_totals[day+1] + mean_set[day]})
                else:
                    day_mean_totals.update(
                        {day+1: day_mean_totals[day+1] + mean_set[day]}
                    )

        inital_days = False
    
    return day_mean_totals


def report(ride_times, date, best_day, park_n):
    """Print to user the order and times of the rides of the park they chose"""

    times = sorted(list(ride_times.values()))

    print(f"""
        Park #{park_n} | Month #{date}
        The best day of the month to visit is: {best_day}
        Below is the order and times of which to visit the rides in your park...
    """)
    
    for time in times:
        for key, val in ride_times.items():
            if val == time:
                ride = ' '.join(key.split('_')[1:])
                print(f'\t{ride}: {val}')


def park_order(rides, date, best_day):
    """Determine the best route to take in a give park. For simplicity sake,
    only the 2019 years data will be accounted for when calculating
    """

    WALK_TIME = timedelta(minutes=7.5) # time to walk between rides 15min
    RIDE_LENGTH = timedelta(minutes=5.0) # time duration of a ride is 5min
    DEAD_TIME = WALK_TIME + RIDE_LENGTH
    SEARCH_DATE = f'{date:02}{best_day:02}2019'

    # get dataframes with their least times
    for key, df in rides.items():
        dataframe = df.loc[df['date'].str.contains(f'.*/{best_day:02}/2019')]
        dataframe.sort_values(by='SPOSTMIN', inplace=True)
        dataframe = dataframe.loc[dataframe['SPOSTMIN'] == dataframe.iloc[0]['SPOSTMIN']]
        rides.update({key: dataframe})
    
    # find out the ride that has the the least time variablilty
    ride_lens = {}
    for ride, df in rides.items():
        ride_lens.update({ride: len(df)})
    r_lens = sorted(list(ride_lens.values()))

    # get times to get on rides
    fist_val = True
    ride_times = {}
    j = 0
    for n in r_lens:
        for key, val in ride_lens.items():
            if val == n:
                if not fist_val:
                    init_time = list(ride_times.values())[j-1]

                    lower = rides[key].loc[
                        rides[key]['datetime'] < f'{init_time-DEAD_TIME}'
                    ]
                    upper = rides[key].loc[
                        rides[key]['datetime'] > f'{init_time+DEAD_TIME}'
                    ]
                    df_cat = pd.concat([lower, upper]).reindex()

                    time = df_cat.iloc[0]['datetime']
                    time = time.split(' ')[-1].split(':')
                    time = ''.join(time)
                    time = SEARCH_DATE + time
                    time = datetime.strptime(time, "%m%d%Y%H%M%S")

                    ride_times.update({key: time})
                else:
                    # if this is the first time going through loop, we will be here
                    for i in rides[key]['datetime']:
                        init_time = i
                        init_time = init_time.split(' ')[-1].split(':')
                        init_time = ''.join(init_time)
                        init_time = SEARCH_DATE + init_time
                        init_time = datetime.strptime(init_time, "%m%d%Y%H%M%S")
                        if fist_val:
                            ride_times.update({key: init_time})

                        break
        j += 1
        fist_val = False

    return ride_times


def main(parks):
    """Function that will decided the best route to take in a certain park on a
    certain day
    """

    # transform parks dict keys to make it eaiser to match to input
    park_keys = [1, 2, 3, 4, 5]
    parks = dict(zip(park_keys, list(parks.values())))

    while True:
        park_n = input(
            'Magic Kingdom(1) | Hollywood Studios(2) | Animal Kingdom(3) | '
            'Disneyland(4) | Epcot(5)'
            '\nWhich park would you like to visit?(1-5): '
        )
        park_n = check_input(park_n, 1, 5)
        if park_n:
            break

    while True:
        date = input(
            'Jan(1) | Feb(2) | March(3) | April(4) | May(5) | June(6) | July(7) | '
            'Aug(8) | Sep(9) | Oct(10) | Nov(11) | Dec(12)'
            f'\nWhen would you like to visit park {park_n}?(1-12): '
        )
        date = check_input(date, 1, 12)
        if date:
            break

    # create dict with key as `variable name` and values as dataframe objects
    rides = {}
    for park in parks[park_n]:
        df_temp = pd.read_csv(f'{path}/data/{park}.csv')
        rides.update(
            {f'df_{park}': df_temp.loc[df_temp['date'].str.contains(f'{date:02}/.*/.*')]}
        )

    # clean dataframes
    for dataframe in rides.values():
        dataframe.dropna(subset=['SPOSTMIN'], inplace=True)
        dataframe.drop(dataframe[dataframe['SPOSTMIN'] < 0].index, inplace=True)

    ride_means = mean_wait_times(date, rides)
    day_mean_totals = total_wait_times(ride_means)

    # get the best day to visit the park
    min_mean = np.nanmin(list(day_mean_totals.values()))
    for key, value in day_mean_totals.items(): 
        if min_mean == value: 
            best_day = key

    ride_times = park_order(rides, date, best_day)
    report(ride_times, date, best_day, park_n)


if __name__ == '__main__':
    parks = {
        'Magic Kingdom': ('7_dwarfs_train',),
        'Hollywood Studios':
            ('alien_saucers', 'rock_n_rollercoaster', 'slinky_dog', 'toy_story_mania'),
        'Animal Kingdom':
            ('dinosaur', 'expedition_everest', 'flight_of_passage', 
             'kilimanjaro_safaris', 'navi_river'),
        'Disneyland': ('pirates_of_caribbean', 'splash_mountain'),
        'Epcot': ('soarin', 'spaceship_earth')
    }

    main(parks)
