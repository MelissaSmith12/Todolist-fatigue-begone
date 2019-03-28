import trello
from trello import TrelloApi
import pprint
import re
import random
import os.path
import csv
import datetime
import keyring
import json
import requests

# trello docs: https://pythonhosted.org/trello/trello.html


def get_credentials():
    # try to open file with user info, if not available, prompt user
    filename = "credentials.csv"
    if os.path.isfile(filename):
        credentials = {}
        with open(filename, "r") as f:
            lines = f.readlines()
            for line in lines:
                key_data = line.split(',')
                credentials[key_data[0]] = re.search('[^\n]*',
                                                     key_data[1]).group()
        username = credentials['username']
        token = credentials['token']
        trello_username = credentials['trello_username']
    else:
        username = input('Please enter your name: ')
        trello_username = input('Please enter your trello username: ')
        token = input('Please enter your API token: ')
        with open(filename, "w") as f:
            line = "username,"+username + '\n'
            f.write(line)
            line = "token,"+token + '\n'
            f.write(line)
            line = "trello_username,"+trello_username + '\n'
            f.write(line)
    return username, token, trello_username


def prompt_for_task():
    location = input('Are you at Home, Work, or Out? ')
    location = location.capitalize()
    while location not in ['Home', 'Work', 'Out']:
        print("\nI'm sorry. I didn't understand your answer.")
        location = input('Are you at Home, Work, or Out? ')
    time = input('What size task do you have time for (xs, s, m, l, xl, any)?')
    time = time.lower()
    while time not in ['xs', 's', 'm', 'l', 'xl', 'any']:
        print("\nI'm sorry. I didn't understand your answer.")
        time = input('What size task do you have time for (xs, s, m, l, xl, '
                     'any)? ')
    energy = input('Do you have Mental, Physical, Creative, or Social energy?')
    energy = energy.capitalize()
    while energy not in ['Social', 'Mental', 'Physical', 'Creative']:
        print("I'm sorry. I didn't understand your answer.")
        energy = input('Do you have Mental, Physical, Creative, or Social '
                       'energy?')
    return location, time, energy


def load_stats(name):
    filename = "stats.csv"
    if os.path.isfile(filename):
        stats = {}
        with open(filename, "r") as f:
            lines = f.readlines()
            for line in lines:
                key_data = line.split(',')
                stats[key_data[0]] = int(key_data[1])
        total_tasks = stats['total']
    else:
        with open(filename, "w") as f:
            line = "total,0"
            f.write(line)
            total_tasks = 0
    print("Congratulations, " + name + ". You've completed " +
          str(total_tasks) + " tasks since you started using this app.")
    return total_tasks


def make_active_done(active_card, name, total_tasks, daily_tasks, start_time,
                     list_dict, trello):
    messages = {
                1: "Way to go, ass kicker!",
                2: "You slayed that task, " + name + "!",
                3: name + ", truly you are mighty and wise.",
                4: "Behold! It is " + name + ", Slayer of Tasks. Mightiest of "
                   "To-Doers.",
                5: "What? You're done already?"
                }
    recurring = False
    active_labels = active_card['labels']
    for label in active_labels:
        if label['name'] == 'Recurring':
            recurring = True
    if recurring is True:
        recurring_name = active_card['name']
        recurring_description = active_card['desc']
        new_card = trello.cards.new(recurring_name, list_dict['To Do'],
                                    desc=recurring_description)
        for label in active_labels:
            trello.cards.new_label(new_card['id'], label['color'])
    trello.cards.update(active_card['id'], idList=list_dict['Done'])
    end_time = datetime.datetime.now()
    message_number = random.randint(1, len(messages))
    print(message[message_number])
    total_tasks, daily_tasks = increase_stats(total_tasks, daily_tasks)
    print("")
    print("That task took " + str(end_time - start_time) + " minutes to "
          "complete.")
    return total_tasks, daily_tasks


def increase_stats(total_tasks, daily_tasks):
    daily_tasks += 1
    total_tasks += 1
    filename = "stats.csv"
    with open(filename, "w") as f:
            line = "total," + str(total_tasks)
            f.write(line)
    if daily_tasks == 1:
        print("You've completed " + str(daily_tasks) + " task so far today "
              "and " + str(total_tasks) + " total tasks since you started "
              "using this app.")
    else:
        print("You've completed " + str(daily_tasks) + " tasks so far today "
              "and " + str(total_tasks) + " total tasks since you started "
              "using this app.")
    return total_tasks, daily_tasks


