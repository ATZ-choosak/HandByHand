
import os




def create_user_directory(user_id: int):
    # Create a directory for the user with their ID
    user_directory = f"images/{user_id}"
    if not os.path.exists(user_directory):
        print(f"Creating directory: {user_directory}")
        os.makedirs(user_directory)
    else:
        print(f"Directory {user_directory} already exists")

