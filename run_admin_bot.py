#!/usr/bin/env python3
import sys
import os

def main():
    # Ensure project root on path
    root = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(root, 'bot'))
    from bot.admin_bot import AdminBot
    AdminBot().run()

if __name__ == "__main__":
    main()


