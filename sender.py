import requests
import time
from itertools import cycle

def sendMessage(token, channel_id, message, counter, proxies=None, retry_count=4):
    url = f'https://discord.com/api/v9/channels/{channel_id}/messages'
    data = {"content": message}
    headers = {"Authorization": token}

    response = requests.post(url, data=data, headers=headers, proxies=proxies)

    if response.status_code == 200:
        print(f"{counter}. Message sent to {channel_id}")
        return True
    elif response.status_code == 429:
        print(f"{counter}. Rate limited. Waiting for {response.headers['Retry-After']} seconds.")
        time.sleep(int(response.headers['Retry-After']) + 1)
        return sendMessage(token, channel_id, message, counter, proxies, retry_count)
    else:
        print(f"{counter}. Failed to send message to {channel_id}. Response: {response.status_code}")
        if retry_count > 1:
            print(f"{counter}. MESSAGE FAILED TO SEND, {retry_count - 1} RETRIES REMAINING. WAITING 3 SECONDS THEN RETRYING")
            time.sleep(3)
            return sendMessage(token, channel_id, message, counter, proxies, retry_count - 1)
        else:
            print(f"{counter}. MESSAGE FAILED TO SEND AFTER MULTIPLE RETRIES. SKIPPING ID {channel_id}")
            return False

def getValidTokens(tokens):
    spinner = cycle(['-', '\\', '|', '/'])
    print("Checking valid tokens ", end='', flush=True)

    unique_tokens = list(set(tokens))  # Remove duplicates
    valid_tokens = []
    invalid_tokens = []

    for token_number, token in enumerate(unique_tokens, start=1):
        print(next(spinner), end='\b', flush=True)  # Backspace to overwrite the spinner
        if validateToken(token):
            valid_tokens.append(token)
        else:
            invalid_tokens.append(token)

    x = len(valid_tokens)
    y = len(invalid_tokens)

    print(f"\n{x} tokens were valid, {y} were invalid")
    with open("tokens.txt", "w") as token_file:
        token_file.write("\n".join(valid_tokens))

    return valid_tokens

def validateToken(token):
    response = requests.get("https://discord.com/api/v9/users/@me", headers={"Authorization": token})
    return response.status_code == 200

def countIdsInDms(tokens):
    total_ids = 0
    for token_number, token in enumerate(tokens, start=1):
        channel_ids = getOpenChannels(token)
        print(f"Checking token #{token_number}'s open message ids... ", end='', flush=True)
        total_ids += len(channel_ids)
        print(f"{len(channel_ids)} ids found.", flush=True)

    print(f"\n{total_ids} IDs were counted! You will send {total_ids} messages! Nice!")
    return total_ids

def getOpenChannels(token):
    try:
        channels = requests.get("https://discord.com/api/v9/users/@me/channels", headers={"Authorization": token}).json()
        return [channel['id'] for channel in channels]
    except (KeyError, TypeError):
        print("Failed to retrieve open channels. Check your token and try again.")
        return []

def sendMessages(tokens, message, proxies, cooldown, retry_count):
    total_tokens = len(tokens)
    success_count = 0
    failure_count = 0

    for token_number, token in enumerate(tokens, start=1):
        current_proxy = next(proxies) if proxies else None
        channel_ids = getOpenChannels(token)

        if not channel_ids:
            print(f"No open channels found for token #{token_number}. Check your token and try again.")
            continue

        num_messages = len(channel_ids)
        estimated_time = num_messages * (cooldown + 3)  # Cooldown time + retry waiting time
        print(f"INITIALIZING TOKEN #{token_number}. HE WILL SEND {num_messages} MESSAGES. ESTIMATED TIME: {estimated_time} SECONDS.")

        for idx, channel_id in enumerate(channel_ids, start=1):
            print(f"TOKEN {token_number}: Sending message to ID {channel_id}... ", end='', flush=True)
            success = sendMessage(token, channel_id, message, idx, current_proxy, retry_count)

            if success:
                success_count += 1
            else:
                failure_count += 1

            time.sleep(cooldown)  # Wait for the specified cooldown between messages

    print(f"\nFinal Stats: Successful Messages: {success_count}, Failed Messages: {failure_count}")

def get_yes_no_input(prompt=""):
    while True:
        response = input(prompt).strip().lower()
        if response in ['y', 'n']:
            return response == 'y'
        else:
            print("Invalid input. Please enter 'y' or 'n'.")

def get_numeric_input(prompt, min_value=None, max_value=None):
    while True:
        try:
            value = float(input(prompt))
            if (min_value is None or value >= min_value) and (max_value is None or value <= max_value):
                return value
            else:
                print(f"Input must be between {min_value} and {max_value}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

def main():
    token_file = 'tokens.txt'
    with open(token_file, 'r') as file:
        tokens = file.read().splitlines()

    valid_tokens = getValidTokens(tokens)

    cooldown = get_numeric_input("How long should the cooldown be between sends? (input in seconds): ")
    retry_count = get_numeric_input("How many retries for a failed message send? (input 1-5): ", 1, 5)
    use_proxies = get_yes_no_input("Use proxies? (y/n): ")

    proxies = cycle([{'http': line.strip()} for line in open('proxies.txt')]) if use_proxies else None

    sendMessages(valid_tokens, 'yo join up bro they actually have free cheats that work :skull: https://discord.gg/tr4e3qRq', proxies, cooldown, retry_count)

if __name__ == "__main__":
    main()
