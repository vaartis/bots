# Copyright (C) 2016 TyanNN <TyanNN@cocaine.ninja>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
Если падает с ошибкой, мол, многовато реквестов в секунду,
то добавь sleep(0.3) на следующей строке
"""

import sys
import os
import re
from time import sleep
import vk

# https://oauth.vk.com/authorize?client_id=5088888&scope=groups,offline&response_type=token
TOKEN = ""
GID = 34223764 # Атмта
COMMENT = "Чистка!" # Комментарий к бану

session = vk.Session(access_token=TOKEN)
api = vk.API(session, v=5.60)

if "file" in sys.argv:
    p = os.path.dirname(os.path.abspath(__file__)) + ("\\" if os.name == 'nt' else "/") + "list.txt"
    with open(p) as f:
        lst = f.readlines()

    c = 0
    for u in lst:
        api.groups.banUser(group_id=GID, user_id=int(u), comment=COMMENT, comment_visible=1)
        c += 1
        with open(p, 'w') as f:
            f.writelines(lst[c:])

members_count = api.groups.getById(group_id=GID, fields="members_count")[0]["members_count"]
th_count = int(members_count / 1000) + 1 # Чтобы захватить ещё оставшиеся после ровно тысячи

current_offset = 0

# Если номер - ID, если строка - регулярка для проверки названия
cancer_pubs = [
    73319310, # Ilita!
    r"\d+ch(an)*" # Все цифрочаны
    ]

for i in range(th_count):
    member_ids = api.groups.getMembers(group_id=GID, offset=current_offset)["users"]

    for member_id in member_ids:
        try:
            user_subs = api.users.getSubscriptions(user_id=member_id, extended=1, count=200)
            user_subs_list = user_subs["items"]
            if user_subs["count"] > 200:
                coef = int(user_subs["count"] / 200)
                curr_coef = 1
                for i in range(coef):
                    user_subs_list.extend(
                        api.users.getSubscriptions(user_id=member_id,
                                                   extended=1,
                                                   count=200,
                                                   offset=200 * coef)["items"])
                    curr_coef += 1

        except vk.exceptions.VkAPIError as e:
            if e.code == 18:
                api.groups.removeUser(group_id=GID, user_id=member_id) # Пинок мёртвых акков

        for group in user_subs_list:
            for cancer in cancer_pubs:
                if isinstance(cancer, int):
                    if group["id"] == cancer:
                        api.groups.banUser(group_id=GID, user_id=member_id, comment=COMMENT, comment_visible=1)
                        print(member_id)
                elif isinstance(cancer, str):
                    try:
                        if re.match(cancer, group["name"], re.IGNORECASE):
                            api.groups.banUser(group_id=GID, user_id=member_id, comment=COMMENT, comment_visible=1)
                            print(member_id)
                    except KeyError:
                        pass

    current_offset += 1
    sleep(0.3)