def storeListIDs(boards, board_id, trello):
    trello_lists = trello.boards.get_list(board_id)
    list_dict = {}
    for list in trello_lists:
        list_dict[list['name']] = list['id']
    return list_dict, trello_lists


def store_boards(trello_username, trello):
    boards = trello.members.get_board(trello_username)
    my_boards = []
    for board in boards:
        board_dict = {}
        board_dict[board['name']] = board['id']
        my_boards.append(board_dict)
    return my_boards


def pick_new_board(my_boards, pick_type):
    # Adjust to pick from all boards or from recent boards
    board_select = False
    print(my_boards)
    if pick_type == 'All':
        print("Below, you'll see a list of all the Trello boards you "
              "currently have access to. At the prompt, please type the "
              "number that is next to the board you would like to use "
              "for tasks.")

    else:
        print("Below, you'll see a list of the Trello boards you've recently "
              "used in this application. At the prompt, please type the number"
              " that is next to the board you would like to use for tasks.")

    i = 0
    while i < len(my_boards):
        for key, item in my_boards[i].items():
            print(str(i + 1) + ": " + key)
            i += 1
    while board_select is False:
            try:
                board_menu_pick = int(input("Please enter the board number: "))
                if board_menu_pick > len(my_boards):
                    print("I'm sorry, your entry either wasn't a number or"
                          "didn't match a board. ")
                else:
                    board_select = True
            except:
                print("I'm sorry, your entry either wasn't a number or didn't "
                      "match a board. ")
    my_board_dict = my_boards[board_menu_pick - 1]
    print(my_board_dict)
    my_board_name = list(my_board_dict.keys())[0]
    print(my_board_name)
    my_board_id = my_board_dict[my_board_name]
    print(my_board_id)
    print("")
    confirm = input("The board you picked is: " + my_board_name + ". Is this "
                    "the correct board? (y/n) ")
    if confirm == 'n':
        pick_new_board(my_boards, pick_type)
    else:
        return my_board_id, my_board_name


def save_current_board(board_id, board_name):
    filename = "most_recent_board.csv"
    with open(filename, "w") as f:
            line = "board_id,"+board_id + '\n'
            f.write(line)
            line = "board_name," + board_name + '\n'
            f.write(line)


def board_prompt(my_boards):
    board_id, board_name = get_last_board()
    if board_id is not None:
        print("Your most recent board was " + board_name + ".")
        selection = input("Would you like to: \n(1) pull tasks from your "
                          "current Trello board, \n(2) switch to one of the "
                          "Trello boards you've recently used in this app and "
                          "get tasks from it, or \n(3) select a board from "
                          "your entire list of trello boards and get tasks "
                          "from it? \nEnter 1, 2, 3, or Quit: ")
        if selection == '1':
            board_id = board_id
            board_name = board_name
        elif selection == '2':
            recent_boards = get_recent_boards()
            board_id, board_name = pick_new_board(recent_boards, 'Recent')
        else:
            board_id, board_name = pick_new_board(my_boards, 'All')
    else:
        board_id, board_name = pick_new_board(my_boards, 'All')
    return board_id, board_name


def get_last_board():
    filename = "most_recent_board.csv"
    if os.path.isfile(filename):
        board_details = {}
        with open(filename, "r") as f:
            lines = f.readlines()
            for line in lines:
                key_data = line.split(',')
                board_details[key_data[0]] = re.search('[^\n]*',
                                                       key_data[1]).group()
        board_id = board_details['board_id']
        board_name = board_details['board_name']
    else:
        print("You need to set which board to use.")
        board_id = None
        board_name = None
    return board_id, board_name


def get_recent_boards():
    filename = "all_recent_boards.csv"
    recent_boards = []
    if os.path.isfile(filename):
        with open(filename, "r") as f:
            reader = csv.DictReader(f)
            for line in reader:
                board_details = {line['board_name']: line['board_id']}
                recent_boards.append(board_details)
        print(recent_boards)
        return recent_boards
    else:
        print("You have no recent boards.")


