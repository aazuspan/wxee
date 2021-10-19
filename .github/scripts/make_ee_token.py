import os

credentials = f'{{"refresh_token": "{os.environ["EE_TOKEN"]}"}}'

credential_dir = os.path.expanduser("~/.config/earthengine/")
os.makedirs(credential_dir, exist_ok=True)

with open(os.path.join(credential_dir, "credentials"), "w") as dst:
    dst.write(credentials)
