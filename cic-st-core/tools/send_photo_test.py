import os
import sys
from cicada.adapters.telegram import TelegramAdapter

def main():
    if len(sys.argv) < 3:
        print("Usage: python tools/send_photo_test.py <TOKEN> <CHAT_ID> [<FILE_PATH_OR_URL>]")
        return
    token = sys.argv[1]
    chat_id = int(sys.argv[2])
    file = sys.argv[3] if len(sys.argv) > 3 else "/var/www/cicada-studio/bots/moux04aqmdxm0n1lvo/media/1778690521157-19fc904b-ed12-4d38-bdb0-2a5f71fdac54-254706.jpg"

    tg = TelegramAdapter(token)
    try:
        resp = tg.send_photo(chat_id, file, caption="test from cicada send_photo_test")
        print("Response:", resp)
    except Exception as e:
        print("Exception:", e)

if __name__ == '__main__':
    main()