def add_recent_board(board_id, board_name):
    filename = "all_recent_boards.csv"
    # first check to see if board is already in file
    with open(filename, "r+") as f:
        reader = csv.DictReader(f)
        found_board = False
        for line in reader:
            if board_id in line:
                newline = ','.join([line['board_id'], line['board_name'],
                                   str(datetime.datetime.now())])
                f.write(newline)
                found_board = True
                break
    if found_board is False:
        with open(filename, "a") as f:
            row = ",".join([board_id, board_name,
                           str(datetime.datetime.now())])
            f.write(row)


def pull_trello(key, token, trello_username, my_board_id, trello):
    if my_board_id == "":
        my_boards = store_boards(trello_username)
        my_board_id = pick_new_board(my_boards)
    task_board = trello.boards.get(my_board_id)
    list_dict, trello_lists = storeListIDs(task_board, my_board_id, trello)
    return list_dict, trello_lists


def get_task(lists, list_dict, trello):
    location, time_size, energy = prompt_for_task()
    print("")
    print("Your task is: ")
    cards = trello.lists.get_card(list_dict['To Do'])
    time_hold = False
    card_id = ""
    max_time = 0
    time_size = time_size.lower()
    time_scale = {'xs': 0, 's': 1, 'm': 2, 'l': 3, 'xl': 4, 'any': 100}
    time_number = time_scale[time_size]
    for card in reversed(cards):
        location_match = False
        energy_match = False
        card_labels = card['labels']
        for label in card_labels:
            if label['name'] == location:
                location_match = True
            if label['name'] == energy:
                energy_match = True
            if location_match is True and energy_match is True:
                if time_size == 'any':
                    card_id = card['id']
                    start_time = datetime.datetime.now()
                    return card_id, card, start_time
                else:
                    # get time category on card and determine if it is less
                    # than or equal to the time available
                    card_time = re.search('\((xs|s|m|l|xl)\)', card['name'])
                    if card_time is not None:
                        card_time = (re.search('(xs|s|m|l|xl)',
                                     card_time.group(0)).group(0))
                        if time_scale[card_time] < (time_number + 1):
                            if time_scale[card_time] == time_number:
                                card_id = card['id']
                                print(card['name'])
                                start_time = datetime.datetime.now()
                                return card_id, card, start_time
                            elif time_hold is False:
                                # This holds the first smaller task that's
                                # encountered, in case an exact match isn't
                                # found
                                card_id = card['id']
                                hold_card = card
                                time_hold = True
    if card_id == "":
        print("No matching task found")
        card = None
        start_time = None
        return card_id, card, start_time
    else:
        print(hold_card['name'])
        start_time = datetime.datetime.now()
        return card_id, hold_card, start_time


def wait_for_done():
    done = input("Type Done when you've completed the task or Quit to leave "
                 "the program: ")
    return done


def get_from_beeminder():
    username = "pjpants"
    goal = "doallthethings"

    BEEMINDER_URL = "https://www.beeminder.com/api/v1"
    GET_URL = BEEMINDER_URL + \
        "/users/{username}/goals/{goal}.json".format(**locals())

    # Look up data points for today
    beeminder_key = keyring.get_password("beeminder", username)
    data = {"auth_token": beeminder_key}
    result = json.loads(requests.get(GET_URL, data=data).content)
    return result['curval']


def post_to_beeminder(value):
    username = "pjpants"
    goal = "doallthethings"

    BEEMINDER_URL = "https://www.beeminder.com/api/v1"
    POST_URL = BEEMINDER_URL + \
        "/users/{username}/goals/{goal}/datapoints.json".format(**locals())

    # Look up data points for today
    beeminder_key = keyring.get_password("beeminder", username)
    data = {"auth_token": beeminder_key,
            "value": value,
            "comment": "via scripting on {}."
            .format(datetime.datetime.now().isoformat())}
    beeminder_result = requests.post(POST_URL, data=data)
    if beeminder_result.status_code == 200:
        print("Your beeminder was updated. We added {} tasks.".format(value))
    else:
        print(beeminder_result)
    return


def checkBeeminder():
    # currently configured just to work for me

    # first get stats
    name = "Melissa"
    total_tasks = float(load_stats(name))

    # then get total number completed from beeminder
    current_beeminder_value = get_from_beeminder()
    print(current_beeminder_value)

    # Update if there's a difference
    if current_beeminder_value < total_tasks:
        post_to_beeminder(total_tasks - current_beeminder_value)
    return
